from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.garden import GardenCell
from app.models.user import User
from app.schemas.garden import (
    GardenCellResponse,
    GardenGridResponse,
    GardenSyncResponse,
)
from app.services.garden_service import (
    GARDEN_COLUMNS,
    GARDEN_ROWS,
    sync_completed_tasks_to_garden,
)


router = APIRouter(
    prefix="/garden",
    tags=["Garden"],
)


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
def sync_completed_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    created_cells, skipped_count = sync_completed_tasks_to_garden(
        user_id=current_user.id,
        db=db,
    )

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