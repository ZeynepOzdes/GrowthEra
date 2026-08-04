import { apiRequest } from "./client";
import type {
  FocusDashboardSummaryResponse,
  FocusSessionCreate,
  FocusSessionResponse,
  FocusSessionStatus,
  FocusTaskSummaryResponse,
} from "../types/focusSession";

type GetFocusSessionsParams = {
  status?: FocusSessionStatus;
  task_id?: number;
  habit_id?: number;
  goal_id?: number;
  limit?: number;
};

export async function startFocusSession(
  sessionData: FocusSessionCreate
): Promise<FocusSessionResponse> {
  return apiRequest<FocusSessionResponse>("/focus-sessions/start", {
    method: "POST",
    body: JSON.stringify(sessionData),
  });
}

export async function getActiveFocusSession(): Promise<FocusSessionResponse | null> {
  return apiRequest<FocusSessionResponse | null>("/focus-sessions/active");
}

export async function getTaskFocusSummary(): Promise<
  FocusTaskSummaryResponse[]
> {
  return apiRequest<FocusTaskSummaryResponse[]>(
    "/focus-sessions/task-summary"
  );
}

export async function getFocusDashboardSummary(): Promise<FocusDashboardSummaryResponse> {
  return apiRequest<FocusDashboardSummaryResponse>(
    "/focus-sessions/dashboard-summary"
  );
}

export async function getFocusSessions(
  params: GetFocusSessionsParams = {}
): Promise<FocusSessionResponse[]> {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  });

  const queryString = searchParams.toString();

  return apiRequest<FocusSessionResponse[]>(
    queryString ? `/focus-sessions/?${queryString}` : "/focus-sessions/"
  );
}

export async function pauseFocusSession(
  sessionId: number
): Promise<FocusSessionResponse> {
  return apiRequest<FocusSessionResponse>(
    `/focus-sessions/${sessionId}/pause`,
    {
      method: "PATCH",
    }
  );
}

export async function resumeFocusSession(
  sessionId: number
): Promise<FocusSessionResponse> {
  return apiRequest<FocusSessionResponse>(
    `/focus-sessions/${sessionId}/resume`,
    {
      method: "PATCH",
    }
  );
}

export async function completeFocusSession(
  sessionId: number
): Promise<FocusSessionResponse> {
  return apiRequest<FocusSessionResponse>(
    `/focus-sessions/${sessionId}/complete`,
    {
      method: "PATCH",
    }
  );
}

export async function cancelFocusSession(
  sessionId: number
): Promise<FocusSessionResponse> {
  return apiRequest<FocusSessionResponse>(
    `/focus-sessions/${sessionId}/cancel`,
    {
      method: "PATCH",
    }
  );
}