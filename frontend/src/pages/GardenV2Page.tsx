import { useEffect, useMemo, useState } from "react";
import {
  getCurrentGardenV2Plot,
  getGardenV2AirRewards,
} from "../api/gardenV2";
import type {
  GardenV2AirReward,
  GardenV2CurrentPlotResponse,
  GardenV2Object,
} from "../types/gardenV2";
import "./GardenV2Page.css";

type ObjectVisual = {
  symbol: string;
  label: string;
  className: string;
};

function getObjectVisual(object: GardenV2Object): ObjectVisual {
  if (object.object_subtype === "fire_flower") {
    return {
      symbol: "🔥",
      label: "Urgent flower",
      className: "fire",
    };
  }

  if (
    object.object_type === "plant" ||
    object.object_subtype === "flower"
  ) {
    return {
      symbol: "🌸",
      label: "Productive effort",
      className: "flower",
    };
  }

  if (object.object_type === "idle_rock") {
    return {
      symbol: "○",
      label: "Unfinished daily responsibility",
      className: "idle-rock",
    };
  }

  if (
    object.object_type === "path_stone" ||
    object.object_subtype === "stone" ||
    object.object_subtype === "fire_path_stone"
  ) {
    return {
      symbol:
        object.object_subtype === "fire_path_stone"
          ? "🔥"
          : "🪨",
      label: "Completed daily responsibility",
      className: "path",
    };
  }

  if (object.object_type === "tree") {
    if (object.object_subtype === "seed") {
      return {
        symbol: "•",
        label: "Habit seed",
        className: "tree",
      };
    }

    if (
      object.object_subtype === "sprout" ||
      object.object_subtype === "small_tree"
    ) {
      return {
        symbol: "🌱",
        label: "Growing habit",
        className: "tree",
      };
    }

    return {
      symbol: "🌳",
      label: "Habit tree",
      className: "tree",
    };
  }

  if (
    object.element_type === "water" ||
    object.object_type === "lake"
  ) {
    return {
      symbol:
        object.object_subtype === "puddle" ? "💧" : "🌊",
      label: "Awareness and care",
      className: "water",
    };
  }

  if (
    object.element_type === "air" ||
    object.object_type === "decoration"
  ) {
    const decorationSymbols: Record<string, string> = {
      bench: "🪑",
      table: "🛋️",
      torch: "🕯️",
      paper_plane: "✈️",
      wind_chime: "🎐",
      spark: "✨",
    };

    return {
      symbol: decorationSymbols[object.object_subtype] ?? "✨",
      label: "Inspiration reward",
      className: "air",
    };
  }

  return {
    symbol: "◆",
    label: "Garden object",
    className: "default",
  };
}

function getPositionKey(row: number, column: number): string {
  return `${row}-${column}`;
}

