from datetime import date, datetime
from math import ceil

from sqlalchemy.orm import Session

from app.models.garden_v2 import GardenObject, GardenPlot
from app.models.task import Task
from app.models.user import User


PLOT_SIZE_DAYS = 30
DEFAULT_PLOT_ROWS = 10
DEFAULT_PLOT_COLUMNS = 10


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


def get_next_empty_object_position(
    garden_plot: GardenPlot,
    db: Session,
) -> tuple[int, int]:
    existing_objects = (
        db.query(GardenObject.position_row, GardenObject.position_column)
        .filter(
            GardenObject.garden_plot_id == garden_plot.id,
            GardenObject.is_persistent == True,
        )
        .all()
    )

    occupied_positions = {
        (item.position_row, item.position_column) for item in existing_objects
    }

    for row_index in range(garden_plot.rows):
        for column_index in range(garden_plot.columns):
            if (row_index, column_index) not in occupied_positions:
                return row_index, column_index

    return garden_plot.rows - 1, garden_plot.columns - 1


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