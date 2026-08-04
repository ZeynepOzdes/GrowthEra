import { apiRequest } from "./client";
import type { DashboardSummaryResponse } from "../types/dashboard";

export async function getDashboardSummary(): Promise<DashboardSummaryResponse> {
  return apiRequest<DashboardSummaryResponse>("/dashboard/summary");
}