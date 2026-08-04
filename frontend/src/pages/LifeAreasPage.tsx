import { useEffect, useMemo, useState } from "react";
import {
  getLifeAreas,
  getMyLifeAreas,
  selectLifeArea,
  unselectLifeArea,
} from "../api/lifeAreas";
import type { LifeAreaResponse } from "../types/lifeArea";

export function LifeAreasPage() {
  const [lifeAreas, setLifeAreas] = useState<LifeAreaResponse[]>([]);
  const [myLifeAreas, setMyLifeAreas] = useState<LifeAreaResponse[]>([]);

  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const selectedAreaIds = useMemo(() => {
    return new Set(myLifeAreas.map((area) => area.id));
  }, [myLifeAreas]);

  async function loadLifeAreas() {
    setError(null);
    setIsLoading(true);

    try {
      const [allAreas, selectedAreas] = await Promise.all([
        getLifeAreas(),
        getMyLifeAreas(),
      ]);

      setLifeAreas(allAreas);
      setMyLifeAreas(selectedAreas);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load life areas."
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function handleToggleArea(areaId: number) {
    setError(null);
    setUpdatingId(areaId);

    try {
      if (selectedAreaIds.has(areaId)) {
        await unselectLifeArea(areaId);
      } else {
        await selectLifeArea(areaId);
      }

      await loadLifeAreas();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not update life area."
      );
    } finally {
      setUpdatingId(null);
    }
  }

  useEffect(() => {
    loadLifeAreas();
  }, []);

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <h1>Life Areas</h1>
          <p>Choose the areas you want to improve and track.</p>
        </div>
      </header>

      {error && <p className="error-message">{error}</p>}

      {isLoading ? (
        <section className="panel">
          <p>Loading life areas...</p>
        </section>
      ) : (
        <section className="area-grid">
          {lifeAreas.map((area) => {
            const isSelected = selectedAreaIds.has(area.id);
            const isUpdating = updatingId === area.id;

            return (
              <article
                key={area.id}
                className={`area-card ${isSelected ? "area-card-selected" : ""}`}
              >
                <div>
                  <span className="area-icon">{area.icon ?? "target"}</span>
                  <h2>{area.name}</h2>
                  <p>{area.description}</p>
                </div>

                <button
                  onClick={() => handleToggleArea(area.id)}
                  disabled={isUpdating}
                >
                  {isUpdating
                    ? "Updating..."
                    : isSelected
                      ? "Selected"
                      : "Select"}
                </button>
              </article>
            );
          })}
        </section>
      )}
    </main>
  );
}