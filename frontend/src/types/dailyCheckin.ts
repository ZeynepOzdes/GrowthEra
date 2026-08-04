export type DailyCheckInCreate = {
  checkin_date: string;
  mood_score: number | null;
  energy_score: number | null;
  focus_score: number | null;
  stress_score: number | null;
  sleep_quality_score: number | null;
  note: string | null;
};

export type DailyCheckInResponse = {
  id: number;
  user_id: number;

  checkin_date: string;

  mood_score: number | null;
  energy_score: number | null;
  focus_score: number | null;
  stress_score: number | null;
  sleep_quality_score: number | null;

  note: string | null;

  created_at: string;
  updated_at: string;
};