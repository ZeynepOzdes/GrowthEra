from datetime import date, datetime, timedelta
from math import ceil

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.garden_v2 import (
    GardenObject,
    GardenPlot,
    HabitTreeCycle,
    HabitTreeState,
)
from app.models.habit import Habit, HabitLog
from app.models.task import Task
from app.models.user import User
from app.schemas.garden_v2 import GardenObjectResponse


PLOT_SIZE_DAYS = 30
DEFAULT_PLOT_ROWS = 10
DEFAULT_PLOT_COLUMNS = 10
HABIT_TREE_CYCLE_SIZE = 30


def get_user_garden_start_date(user: User) -> date:
    created_at = getattr(user, "created_at", None)

    if isinstance(created_at, datetime):
        return created_at.date()

    if isinstance(created_at, date):
        return created_at

    return date.today()


def calculate_journey_day(user: User, today: date | None = None) -> int:
    current_date = today or date.today()
    start_date = get_user_garden_start_date(user)

    journey_day = (current_date - start_date).days + 1

    return max(journey_day, 1)


def calculate_plot_index(journey_day: int) -> int:
    return max(ceil(journey_day / PLOT_SIZE_DAYS), 1)


def calculate_plot_day(journey_day: int) -> int:
    return ((journey_day - 1) % PLOT_SIZE_DAYS) + 1


def get_plot_day_range(plot_index: int) -> tuple[int, int]:
    start_journey_day = ((plot_index - 1) * PLOT_SIZE_DAYS) + 1
    end_journey_day = plot_index * PLOT_SIZE_DAYS

    return start_journey_day, end_journey_day


def build_plot_title(plot_index: int) -> str:
    if plot_index == 1:
        return "First Garden"

    return f"Garden Plot {plot_index}"


def get_or_create_garden_plot(
    user_id: int,
    plot_index: int,
    db: Session,
) -> GardenPlot:
    existing_plot = (
        db.query(GardenPlot)
        .filter(
            GardenPlot.user_id == user_id,
            GardenPlot.plot_index == plot_index,
        )
        .first()
    )

    if existing_plot is not None:
        return existing_plot

    start_journey_day, end_journey_day = get_plot_day_range(plot_index)

    garden_plot = GardenPlot(
        user_id=user_id,
        plot_index=plot_index,
        start_journey_day=start_journey_day,
        end_journey_day=end_journey_day,
        title=build_plot_title(plot_index),
        status="active",
        rows=DEFAULT_PLOT_ROWS,
        columns=DEFAULT_PLOT_COLUMNS,
    )

    db.add(garden_plot)
    db.flush()

    return garden_plot


def ensure_plots_up_to_current(
    user: User,
    db: Session,
) -> tuple[int, int, int, list[GardenPlot]]:
    journey_day = calculate_journey_day(user)
    current_plot_index = calculate_plot_index(journey_day)
    plot_day = calculate_plot_day(journey_day)

    plots: list[GardenPlot] = []

    for plot_index in range(1, current_plot_index + 1):
        plot = get_or_create_garden_plot(
            user_id=user.id,
            plot_index=plot_index,
            db=db,
        )
        plots.append(plot)

    return journey_day, current_plot_index, plot_day, plots


def get_current_garden_plot(
    user: User,
    db: Session,
) -> GardenPlot:
    journey_day = calculate_journey_day(user)
    plot_index = calculate_plot_index(journey_day)

    return get_or_create_garden_plot(
        user_id=user.id,
        plot_index=plot_index,
        db=db,
    )


def get_plot_objects(
    user_id: int,
    garden_plot_id: int,
    db: Session,
) -> list[GardenObject]:
    return (
        db.query(GardenObject)
        .filter(
            GardenObject.user_id == user_id,
            GardenObject.garden_plot_id == garden_plot_id,
        )
        .order_by(
            GardenObject.layer.asc(),
            GardenObject.position_row.asc(),
            GardenObject.position_column.asc(),
            GardenObject.created_at.asc(),
        )
        .all()
    )


