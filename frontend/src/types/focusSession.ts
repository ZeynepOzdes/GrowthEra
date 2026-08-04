export type FocusSessionStatus =
  | "running"
  | "paused"
  | "completed"
  | "cancelled";

export type FocusSessionType =
  | "focus"
  | "task"
  | "habit"
  | "goal"
  | "general";

export type FocusSessionCreate = {
  life_area_id: number | null;
  goal_id: number | null;
  habit_id: number | null;
  task_id: number | null;

  title: string;
  session_type: FocusSessionType;

  planned_duration_minutes: number | null;

  note: string | null;
};

export type FocusSessionResponse = {
  id: number;
  user_id: number;

  life_area_id: number | null;
  goal_id: number | null;
  habit_id: number | null;
  task_id: number | null;

  title: string;
  session_type: string;
  status: FocusSessionStatus;

  planned_duration_minutes: number | null;

  accumulated_seconds: number;
  duration_seconds: number | null;

  started_at: string;
  last_resumed_at: string | null;
  paused_at: string | null;
  ended_at: string | null;

  note: string | null;

  created_at: string;
  updated_at: string;
};

export type FocusTaskSummaryResponse = {
  task_id: number;
  task_title: string;
  task_status: string;

  planned_duration_minutes: number | null;

  total_focus_seconds: number;
  total_focus_minutes: number;

  completed_sessions_count: number;
  last_session_at: string | null;

  has_active_session: boolean;
  active_session_id: number | null;
  active_session_status: FocusSessionStatus | null;
  active_session_seconds: number;

  progress_percentage: number | null;
  is_over_planned: boolean;
};

export type FocusDashboardSummaryResponse = {
  today_focus_seconds: number;
  today_focus_minutes: number;
  completed_sessions_today: number;

  total_focus_seconds: number;
  total_focus_minutes: number;
  completed_sessions_total: number;

  has_active_session: boolean;
  active_session_id: number | null;
  active_session_title: string | null;
  active_session_status: FocusSessionStatus | null;
  active_session_task_id: number | null;
  active_session_seconds: number;
};