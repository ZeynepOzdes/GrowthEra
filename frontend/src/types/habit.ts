export type HabitFrequency = "daily" | "weekly" | "custom";
export type HabitStatus = "active" | "paused" | "archived";

export type HabitCreate = {
  life_area_id: number;
  goal_id: number | null;
  title: string;
  description: string | null;
  frequency: HabitFrequency;
  target_value: number | null;
  target_unit: string | null;
};

export type HabitResponse = {
  id: number;
  user_id: number;
  life_area_id: number;
  goal_id: number | null;

  title: string;
  description: string | null;

  frequency: string;

  target_value: number | null;
  target_unit: string | null;

  status: string;

  created_at: string;
  updated_at: string;
};

export type HabitLogCreate = {
  log_date: string;
  value: number | null;
  is_completed: boolean;
  note: string | null;
};

export type HabitLogResponse = {
  id: number;
  habit_id: number;
  user_id: number;

  log_date: string;
  value: number | null;
  is_completed: boolean;

  note: string | null;

  created_at: string;
  updated_at: string;
};