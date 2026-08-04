export type AiInsightStatus = "active" | "accepted" | "rejected" | "archived";

export type AiInsightResponse = {
  id: number;
  user_id: number;
  related_goal_id: number | null;

  insight_date: string;

  insight_type: string;
  source: string;

  title: string;
  content: string;
  recommendation: string | null;

  status: string;

  created_at: string;
  updated_at: string;
};

export type AiInsightStatusUpdate = {
  status: AiInsightStatus;
};