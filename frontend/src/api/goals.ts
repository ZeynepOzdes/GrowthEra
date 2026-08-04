import { apiRequest } from "./client";
import type {
  GoalCreate,
  GoalProgressUpdate,
  GoalResponse,
} from "../types/goal";

export async function getGoals(): Promise<GoalResponse[]> {
  return apiRequest<GoalResponse[]>("/goals/");
}

export async function getActiveGoals(): Promise<GoalResponse[]> {
  return apiRequest<GoalResponse[]>("/goals/?status=active");
}

export async function createGoal(data: GoalCreate): Promise<GoalResponse> {
  return apiRequest<GoalResponse>("/goals/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateGoalProgress(
  goalId: number,
  data: GoalProgressUpdate
): Promise<GoalResponse> {
  return apiRequest<GoalResponse>(`/goals/${goalId}/progress`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function completeGoal(goalId: number): Promise<GoalResponse> {
  return apiRequest<GoalResponse>(`/goals/${goalId}/complete`, {
    method: "PATCH",
  });
}