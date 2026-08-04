from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.garden import GardenCell
from app.models.task import Task
from app.models.user import User
from app.schemas.garden import (
    GardenCellResponse,
    GardenGridResponse,
    GardenSyncResponse,
)


router = APIRouter(
    prefix="/garden",
    tags=["Garden"],
)


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


def get_next_empty_position(
    user_id: int,
    db: Session,
) -> tuple[int, int]:
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


@router.get("/grid", response_model=GardenGridResponse)
def get_garden_grid(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    cells = (
        db.query(GardenCell)
        .filter(GardenCell.user_id == current_user.id)
        .order_by(GardenCell.row_index.asc(), GardenCell.column_index.asc())
        .all()
    )

    total_cells = GARDEN_ROWS * GARDEN_COLUMNS
    occupied_cells = len(cells)

    return GardenGridResponse(
        rows=GARDEN_ROWS,
        columns=GARDEN_COLUMNS,
        total_cells=total_cells,
        occupied_cells=occupied_cells,
        empty_cells=total_cells - occupied_cells,
        cells=cells,
    )


@router.post("/sync-completed-tasks", response_model=GardenSyncResponse)
def sync_completed_tasks_to_garden(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    completed_tasks = (
        db.query(Task)
        .filter(
            Task.user_id == current_user.id,
            Task.status == "completed",
        )
        .order_by(Task.completed_at.asc(), Task.created_at.asc())
        .all()
    )

    created_cells: list[GardenCell] = []
    skipped_count = 0

    for task in completed_tasks:
        if task_already_has_garden_cell(
            task_id=task.id,
            user_id=current_user.id,
            db=db,
        ):
            skipped_count += 1
            continue

        row_index, column_index = get_next_empty_position(
            user_id=current_user.id,
            db=db,
        )

        cell_type, color_name = get_task_cell_type(task)

        garden_cell = GardenCell(
            user_id=current_user.id,
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

        created_cells.append(garden_cell)

    db.commit()

    for cell in created_cells:
        db.refresh(cell)

    return GardenSyncResponse(
        created_count=len(created_cells),
        skipped_count=skipped_count,
        cells=created_cells,
    )


@router.get("/cells", response_model=list[GardenCellResponse])
def get_garden_cells(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return (
        db.query(GardenCell)
        .filter(GardenCell.user_id == current_user.id)
        .order_by(GardenCell.created_at.desc())
        .all()
    )