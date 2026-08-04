from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GardenCellResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int

    row_index: int
    column_index: int

    cell_type: str
    color_name: str

    source_type: str
    source_id: int | None

    title: str
    description: str | None

    created_at: datetime


class GardenGridResponse(BaseModel):
    rows: int
    columns: int
    total_cells: int
    occupied_cells: int
    empty_cells: int

    cells: list[GardenCellResponse]


class GardenSyncResponse(BaseModel):
    created_count: int
    skipped_count: int
    cells: list[GardenCellResponse]


class GardenHabitTreeSyncResponse(BaseModel):
    changed_count: int
    skipped_count: int
    dormant_count: int
    cells: list[GardenCellResponse]