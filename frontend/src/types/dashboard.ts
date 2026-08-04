export type DashboardLifeAreaSummary = {
  id: number;
  name: string;
  slug: string;
  icon: string | null;
};

export type DashboardGoalSummary = {
  id: number;
  life_area_id: number;
  title: string;
  goal_type: string;
  target_value: number | null;
  target_unit: string | null;
  current_value: number;
  progress_percentage: number | null;
  priority: string;
  status: string;
  end_date: string | null;
};

export type DashboardHabitTodaySummary = {
  id: number;
  life_area_id: number;
  goal_id: number | null;
  title: string;
  frequency: string;
  target_value: number | null;
  target_unit: string | null;
  completed_today: boolean;
  today_value: number | null;
};

export type DashboardCheckInSummary = {
  id: number;
  checkin_date: string;
  mood_score: number | null;
  energy_score: number | null;
  focus_score: number | null;
  stress_score: number | null;
  sleep_quality_score: number | null;
  note: string | null;
};

export type DashboardSummaryResponse = {
  summary_date: string;
  user_id: number;

  selected_life_areas_count: number;

  active_goals_count: number;
  completed_goals_count: number;
  average_active_goal_progress: number | null;

  active_habits_count: number;
  completed_habits_today: number;
  habit_completion_rate_today: number | null;

  today_checkin_completed: boolean;

  selected_life_areas: DashboardLifeAreaSummary[];
  top_active_goals: DashboardGoalSummary[];
  today_habits: DashboardHabitTodaySummary[];

  today_checkin: DashboardCheckInSummary | null;
  recent_checkins: DashboardCheckInSummary[];
};