export function GardenV2Page() {
  const [gardenData, setGardenData] =
    useState<GardenV2CurrentPlotResponse | null>(null);

  const [airRewards, setAirRewards] = useState<
    GardenV2AirReward[]
  >([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadGarden() {
      try {
        setIsLoading(true);
        setError("");

        const [currentPlot, rewards] = await Promise.all([
          getCurrentGardenV2Plot(),
          getGardenV2AirRewards(),
        ]);

        setGardenData(currentPlot);
        setAirRewards(rewards);
      } catch (requestError) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Garden could not be loaded."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadGarden();
  }, []);

  const objectsByPosition = useMemo(() => {
    const positionMap = new Map<string, GardenV2Object>();

    if (!gardenData) {
      return positionMap;
    }

    const sortedObjects = [...gardenData.objects].sort(
      (firstObject, secondObject) =>
        firstObject.layer - secondObject.layer
    );

    for (const object of sortedObjects) {
      positionMap.set(
        getPositionKey(
          object.position_row,
          object.position_column
        ),
        object
      );
    }

    return positionMap;
  }, [gardenData]);

  const objectCounts = useMemo(() => {
    if (!gardenData) {
      return {
        flowers: 0,
        paths: 0,
        trees: 0,
        water: 0,
        air: 0,
      };
    }

    return {
      flowers: gardenData.objects.filter(
        (object) =>
          object.object_type === "plant" ||
          object.object_subtype.includes("flower")
      ).length,

      paths: gardenData.objects.filter(
        (object) =>
          object.object_type === "path_stone" ||
          object.object_type === "idle_rock"
      ).length,

      trees: gardenData.objects.filter(
        (object) => object.object_type === "tree"
      ).length,

      water: gardenData.objects.filter(
        (object) =>
          object.element_type === "water" ||
          object.object_type === "lake"
      ).length,

      air: gardenData.objects.filter(
        (object) =>
          object.element_type === "air" ||
          object.object_type === "decoration"
      ).length,
    };
  }, [gardenData]);

  if (isLoading) {
    return (
      <main className="garden-v2-page">
        <div className="garden-v2-state-card">
          <span className="garden-v2-loader" />
          <p>Loading your growth world...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="garden-v2-page">
        <div className="garden-v2-state-card garden-v2-error">
          <h2>Garden could not be loaded</h2>
          <p>{error}</p>
        </div>
      </main>
    );
  }

  if (!gardenData) {
    return (
      <main className="garden-v2-page">
        <div className="garden-v2-state-card">
          <p>No garden data is available.</p>
        </div>
      </main>
    );
  }

  const { context, plot } = gardenData;
  const latestAirReward = airRewards[0] ?? null;

  const totalCells = plot.rows * plot.columns;
  const cells = Array.from(
    { length: totalCells },
    (_, index) => {
      const row = Math.floor(index / plot.columns);
      const column = index % plot.columns;

      return {
        row,
        column,
      };
    }
  );

  return (
    <main className="garden-v2-page">
      <section className="garden-v2-hero">
        <div>
          <span className="garden-v2-eyebrow">
            Your growth world
          </span>

          <h1>{plot.title}</h1>

          <p>
            Every completed action leaves a visible trace of
            who you are becoming.
          </p>
        </div>

        <div className="garden-v2-day-card">
          <span>Journey day</span>
          <strong>{context.journey_day}</strong>
          <small>
            Plot {context.plot_index} · Day {context.plot_day} of{" "}
            {context.plot_size_days}
          </small>
        </div>
      </section>

      <section className="garden-v2-summary-grid">
        <article>
          <span>🌸</span>
          <strong>{objectCounts.flowers}</strong>
          <small>Efforts</small>
        </article>

        <article>
          <span>🪨</span>
          <strong>{objectCounts.paths}</strong>
          <small>Responsibilities</small>
        </article>

        <article>
          <span>🌳</span>
          <strong>{objectCounts.trees}</strong>
          <small>Habit trees</small>
        </article>

        <article>
          <span>🌊</span>
          <strong>{objectCounts.water}</strong>
          <small>Water areas</small>
        </article>

        <article>
          <span>✨</span>
          <strong>{objectCounts.air}</strong>
          <small>Air rewards</small>
        </article>
      </section>

      <section className="garden-v2-content">
        <div className="garden-v2-panel">
          <div className="garden-v2-panel-heading">
            <div>
              <span>Current plot</span>
              <h2>
                Days {plot.start_journey_day}–
                {plot.end_journey_day}
              </h2>
            </div>

            <span className="garden-v2-status">
              {plot.status}
            </span>
          </div>

          <div
            className="garden-v2-board"
            style={{
              gridTemplateColumns: `repeat(${plot.columns}, minmax(34px, 1fr))`,
            }}
          >
            {cells.map((cell) => {
              const object = objectsByPosition.get(
                getPositionKey(cell.row, cell.column)
              );

              const visual = object
                ? getObjectVisual(object)
                : null;

              return (
                <div
                  key={getPositionKey(cell.row, cell.column)}
                  className={`garden-v2-cell ${
                    visual
                      ? `garden-v2-object--${visual.className}`
                      : ""
                  }`}
                  title={
                    object
                      ? `${object.title} — ${visual?.label}`
                      : "Empty garden space"
                  }
                >
                  {visual && (
                    <span className="garden-v2-symbol">
                      {visual.symbol}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <aside className="garden-v2-side-panel">
          <article className="garden-v2-info-card">
            <span className="garden-v2-card-label">
              Latest Air reward
            </span>

            {latestAirReward ? (
              <>
                <div className="garden-v2-reward-icon">
                  ✨
                </div>

                <h3>{latestAirReward.reward_name}</h3>

                <p>
                  {latestAirReward.reward_description ??
                    "A reward earned through inspiration and joy."}
                </p>

                <small>
                  Earned on journey day{" "}
                  {latestAirReward.journey_day}
                </small>
              </>
            ) : (
              <>
                <div className="garden-v2-reward-icon">
                  ☁️
                </div>

                <h3>No Air reward yet</h3>

                <p>
                  Complete an Air task to discover today&apos;s
                  decorative reward.
                </p>
              </>
            )}
          </article>

          <article className="garden-v2-info-card">
            <span className="garden-v2-card-label">
              Garden language
            </span>

            <ul className="garden-v2-legend">
              <li>
                <span>🌸</span>
                <div>
                  <strong>Flower</strong>
                  <small>Productive effort</small>
                </div>
              </li>

              <li>
                <span>🌳</span>
                <div>
                  <strong>Tree</strong>
                  <small>Consistency and habits</small>
                </div>
              </li>

              <li>
                <span>🪨</span>
                <div>
                  <strong>Path</strong>
                  <small>Daily responsibilities</small>
                </div>
              </li>

              <li>
                <span>🌊</span>
                <div>
                  <strong>Water</strong>
                  <small>Awareness and care</small>
                </div>
              </li>

              <li>
                <span>✨</span>
                <div>
                  <strong>Air</strong>
                  <small>Inspiration and joy</small>
                </div>
              </li>
            </ul>
          </article>
        </aside>
      </section>
    </main>
  );
}