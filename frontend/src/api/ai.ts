import { apiRequest } from "./client";
import type {
  AiInsightResponse,
  AiInsightStatus,
} from "../types/ai";

export async function createDailyReview(): Promise<AiInsightResponse> {
  return apiRequest<AiInsightResponse>("/ai/daily-review", {
    method: "POST",
  });
}

export async function getAiInsights(): Promise<AiInsightResponse[]> {
  return apiRequest<AiInsightResponse[]>("/ai/insights?status=active");
}

export async function updateAiInsightStatus(
  insightId: number,
  status: AiInsightStatus
): Promise<AiInsightResponse> {
  return apiRequest<AiInsightResponse>(`/ai/insights/${insightId}/status`, {
    method: "PATCH",
    body: JSON.stringify({
      status,
    }),
  });
}