def get_existing_garden_object_for_source(
    user_id: int,
    source_type: str,
    source_id: int,
    db: Session,
) -> GardenObject | None:
    return (
        db.query(GardenObject)
        .filter(
            GardenObject.user_id == user_id,
            GardenObject.source_type == source_type,
            GardenObject.source_id == source_id,
        )
        .first()
    )


def get_occupied_positions(
    garden_plot: GardenPlot,
    db: Session,
) -> set[tuple[int, int]]:
    existing_objects = (
        db.query(GardenObject.position_row, GardenObject.position_column)
        .filter(
            GardenObject.garden_plot_id == garden_plot.id,
            GardenObject.is_persistent == True,
        )
        .all()
    )

    return {(item.position_row, item.position_column) for item in existing_objects}


def get_next_empty_object_position(
    garden_plot: GardenPlot,
    db: Session,
) -> tuple[int, int]:
    occupied_positions = get_occupied_positions(
        garden_plot=garden_plot,
        db=db,
    )

    for row_index in range(garden_plot.rows):
        for column_index in range(garden_plot.columns):
            if (row_index, column_index) not in occupied_positions:
                return row_index, column_index

    return garden_plot.rows - 1, garden_plot.columns - 1


def get_multiple_empty_positions(
    garden_plot: GardenPlot,
    count: int,
    db: Session,
) -> list[tuple[int, int]]:
    occupied_positions = get_occupied_positions(
        garden_plot=garden_plot,
        db=db,
    )

    positions: list[tuple[int, int]] = []

    for row_index in range(garden_plot.rows - 1, -1, -1):
        for column_index in range(garden_plot.columns):
            candidate = (row_index, column_index)

            if candidate in occupied_positions:
                continue

            if candidate in positions:
                continue

            positions.append(candidate)

            if len(positions) >= count:
                return positions

    return positions


def get_task_garden_v2_mapping(task: Task) -> tuple[str, str, str, str] | None:
    if task.element_type == "earth" and task.task_shape == "flower":
        if task.urgency_state == "fire":
            return "flower", "plant", "fire_flower", "Urgent Flower"

        return "flower", "plant", "flower", "Flower"

    if task.element_type == "earth" and task.task_shape == "rock":
        if task.urgency_state == "fire":
            return "path", "path_stone", "fire_path_stone", "Urgent Path Stone"

        return "path", "path_stone", "stone", "Path Stone"

    return None


def create_garden_v2_object_from_task(
    task: Task,
    user: User,
    db: Session,
) -> GardenObject | None:
    if task.status != "completed":
        return None

    task_mapping = get_task_garden_v2_mapping(task)

    if task_mapping is None:
        return None

    existing_object = get_existing_garden_object_for_source(
        user_id=user.id,
        source_type="task",
        source_id=task.id,
        db=db,
    )

    if existing_object is not None:
        return None

    garden_plot = get_current_garden_plot(
        user=user,
        db=db,
    )

    position_row, position_column = get_next_empty_object_position(
        garden_plot=garden_plot,
        db=db,
    )

    element_type, object_type, object_subtype, object_label = task_mapping

    garden_object = GardenObject(
        user_id=user.id,
        garden_plot_id=garden_plot.id,
        element_type=element_type,
        object_type=object_type,
        object_subtype=object_subtype,
        source_type="task",
        source_id=task.id,
        position_row=position_row,
        position_column=position_column,
        layer=1,
        status="active",
        is_persistent=True,
        visible_date=date.today(),
        title=task.title,
        description=f"{object_label} created from completed task.",
        metadata_json=None,
    )

    db.add(garden_object)
    db.flush()

    return garden_object


def sync_completed_tasks_to_garden_v2(
    user: User,
    db: Session,
) -> tuple[list[GardenObject], int]:
    completed_tasks = (
        db.query(Task)
        .filter(
            Task.user_id == user.id,
            Task.status == "completed",
        )
        .order_by(Task.completed_at.asc(), Task.created_at.asc())
        .all()
    )

    created_objects: list[GardenObject] = []
    skipped_count = 0

    for task in completed_tasks:
        created_object = create_garden_v2_object_from_task(
            task=task,
            user=user,
            db=db,
        )

        if created_object is None:
            skipped_count += 1
            continue

        created_objects.append(created_object)

    return created_objects, skipped_count


