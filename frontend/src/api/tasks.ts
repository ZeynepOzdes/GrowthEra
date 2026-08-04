import { apiRequest } from "./client";
import type {
  TaskCreate,
  TaskElementType,
  TaskResponse,
  TaskShape,
  TaskStatus,
  TaskUrgencyState,
} from "../types/task";

type GetTasksParams = {
  status?: TaskStatus;
  element_type?: TaskElementType;
  urgency_state?: TaskUrgencyState;
  task_shape?: TaskShape;
  life_area_id?: number;
  goal_id?: number;
};

export async function createTask(
  taskData: TaskCreate
): Promise<TaskResponse> {
  return apiRequest<TaskResponse>("/tasks/", {
    method: "POST",
    body: JSON.stringify(taskData),
  });
}

export async function getTasks(
  params: GetTasksParams = {}
): Promise<TaskResponse[]> {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  });

  const queryString = searchParams.toString();

  return apiRequest<TaskResponse[]>(
    queryString ? `/tasks/?${queryString}` : "/tasks/"
  );
}

export async function startTask(taskId: number): Promise<TaskResponse> {
  return apiRequest<TaskResponse>(`/tasks/${taskId}/start`, {
    method: "PATCH",
  });
}

export async function completeTask(taskId: number): Promise<TaskResponse> {
  return apiRequest<TaskResponse>(`/tasks/${taskId}/complete`, {
    method: "PATCH",
  });
}

export async function markTaskAsFire(taskId: number): Promise<TaskResponse> {
  return apiRequest<TaskResponse>(`/tasks/${taskId}/fire`, {
    method: "PATCH",
  });
}

export async function normalizeTaskUrgency(
  taskId: number
): Promise<TaskResponse> {
  return apiRequest<TaskResponse>(`/tasks/${taskId}/normalize`, {
    method: "PATCH",
  });
}

export async function archiveTask(taskId: number): Promise<{ message: string }> {
  return apiRequest<{ message: string }>(`/tasks/${taskId}`, {
    method: "DELETE",
  });
}