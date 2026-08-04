import { apiRequest } from "./client";
import type {
  HabitCreate,
  HabitLogCreate,
  HabitLogResponse,
  HabitResponse,
} from "../types/habit";

export async function getHabits(): Promise<HabitResponse[]> {
  return apiRequest<HabitResponse[]>("/habits/");
}

export async function getActiveHabits(): Promise<HabitResponse[]> {
  return apiRequest<HabitResponse[]>("/habits/?status=active");
}

export async function createHabit(data: HabitCreate): Promise<HabitResponse> {
  return apiRequest<HabitResponse>("/habits/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function logHabit(
  habitId: number,
  data: HabitLogCreate
): Promise<HabitLogResponse> {
  return apiRequest<HabitLogResponse>(`/habits/${habitId}/logs`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}