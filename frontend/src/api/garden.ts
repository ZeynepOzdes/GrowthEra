import { apiRequest } from "./client";
import type {
  GardenCellResponse,
  GardenGridResponse,
  GardenSyncResponse,
} from "../types/garden";

export async function getGardenGrid(): Promise<GardenGridResponse> {
  return apiRequest<GardenGridResponse>("/garden/grid");
}

export async function syncCompletedTasksToGarden(): Promise<GardenSyncResponse> {
  return apiRequest<GardenSyncResponse>("/garden/sync-completed-tasks", {
    method: "POST",
  });
}

export async function getGardenCells(): Promise<GardenCellResponse[]> {
  return apiRequest<GardenCellResponse[]>("/garden/cells");
}