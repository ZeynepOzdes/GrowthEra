import { useEffect, useMemo, useState } from "react";
import {
  getGardenGrid,
  syncCompletedTasksToGarden,
  syncHabitTreesToGarden,
} from "../api/garden";
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

  if (cellType === "seed") {
    return "•";
  }

  if (cellType === "sprout") {
    return "♧";
  }

  if (cellType === "small-tree") {
    return "♣";
  }

  if (cellType === "tree") {
    return "♠";
  }

  if (cellType === "strong-tree") {
    return "♛";
  }

  if (cellType === "dormant-tree") {
    return "○";
  }

  return "";
}

function getReadableCellType(cellType: string): string {
  return cellType
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function getCellLabel(cell: GardenCellResponse | undefined): string {
  if (!cell) {
    return "Empty cell";
  }

  return `${getReadableCellType(cell.cell_type)}: ${cell.title}`;
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

function countCellsBySourceType(
  cells: GardenCellResponse[],
  sourceType: string
): number {
  return cells.filter((cell) => cell.source_type === sourceType).length;
}

function countTreeCells(cells: GardenCellResponse[]): number {
  const treeTypes = [
    "seed",
    "sprout",
    "small-tree",
    "tree",
    "strong-tree",
    "dormant-tree",
  ];

  return cells.filter((cell) => treeTypes.includes(cell.cell_type)).length;
}

export function GardenPage() {
  const [gardenGrid, setGardenGrid] = useState<GardenGridResponse | null>(null);
  const [selectedCell, setSelectedCell] =
    useState<GardenCellResponse | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isRepairingTasks, setIsRepairingTasks] = useState(false);
  const [isRepairingTrees, setIsRepairingTrees] = useState(false);

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

  async function handleRepairTaskCells() {
    setError(null);
    setMessage(null);

    const confirmed = window.confirm(
      "This will check completed tasks and add missing garden cells if any are missing. Continue?"
    );

    if (!confirmed) {
      return;
    }

    setIsRepairingTasks(true);

    try {
      const result = await syncCompletedTasksToGarden();

      if (result.created_count > 0) {
        setMessage(
          `${result.created_count} missing completed task cell(s) were added to your garden.`
        );
      } else {
        setMessage("Task cells are already up to date. No repair was needed.");
      }

      await loadGarden();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not repair task cells."
      );
    } finally {
      setIsRepairingTasks(false);
    }
  }

  async function handleRepairHabitTrees() {
    setError(null);
    setMessage(null);

    const confirmed = window.confirm(
      "This will recalculate habit streak trees and update missing or outdated tree cells. Continue?"
    );

    if (!confirmed) {
      return;
    }

    setIsRepairingTrees(true);

    try {
      const result = await syncHabitTreesToGarden();

      if (result.changed_count > 0) {
        setMessage(
          `${result.changed_count} habit tree cell(s) were updated. Dormant trees: ${result.dormant_count}.`
        );
      } else {
        setMessage("Habit trees are already up to date.");
      }

      await loadGarden();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not repair habit trees."
      );
    } finally {
      setIsRepairingTrees(false);
    }
  }

  useEffect(() => {
    loadGarden();

    window.addEventListener("growthera:task-updated", loadGarden);

    return () => {
      window.removeEventListener("growthera:task-updated", loadGarden);
    };
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
  const taskCellCount = countCellsBySourceType(gardenGrid.cells, "task");
  const habitTreeCount = countTreeCells(gardenGrid.cells);

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <h1>Garden</h1>
          <p>
            Your completed tasks and habit streaks become visual growth in your
            personal garden.
          </p>
        </div>

        <div className="page-header-actions">
          <button onClick={loadGarden}>Refresh</button>

          <button onClick={handleRepairTaskCells} disabled={isRepairingTasks}>
            {isRepairingTasks ? "Repairing..." : "Repair task cells"}
          </button>

          <button onClick={handleRepairHabitTrees} disabled={isRepairingTrees}>
            {isRepairingTrees ? "Updating..." : "Repair habit trees"}
          </button>
        </div>
      </header>

      <section className="garden-info-panel">
        <div>
          <strong>Automatic garden sync is active.</strong>
          <p>
            Completed tasks create garden cells automatically. Completed habit
            logs grow habit trees from seed to strong tree as your streak grows.
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
          <span>Task cells</span>
          <strong>{taskCellCount}</strong>
        </article>

        <article className="stat-card">
          <span>Habit trees</span>
          <strong>{habitTreeCount}</strong>
        </article>

        <article className="stat-card">
          <span>Garden progress</span>
          <strong>{progressPercentage}%</strong>
        </article>
      </section>

      <section className="panel garden-progress-panel">
        <div className="garden-progress-header">
          <span>Garden completion</span>
          <strong>
            {gardenGrid.occupied_cells}/{gardenGrid.total_cells} cells •{" "}
            {progressPercentage}%
          </strong>
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

          <div className="garden-legend garden-legend-grouped">
            <div>
              <strong>Task cells</strong>
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

            <div>
              <strong>Habit trees</strong>
              <span>
                <i className="legend-box legend-seed" /> Seed
              </span>
              <span>
                <i className="legend-box legend-sprout" /> Sprout
              </span>
              <span>
                <i className="legend-box legend-small-tree" /> Small tree
              </span>
              <span>
                <i className="legend-box legend-tree" /> Tree
              </span>
              <span>
                <i className="legend-box legend-strong-tree" /> Strong tree
              </span>
              <span>
                <i className="legend-box legend-dormant-tree" /> Dormant
              </span>
            </div>
          </div>
        </article>

        <article className="panel">
          <h2>Cell details</h2>

          {selectedCell ? (
            <div className="garden-cell-details">
              <span
                className={`garden-detail-badge garden-detail-badge-${selectedCell.cell_type}`}
              >
                {getReadableCellType(selectedCell.cell_type)}
              </span>

              <h3>{selectedCell.title}</h3>

              {selectedCell.description && <p>{selectedCell.description}</p>}

              <div className="task-meta">
                <span>Color: {selectedCell.color_name}</span>
                <span>Source: {selectedCell.source_type}</span>
                <span>Source ID: {selectedCell.source_id ?? "N/A"}</span>
                <span>Created: {formatDateTime(selectedCell.created_at)}</span>
              </div>

              {selectedCell.source_type === "habit" && (
                <p className="note">
                  Habit trees grow as your daily completion streak increases.
                </p>
              )}

              {selectedCell.source_type === "task" && (
                <p className="note">
                  Task cells represent completed tasks and stay as historical
                  progress.
                </p>
              )}
            </div>
          ) : (
            <p>Select a filled garden cell to see details.</p>
          )}
        </article>
      </section>
    </main>
  );
}