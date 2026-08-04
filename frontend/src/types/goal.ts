export type GoalType = "outcome" | "process" | "habit" | "limit" | "project";
export type GoalPriority = "low" | "medium" | "high";
export type GoalDifficulty = "easy" | "medium" | "hard";
export type GoalStatus = "active" | "completed" | "paused" | "archived";

export type GoalCreate = {
  life_area_id: number;
  title: string;
  description: string | null;
  goal_type: GoalType;
  target_value: number | null;
  target_unit: string | null;
  start_date: string | null;
  end_date: string | null;
  priority: GoalPriority;
  difficulty: GoalDifficulty;
};

export type GoalProgressUpdate = {
  current_value: number;
};

export type GoalResponse = {
  id: number;
  user_id: number;
  life_area_id: number;

  title: string;
  description: string | null;

  goal_type: string;

  target_value: number | null;
  target_unit: string | null;
  current_value: number;
  progress_percentage: number | null;

  start_date: string | null;
  end_date: string | null;

  priority: string;
  difficulty: string;
  status: string;

  created_at: string;
  updated_at: string;
};