export type LifeAreaResponse = {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  icon: string | null;
  is_default: boolean;
  created_at: string;
};

export type UserAreaResponse = {
  id: number;
  user_id: number;
  life_area_id: number;
  is_active: boolean;
  created_at: string;
};