def get_today_idle_rock_tasks(
    user: User,
    db: Session,
) -> list[Task]:
    today = date.today()

    return (
        db.query(Task)
        .filter(
            Task.user_id == user.id,
            Task.element_type == "earth",
            Task.task_shape == "rock",
            Task.status.in_(["active", "ongoing", "paused"]),
            or_(
                Task.planned_date == today,
                Task.due_date == today,
            ),
        )
        .order_by(Task.priority.desc(), Task.created_at.asc())
        .all()
    )


def build_today_idle_rock_objects(
    user: User,
    garden_plot: GardenPlot,
    db: Session,
) -> list[GardenObjectResponse]:
    idle_rock_tasks = get_today_idle_rock_tasks(
        user=user,
        db=db,
    )

    positions = get_multiple_empty_positions(
        garden_plot=garden_plot,
        count=len(idle_rock_tasks),
        db=db,
    )

    idle_rock_objects: list[GardenObjectResponse] = []

    for index, task in enumerate(idle_rock_tasks):
        if index < len(positions):
            position_row, position_column = positions[index]
        else:
            position_row = garden_plot.rows - 1
            position_column = garden_plot.columns - 1

        idle_rock_objects.append(
            GardenObjectResponse(
                id=-task.id,
                user_id=user.id,
                garden_plot_id=garden_plot.id,
                element_type="path",
                object_type="idle_rock",
                object_subtype="idle_rock",
                source_type="task_idle",
                source_id=task.id,
                position_row=position_row,
                position_column=position_column,
                layer=0,
                status="temporary",
                is_persistent=False,
                visible_date=date.today(),
                title=task.title,
                description="Temporary idle rock from today's incomplete rock task.",
                metadata_json=None,
                created_at=task.created_at,
                updated_at=task.updated_at,
            )
        )

    return idle_rock_objects


def get_current_plot_objects_with_idle_rocks(
    user: User,
    garden_plot: GardenPlot,
    db: Session,
) -> list[GardenObjectResponse]:
    persistent_objects = [
        GardenObjectResponse.model_validate(garden_object)
        for garden_object in get_plot_objects(
            user_id=user.id,
            garden_plot_id=garden_plot.id,
            db=db,
        )
    ]

    idle_rock_objects = build_today_idle_rock_objects(
        user=user,
        garden_plot=garden_plot,
        db=db,
    )

    return persistent_objects + idle_rock_objects


def get_completed_habit_dates(
    habit: Habit,
    db: Session,
) -> list[date]:
    completed_rows = (
        db.query(HabitLog.log_date)
        .filter(
            HabitLog.user_id == habit.user_id,
            HabitLog.habit_id == habit.id,
            HabitLog.is_completed == True,
        )
        .order_by(HabitLog.log_date.asc())
        .all()
    )

    return [row.log_date for row in completed_rows]


def calculate_current_habit_streak(
    completed_dates: set[date],
    habit_status: str,
) -> int:
    if habit_status != "active":
        return 0

    if not completed_dates:
        return 0

    today = date.today()
    yesterday = today - timedelta(days=1)

    if today in completed_dates:
        cursor = today
    elif yesterday in completed_dates:
        cursor = yesterday
    else:
        return 0

    streak_count = 0

    while cursor in completed_dates:
        streak_count += 1
        cursor -= timedelta(days=1)

    return streak_count


def calculate_best_habit_streak(completed_dates: list[date]) -> int:
    if not completed_dates:
        return 0

    sorted_dates = sorted(set(completed_dates))

    best_streak = 1
    current_streak = 1

    for index in range(1, len(sorted_dates)):
        previous_date = sorted_dates[index - 1]
        current_date = sorted_dates[index]

        if current_date == previous_date + timedelta(days=1):
            current_streak += 1
        else:
            current_streak = 1

        best_streak = max(best_streak, current_streak)

    return best_streak


