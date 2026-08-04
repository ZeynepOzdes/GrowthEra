from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.garden import GardenCell
from app.models.habit import Habit, HabitLog
from app.models.task import Task


GARDEN_ROWS = 8
GARDEN_COLUMNS = 8


def get_task_cell_type(task: Task) -> tuple[str, str]:
    if task.urgency_state == "fire":
        return "fire", "red"

    if task.element_type == "earth" and task.task_shape == "flower":
        return "flower", "pink"

    if task.element_type == "earth" and task.task_shape == "rock":
        return "rock", "gray"

    if task.element_type == "water":
        return "water", "blue"

    if task.element_type == "air":
        return "air", "yellow"

    return "unknown", "white"


def get_habit_tree_stage(streak_count: int) -> tuple[str, str]:
    if streak_count <= 0:
        return "dormant-tree", "gray"

    if streak_count <= 2:
        return "seed", "light-green"

    if streak_count <= 6:
        return "sprout", "green"

    if streak_count <= 13:
        return "small-tree", "medium-green"

    if streak_count <= 29:
        return "tree", "dark-green"

    return "strong-tree", "emerald"


def get_next_empty_position(user_id: int, db: Session) -> tuple[int, int]:
    occupied_cells = (
        db.query(GardenCell.row_index, GardenCell.column_index)
        .filter(GardenCell.user_id == user_id)
        .all()
    )

    occupied_positions = {
        (cell.row_index, cell.column_index) for cell in occupied_cells
    }

    for row_index in range(GARDEN_ROWS):
        for column_index in range(GARDEN_COLUMNS):
            if (row_index, column_index) not in occupied_positions:
                return row_index, column_index

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Garden grid is full.",
    )


def get_existing_source_cell(
    user_id: int,
    source_type: str,
    source_id: int,
    db: Session,
) -> GardenCell | None:
    return (
        db.query(GardenCell)
        .filter(
            GardenCell.user_id == user_id,
            GardenCell.source_type == source_type,
            GardenCell.source_id == source_id,
        )
        .first()
    )


def task_already_has_garden_cell(
    task_id: int,
    user_id: int,
    db: Session,
) -> bool:
    existing_cell = get_existing_source_cell(
        user_id=user_id,
        source_type="task",
        source_id=task_id,
        db=db,
    )

    return existing_cell is not None


def create_garden_cell_from_task(
    task: Task,
    db: Session,
) -> GardenCell | None:
    if task.status != "completed":
        return None

    if task_already_has_garden_cell(
        task_id=task.id,
        user_id=task.user_id,
        db=db,
    ):
        return None

    row_index, column_index = get_next_empty_position(
        user_id=task.user_id,
        db=db,
    )

    cell_type, color_name = get_task_cell_type(task)

    garden_cell = GardenCell(
        user_id=task.user_id,
        row_index=row_index,
        column_index=column_index,
        cell_type=cell_type,
        color_name=color_name,
        source_type="task",
        source_id=task.id,
        title=task.title,
        description=f"Created from completed {task.element_type} task.",
    )

    db.add(garden_cell)
    db.flush()

    return garden_cell


def calculate_daily_habit_streak(
    habit: Habit,
    db: Session,
) -> int:
    completed_dates = (
        db.query(HabitLog.log_date)
        .filter(
            HabitLog.user_id == habit.user_id,
            HabitLog.habit_id == habit.id,
            HabitLog.is_completed == True,
        )
        .order_by(HabitLog.log_date.desc())
        .all()
    )

    completed_date_set = {row.log_date for row in completed_dates}

    if not completed_date_set:
        return 0

    today = date.today()
    yesterday = today - timedelta(days=1)

    if today in completed_date_set:
        cursor = today
    elif yesterday in completed_date_set:
        cursor = yesterday
    else:
        return 0

    streak_count = 0

    while cursor in completed_date_set:
        streak_count += 1
        cursor -= timedelta(days=1)

    return streak_count


def create_or_update_habit_tree_cell(
    habit: Habit,
    streak_count: int,
    db: Session,
) -> GardenCell | None:
    existing_cell = get_existing_source_cell(
        user_id=habit.user_id,
        source_type="habit",
        source_id=habit.id,
        db=db,
    )

    if streak_count <= 0 and existing_cell is None:
        return None

    cell_type, color_name = get_habit_tree_stage(streak_count)

    description = (
        f"Habit streak: {streak_count} day(s)."
        if streak_count > 0
        else "Habit streak is currently inactive."
    )

    if existing_cell is not None:
        existing_cell.cell_type = cell_type
        existing_cell.color_name = color_name
        existing_cell.title = habit.title
        existing_cell.description = description

        db.flush()

        return existing_cell

    row_index, column_index = get_next_empty_position(
        user_id=habit.user_id,
        db=db,
    )

    garden_cell = GardenCell(
        user_id=habit.user_id,
        row_index=row_index,
        column_index=column_index,
        cell_type=cell_type,
        color_name=color_name,
        source_type="habit",
        source_id=habit.id,
        title=habit.title,
        description=description,
    )

    db.add(garden_cell)
    db.flush()

    return garden_cell


def update_habit_tree_from_habit(
    habit: Habit,
    db: Session,
) -> GardenCell | None:
    if habit.status == "archived":
        return None

    streak_count = calculate_daily_habit_streak(
        habit=habit,
        db=db,
    )

    return create_or_update_habit_tree_cell(
        habit=habit,
        streak_count=streak_count,
        db=db,
    )


def sync_completed_tasks_to_garden(
    user_id: int,
    db: Session,
) -> tuple[list[GardenCell], int]:
    completed_tasks = (
        db.query(Task)
        .filter(
            Task.user_id == user_id,
            Task.status == "completed",
        )
        .order_by(Task.completed_at.asc(), Task.created_at.asc())
        .all()
    )

    created_cells: list[GardenCell] = []
    skipped_count = 0

    for task in completed_tasks:
        created_cell = create_garden_cell_from_task(task=task, db=db)

        if created_cell is None:
            skipped_count += 1
        else:
            created_cells.append(created_cell)

    return created_cells, skipped_count


def sync_habit_trees_to_garden(
    user_id: int,
    db: Session,
) -> tuple[list[GardenCell], int, int]:
    habits = (
        db.query(Habit)
        .filter(
            Habit.user_id == user_id,
            Habit.status != "archived",
        )
        .order_by(Habit.created_at.asc())
        .all()
    )

    changed_cells: list[GardenCell] = []
    skipped_count = 0
    dormant_count = 0

    for habit in habits:
        existing_cell = get_existing_source_cell(
            user_id=user_id,
            source_type="habit",
            source_id=habit.id,
            db=db,
        )

        updated_cell = update_habit_tree_from_habit(
            habit=habit,
            db=db,
        )

        if updated_cell is None:
            skipped_count += 1
            continue

        if updated_cell.cell_type == "dormant-tree":
            dormant_count += 1

        if existing_cell is None or updated_cell is not None:
            changed_cells.append(updated_cell)

    return changed_cells, skipped_count, dormant_count