import type {
  GardenV2AirReward,
  GardenV2CurrentPlotResponse,
} from "../types/gardenV2";
import { apiRequest } from "./client";

export async function getCurrentGardenV2Plot(): Promise<GardenV2CurrentPlotResponse> {
  return apiRequest<GardenV2CurrentPlotResponse>(
    "/garden-v2/plots/current"
  );
}

export async function getGardenV2AirRewards(): Promise<
  GardenV2AirReward[]
> {
  return apiRequest<GardenV2AirReward[]>(
    "/garden-v2/air-rewards"
  );
}