def get_or_create_habit_tree_state(
    habit: Habit,
    db: Session,
) -> HabitTreeState:
    existing_state = (
        db.query(HabitTreeState)
        .filter(
            HabitTreeState.user_id == habit.user_id,
            HabitTreeState.habit_id == habit.id,
        )
        .first()
    )

    if existing_state is not None:
        return existing_state

    tree_state = HabitTreeState(
        user_id=habit.user_id,
        habit_id=habit.id,
        growth_points=0,
        current_streak=0,
        best_streak=0,
        last_completed_date=None,
        is_dormant=True,
        active_cycle_number=1,
    )

    db.add(tree_state)
    db.flush()

    return tree_state


def get_habit_tree_object_subtype(
    cycle_growth_points: int,
    is_dormant: bool,
    is_completed_cycle: bool,
) -> str:
    if is_completed_cycle:
        return "completed_tree"

    if is_dormant:
        return "dormant_tree"

    if cycle_growth_points <= 2:
        return "seed"

    if cycle_growth_points <= 6:
        return "sprout"

    if cycle_growth_points <= 13:
        return "small_tree"

    return "tree"


def get_or_create_habit_tree_cycle(
    habit: Habit,
    user: User,
    cycle_number: int,
    db: Session,
) -> HabitTreeCycle:
    existing_cycle = (
        db.query(HabitTreeCycle)
        .filter(
            HabitTreeCycle.user_id == user.id,
            HabitTreeCycle.habit_id == habit.id,
            HabitTreeCycle.cycle_number == cycle_number,
        )
        .first()
    )

    if existing_cycle is not None:
        return existing_cycle

    garden_plot = get_current_garden_plot(
        user=user,
        db=db,
    )

    cycle_start_growth_point = ((cycle_number - 1) * HABIT_TREE_CYCLE_SIZE) + 1
    cycle_end_growth_point = cycle_number * HABIT_TREE_CYCLE_SIZE

    habit_tree_cycle = HabitTreeCycle(
        user_id=user.id,
        habit_id=habit.id,
        garden_plot_id=garden_plot.id,
        garden_object_id=None,
        cycle_number=cycle_number,
        cycle_start_growth_point=cycle_start_growth_point,
        cycle_end_growth_point=cycle_end_growth_point,
        growth_points_in_cycle=0,
        status="active",
    )

    db.add(habit_tree_cycle)
    db.flush()

    return habit_tree_cycle


def create_or_update_habit_tree_object(
    habit: Habit,
    user: User,
    tree_cycle: HabitTreeCycle,
    object_subtype: str,
    object_status: str,
    db: Session,
) -> GardenObject:
    existing_object = None

    if tree_cycle.garden_object_id is not None:
        existing_object = (
            db.query(GardenObject)
            .filter(
                GardenObject.id == tree_cycle.garden_object_id,
                GardenObject.user_id == user.id,
            )
            .first()
        )

    description = (
        f"Habit tree cycle {tree_cycle.cycle_number}. "
        f"Cycle progress: {tree_cycle.growth_points_in_cycle}/30."
    )

    if existing_object is not None:
        existing_object.object_subtype = object_subtype
        existing_object.status = object_status
        existing_object.title = habit.title
        existing_object.description = description
        existing_object.updated_at = datetime.utcnow()

        db.flush()

        return existing_object

    garden_plot = (
        db.query(GardenPlot)
        .filter(
            GardenPlot.id == tree_cycle.garden_plot_id,
            GardenPlot.user_id == user.id,
        )
        .first()
    )

    if garden_plot is None:
        garden_plot = get_current_garden_plot(
            user=user,
            db=db,
        )
        tree_cycle.garden_plot_id = garden_plot.id

    position_row, position_column = get_next_empty_object_position(
        garden_plot=garden_plot,
        db=db,
    )

    garden_object = GardenObject(
        user_id=user.id,
        garden_plot_id=garden_plot.id,
        element_type="tree",
        object_type="tree",
        object_subtype=object_subtype,
        source_type="habit_tree_cycle",
        source_id=tree_cycle.id,
        position_row=position_row,
        position_column=position_column,
        layer=1,
        status=object_status,
        is_persistent=True,
        visible_date=date.today(),
        title=habit.title,
        description=description,
        metadata_json=None,
    )

    db.add(garden_object)
    db.flush()

    tree_cycle.garden_object_id = garden_object.id
    db.flush()

    return garden_object


