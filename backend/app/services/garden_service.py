from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.garden import GardenCell
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


def task_already_has_garden_cell(
    task_id: int,
    user_id: int,
    db: Session,
) -> bool:
    existing_cell = (
        db.query(GardenCell)
        .filter(
            GardenCell.user_id == user_id,
            GardenCell.source_type == "task",
            GardenCell.source_id == task_id,
        )
        .first()
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