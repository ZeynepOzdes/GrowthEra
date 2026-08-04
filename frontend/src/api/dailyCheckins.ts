import { apiRequest } from "./client";
import type {
  DailyCheckInCreate,
  DailyCheckInResponse,
} from "../types/dailyCheckin";

export async function getTodayCheckIn(): Promise<DailyCheckInResponse | null> {
  return apiRequest<DailyCheckInResponse | null>("/daily-checkins/today");
}

export async function createOrUpdateDailyCheckIn(
  data: DailyCheckInCreate
): Promise<DailyCheckInResponse> {
  return apiRequest<DailyCheckInResponse>("/daily-checkins/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getDailyCheckIns(): Promise<DailyCheckInResponse[]> {
  return apiRequest<DailyCheckInResponse[]>("/daily-checkins/");
}