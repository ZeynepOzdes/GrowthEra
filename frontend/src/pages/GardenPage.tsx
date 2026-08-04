import { useEffect, useMemo, useState } from "react";
import { getGardenGrid, syncCompletedTasksToGarden } from "../api/garden";
import type {
  GardenCellResponse,
  GardenGridResponse,
} from "../types/garden";

function getCellSymbol(cellType: string): string {
  if (cellType === "flower") {
    return "✿";
  }

  if (cellType === "rock") {
    return "●";
  }

  if (cellType === "water") {
    return "≈";
  }

  if (cellType === "air") {
    return "◇";
  }

  if (cellType === "fire") {
    return "▲";
  }

  return "";
}

function getCellLabel(cell: GardenCellResponse | undefined): string {
  if (!cell) {
    return "Empty cell";
  }

  return `${cell.cell_type}: ${cell.title}`;
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString();
}

function getGardenProgressPercentage(grid: GardenGridResponse): number {
  if (grid.total_cells === 0) {
    return 0;
  }

  return Math.round((grid.occupied_cells / grid.total_cells) * 100);
}

export function GardenPage() {
  const [gardenGrid, setGardenGrid] = useState<GardenGridResponse | null>(null);
  const [selectedCell, setSelectedCell] =
    useState<GardenCellResponse | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isRepairing, setIsRepairing] = useState(false);

  const cellByPosition = useMemo(() => {
    const map = new Map<string, GardenCellResponse>();

    gardenGrid?.cells.forEach((cell) => {
      map.set(`${cell.row_index}-${cell.column_index}`, cell);
    });

    return map;
  }, [gardenGrid]);

  async function loadGarden() {
    setError(null);
    setIsLoading(true);

    try {
      const data = await getGardenGrid();
      setGardenGrid(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load garden.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleRepairGarden() {
    setError(null);
    setMessage(null);

    const confirmed = window.confirm(
      "This will check completed tasks and add missing garden cells if any are missing. Continue?"
    );

    if (!confirmed) {
      return;
    }

    setIsRepairing(true);

    try {
      const result = await syncCompletedTasksToGarden();

      if (result.created_count > 0) {
        setMessage(
          `${result.created_count} missing completed task(s) were added to your garden.`
        );
      } else {
        setMessage("Your garden is already up to date. No repair was needed.");
      }

      await loadGarden();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not repair garden.");
    } finally {
      setIsRepairing(false);
    }
  }

  useEffect(() => {
    loadGarden();
  }, []);

  if (isLoading) {
    return (
      <main className="page">
        <p>Loading garden...</p>
      </main>
    );
  }

  if (error && !gardenGrid) {
    return (
      <main className="page">
        <section className="panel">
          <p className="error-message">{error}</p>
          <button onClick={loadGarden}>Try again</button>
        </section>
      </main>
    );
  }

  if (!gardenGrid) {
    return null;
  }

  const rows = Array.from({ length: gardenGrid.rows }, (_, index) => index);
  const columns = Array.from(
    { length: gardenGrid.columns },
    (_, index) => index
  );

  const progressPercentage = getGardenProgressPercentage(gardenGrid);

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <h1>Garden</h1>
          <p>
            Your completed tasks automatically become visual cells in your
            personal growth garden.
          </p>
        </div>

        <div className="page-header-actions">
          <button onClick={loadGarden}>Refresh</button>

          <button onClick={handleRepairGarden} disabled={isRepairing}>
            {isRepairing ? "Repairing..." : "Repair missing cells"}
          </button>
        </div>
      </header>

      <section className="garden-info-panel">
        <div>
          <strong>Automatic garden sync is active.</strong>
          <p>
            When you complete a task, GrowthEra now adds it to your garden
            automatically. Use repair only if old completed tasks are missing.
          </p>
        </div>
      </section>

      {error && <p className="error-message">{error}</p>}
      {message && <p className="success-message">{message}</p>}

      <section className="stats-grid">
        <article className="stat-card">
          <span>Total cells</span>
          <strong>{gardenGrid.total_cells}</strong>
        </article>

        <article className="stat-card">
          <span>Occupied</span>
          <strong>{gardenGrid.occupied_cells}</strong>
        </article>

        <article className="stat-card">
          <span>Empty</span>
          <strong>{gardenGrid.empty_cells}</strong>
        </article>

        <article className="stat-card">
          <span>Garden progress</span>
          <strong>{progressPercentage}%</strong>
        </article>
      </section>

      <section className="panel garden-progress-panel">
        <div className="garden-progress-header">
          <span>Garden completion</span>
          <strong>{progressPercentage}%</strong>
        </div>

        <div className="garden-progress-track">
          <div
            className="garden-progress-bar"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </section>

      <section className="content-grid garden-layout">
        <article className="panel">
          <div className="section-header">
            <h2>Growth matrix</h2>
            <span>
              {gardenGrid.rows} × {gardenGrid.columns}
            </span>
          </div>

          <div className="garden-grid">
            {rows.map((rowIndex) =>
              columns.map((columnIndex) => {
                const cell = cellByPosition.get(
                  `${rowIndex}-${columnIndex}`
                );

                return (
                  <button
                    key={`${rowIndex}-${columnIndex}`}
                    type="button"
                    className={`garden-cell ${
                      cell ? `garden-cell-${cell.cell_type}` : "garden-cell-empty"
                    }`}
                    title={getCellLabel(cell)}
                    onClick={() => setSelectedCell(cell ?? null)}
                  >
                    <span>{cell ? getCellSymbol(cell.cell_type) : ""}</span>
                  </button>
                );
              })
            )}
          </div>

          <div className="garden-legend">
            <span>
              <i className="legend-box legend-flower" /> Flower
            </span>
            <span>
              <i className="legend-box legend-rock" /> Rock
            </span>
            <span>
              <i className="legend-box legend-water" /> Water
            </span>
            <span>
              <i className="legend-box legend-air" /> Air
            </span>
            <span>
              <i className="legend-box legend-fire" /> Fire
            </span>
          </div>
        </article>

        <article className="panel">
          <h2>Cell details</h2>

          {selectedCell ? (
            <div className="garden-cell-details">
              <span
                className={`garden-detail-badge garden-detail-badge-${selectedCell.cell_type}`}
              >
                {selectedCell.cell_type}
              </span>

              <h3>{selectedCell.title}</h3>

              {selectedCell.description && <p>{selectedCell.description}</p>}

              <div className="task-meta">
                <span>Color: {selectedCell.color_name}</span>
                <span>Source: {selectedCell.source_type}</span>
                <span>Source ID: {selectedCell.source_id ?? "N/A"}</span>
                <span>Created: {formatDateTime(selectedCell.created_at)}</span>
              </div>
            </div>
          ) : (
            <p>Select a filled garden cell to see details.</p>
          )}
        </article>
      </section>
    </main>
  );
}