from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.garden_v2 import GardenPlot
from app.models.user import User
from app.schemas.garden_v2 import (
    GardenCurrentPlotResponse,
    GardenJourneyContextResponse,
    GardenPlotDetailResponse,
    GardenV2TaskSyncResponse,
    GardenWorldResponse,
)
from app.services.garden_v2_service import (
    PLOT_SIZE_DAYS,
    calculate_journey_day,
    calculate_plot_day,
    calculate_plot_index,
    ensure_plots_up_to_current,
    get_plot_objects,
    sync_completed_tasks_to_garden_v2,
)


router = APIRouter(
    prefix="/garden-v2",
    tags=["Garden V2"],
)


@router.get("/context", response_model=GardenJourneyContextResponse)
def get_garden_context(
    current_user: User = Depends(get_current_active_user),
):
    journey_day = calculate_journey_day(current_user)
    plot_index = calculate_plot_index(journey_day)
    plot_day = calculate_plot_day(journey_day)

    return GardenJourneyContextResponse(
        journey_day=journey_day,
        plot_index=plot_index,
        plot_day=plot_day,
        plot_size_days=PLOT_SIZE_DAYS,
    )


@router.get("/plots", response_model=GardenWorldResponse)
def get_garden_plots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    journey_day, plot_index, plot_day, plots = ensure_plots_up_to_current(
        user=current_user,
        db=db,
    )

    db.commit()

    for plot in plots:
        db.refresh(plot)

    return GardenWorldResponse(
        context=GardenJourneyContextResponse(
            journey_day=journey_day,
            plot_index=plot_index,
            plot_day=plot_day,
            plot_size_days=PLOT_SIZE_DAYS,
        ),
        plots=plots,
    )


@router.get("/plots/current", response_model=GardenCurrentPlotResponse)
def get_current_garden_plot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    journey_day, plot_index, plot_day, plots = ensure_plots_up_to_current(
        user=current_user,
        db=db,
    )

    current_plot = plots[-1]

    db.commit()
    db.refresh(current_plot)

    objects = get_plot_objects(
        user_id=current_user.id,
        garden_plot_id=current_plot.id,
        db=db,
    )

    return GardenCurrentPlotResponse(
        context=GardenJourneyContextResponse(
            journey_day=journey_day,
            plot_index=plot_index,
            plot_day=plot_day,
            plot_size_days=PLOT_SIZE_DAYS,
        ),
        plot=current_plot,
        objects=objects,
    )


@router.get("/plots/{plot_id}", response_model=GardenPlotDetailResponse)
def get_garden_plot_detail(
    plot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    plot = (
        db.query(GardenPlot)
        .filter(
            GardenPlot.id == plot_id,
            GardenPlot.user_id == current_user.id,
        )
        .first()
    )

    if plot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Garden plot not found.",
        )

    objects = get_plot_objects(
        user_id=current_user.id,
        garden_plot_id=plot.id,
        db=db,
    )

    return GardenPlotDetailResponse(
        plot=plot,
        objects=objects,
    )


@router.post("/sync-completed-tasks", response_model=GardenV2TaskSyncResponse)
def sync_completed_tasks_to_v2_garden(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    created_objects, skipped_count = sync_completed_tasks_to_garden_v2(
        user=current_user,
        db=db,
    )

    db.commit()

    for garden_object in created_objects:
        db.refresh(garden_object)

    return GardenV2TaskSyncResponse(
        created_count=len(created_objects),
        skipped_count=skipped_count,
        objects=created_objects,
    )