def update_habit_tree_cycles(
    habit: Habit,
    user: User,
    tree_state: HabitTreeState,
    db: Session,
) -> list[GardenObject]:
    changed_objects: list[GardenObject] = []

    if tree_state.growth_points <= 0:
        return changed_objects

    active_cycle_number = max(
        ceil(tree_state.growth_points / HABIT_TREE_CYCLE_SIZE),
        1,
    )

    tree_state.active_cycle_number = active_cycle_number

    for cycle_number in range(1, active_cycle_number + 1):
        tree_cycle = get_or_create_habit_tree_cycle(
            habit=habit,
            user=user,
            cycle_number=cycle_number,
            db=db,
        )

        cycle_start = tree_cycle.cycle_start_growth_point
        cycle_end = tree_cycle.cycle_end_growth_point

        if tree_state.growth_points >= cycle_end:
            growth_points_in_cycle = HABIT_TREE_CYCLE_SIZE
        else:
            growth_points_in_cycle = tree_state.growth_points - cycle_start + 1

        growth_points_in_cycle = max(
            0,
            min(HABIT_TREE_CYCLE_SIZE, growth_points_in_cycle),
        )

        tree_cycle.growth_points_in_cycle = growth_points_in_cycle

        is_completed_cycle = growth_points_in_cycle >= HABIT_TREE_CYCLE_SIZE
        is_active_cycle = cycle_number == active_cycle_number

        if is_completed_cycle:
            tree_cycle.status = "completed"
            object_status = "completed"
        elif tree_state.is_dormant and is_active_cycle:
            tree_cycle.status = "dormant"
            object_status = "dormant"
        else:
            tree_cycle.status = "active"
            object_status = "active"

        object_subtype = get_habit_tree_object_subtype(
            cycle_growth_points=growth_points_in_cycle,
            is_dormant=tree_state.is_dormant and is_active_cycle,
            is_completed_cycle=is_completed_cycle,
        )

        changed_object = create_or_update_habit_tree_object(
            habit=habit,
            user=user,
            tree_cycle=tree_cycle,
            object_subtype=object_subtype,
            object_status=object_status,
            db=db,
        )

        changed_objects.append(changed_object)

    db.flush()

    return changed_objects


def update_habit_tree_state_from_habit(
    habit: Habit,
    user: User,
    db: Session,
) -> list[GardenObject]:
    tree_state = get_or_create_habit_tree_state(
        habit=habit,
        db=db,
    )

    completed_dates = get_completed_habit_dates(
        habit=habit,
        db=db,
    )

    completed_date_set = set(completed_dates)

    growth_points = len(completed_date_set)
    current_streak = calculate_current_habit_streak(
        completed_dates=completed_date_set,
        habit_status=habit.status,
    )
    best_streak = calculate_best_habit_streak(completed_dates)

    tree_state.growth_points = growth_points
    tree_state.current_streak = current_streak
    tree_state.best_streak = best_streak
    tree_state.last_completed_date = max(completed_date_set) if completed_date_set else None
    tree_state.is_dormant = current_streak <= 0
    tree_state.active_cycle_number = max(
        ceil(growth_points / HABIT_TREE_CYCLE_SIZE),
        1,
    )
    tree_state.updated_at = datetime.utcnow()

    db.flush()

    return update_habit_tree_cycles(
        habit=habit,
        user=user,
        tree_state=tree_state,
        db=db,
    )


def sync_habit_trees_to_garden_v2(
    user: User,
    db: Session,
) -> tuple[list[GardenObject], int, int]:
    habits = (
        db.query(Habit)
        .filter(
            Habit.user_id == user.id,
            Habit.status != "archived",
        )
        .order_by(Habit.created_at.asc())
        .all()
    )

    changed_objects: list[GardenObject] = []
    skipped_count = 0
    dormant_count = 0

    for habit in habits:
        habit_objects = update_habit_tree_state_from_habit(
            habit=habit,
            user=user,
            db=db,
        )

        if not habit_objects:
            skipped_count += 1
            continue

        for garden_object in habit_objects:
            if garden_object.status == "dormant":
                dormant_count += 1

            changed_objects.append(garden_object)

    return changed_objects, skipped_count, dormant_count