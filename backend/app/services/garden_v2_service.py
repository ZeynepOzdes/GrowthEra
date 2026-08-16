from datetime import date, datetime
from math import ceil

from sqlalchemy.orm import Session

from app.models.garden_v2 import GardenObject, GardenPlot
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