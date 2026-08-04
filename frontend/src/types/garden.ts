export type GardenCellResponse = {
  id: number;
  user_id: number;

  row_index: number;
  column_index: number;

  cell_type: string;
  color_name: string;

  source_type: string;
  source_id: number | null;

  title: string;
  description: string | null;

  created_at: string;
};

export type GardenGridResponse = {
  rows: number;
  columns: number;
  total_cells: number;
  occupied_cells: number;
  empty_cells: number;

  cells: GardenCellResponse[];
};

export type GardenSyncResponse = {
  created_count: number;
  skipped_count: number;
  cells: GardenCellResponse[];
};

export type GardenHabitTreeSyncResponse = {
  changed_count: number;
  skipped_count: number;
  dormant_count: number;
  cells: GardenCellResponse[];
};