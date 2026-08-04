export type TaskElementType = "earth" | "water" | "air";
export type TaskUrgencyState = "normal" | "fire";
export type TaskShape = "flower" | "rock";
export type TaskPriority = "low" | "medium" | "high";

export type TaskStatus =
  | "active"
  | "ongoing"
  | "completed"
  | "paused"
  | "archived";

export type TaskResponse = {
  id: number;
  user_id: number;
  life_area_id: number;
  goal_id: number | null;

  title: string;
  description: string | null;

  element_type: TaskElementType;
  urgency_state: TaskUrgencyState;
  task_shape: TaskShape | null;

  planned_date: string | null;
  due_date: string | null;

  planned_duration_minutes: number | null;

  priority: TaskPriority;
  status: TaskStatus;

  completed_at: string | null;

  created_at: string;
  updated_at: string;
};

export type TaskCreate = {
  life_area_id: number;
  goal_id: number | null;

  title: string;
  description: string | null;

  element_type: TaskElementType;
  urgency_state: TaskUrgencyState;
  task_shape: TaskShape | null;

  planned_date: string | null;
  due_date: string | null;

  planned_duration_minutes: number | null;

  priority: TaskPriority;
};