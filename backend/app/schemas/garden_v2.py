from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class GardenJourneyContextResponse(BaseModel):
    journey_day: int
    plot_index: int
    plot_day: int
    plot_size_days: int


class GardenPlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int

    plot_index: int
    start_journey_day: int
    end_journey_day: int

    title: str
    status: str

    rows: int
    columns: int

    created_at: datetime
    updated_at: datetime


class GardenObjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    garden_plot_id: int

    element_type: str
    object_type: str
    object_subtype: str

    source_type: str
    source_id: int | None

    position_row: int
    position_column: int
    layer: int

    status: str
    is_persistent: bool
    visible_date: date | None

    title: str
    description: str | None
    metadata_json: str | None

    created_at: datetime
    updated_at: datetime


class GardenPlotDetailResponse(BaseModel):
    plot: GardenPlotResponse
    objects: list[GardenObjectResponse]


class GardenWorldResponse(BaseModel):
    context: GardenJourneyContextResponse
    plots: list[GardenPlotResponse]


class GardenCurrentPlotResponse(BaseModel):
    context: GardenJourneyContextResponse
    plot: GardenPlotResponse
    objects: list[GardenObjectResponse]