import type {
  LifeAreaResponse,
  UserAreaResponse,
} from "../types/lifeArea";
import { apiRequest } from "./client";

export async function getLifeAreas(): Promise<
  LifeAreaResponse[]
> {
  return apiRequest<LifeAreaResponse[]>("/life-areas/", {
    skipAuth: true,
  });
}

export async function getMyLifeAreas(): Promise<
  LifeAreaResponse[]
> {
  return apiRequest<LifeAreaResponse[]>("/life-areas/my");
}

export async function selectLifeArea(
  lifeAreaId: number
): Promise<UserAreaResponse> {
  return apiRequest<UserAreaResponse>(
    `/life-areas/${lifeAreaId}/select`,
    {
      method: "POST",
    }
  );
}

export async function unselectLifeArea(
  lifeAreaId: number
): Promise<{ message: string }> {
  return apiRequest<{ message: string }>(
    `/life-areas/${lifeAreaId}/select`,
    {
      method: "DELETE",
    }
  );
}