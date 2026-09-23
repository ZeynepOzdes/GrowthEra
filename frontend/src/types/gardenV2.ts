export type GardenV2JourneyContext = {
  journey_day: number;
  plot_index: number;
  plot_day: number;
  plot_size_days: number;
};

export type GardenV2Plot = {
  id: number;
  user_id: number;

  plot_index: number;
  start_journey_day: number;
  end_journey_day: number;

  title: string;
  status: string;

  rows: number;
  columns: number;

  created_at: string;
  updated_at: string;
};

export type GardenV2Object = {
  id: number;
  user_id: number;
  garden_plot_id: number;

  element_type: string;
  object_type: string;
  object_subtype: string;

  source_type: string;
  source_id: number | null;

  position_row: number;
  position_column: number;
  layer: number;

  status: string;
  is_persistent: boolean;
  visible_date: string | null;

  title: string;
  description: string | null;
  metadata_json: string | null;

  created_at: string;
  updated_at: string;
};

export type GardenV2CurrentPlotResponse = {
  context: GardenV2JourneyContext;
  plot: GardenV2Plot;
  objects: GardenV2Object[];
};

export type GardenV2AirReward = {
  user_air_reward_id: number;
  task_id: number;
  journey_day: number;
  reward_date: string;
  awarded_at: string;

  reward_code: string;
  reward_name: string;
  reward_description: string | null;
  object_subtype: string;

  garden_object: GardenV2Object | null;
};