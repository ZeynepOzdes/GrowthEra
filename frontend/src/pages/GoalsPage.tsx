import { FormEvent, useEffect, useState } from "react";
import { completeGoal, createGoal, getGoals, updateGoalProgress } from "../api/goals";
import { getMyLifeAreas } from "../api/lifeAreas";
import type { GoalResponse, GoalType, GoalPriority, GoalDifficulty } from "../types/goal";
import type { LifeAreaResponse } from "../types/lifeArea";

function toNullableNumber(value: string): number | null {
  const trimmedValue = value.trim();

  if (!trimmedValue) {
    return null;
  }

  return Number(trimmedValue);
}

function toNullableString(value: string): string | null {
  const trimmedValue = value.trim();

  return trimmedValue ? trimmedValue : null;
}

export function GoalsPage() {
  const [goals, setGoals] = useState<GoalResponse[]>([]);
  const [lifeAreas, setLifeAreas] = useState<LifeAreaResponse[]>([]);

  const [lifeAreaId, setLifeAreaId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [goalType, setGoalType] = useState<GoalType>("project");
  const [targetValue, setTargetValue] = useState("");
  const [targetUnit, setTargetUnit] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [priority, setPriority] = useState<GoalPriority>("medium");
  const [difficulty, setDifficulty] = useState<GoalDifficulty>("medium");

  const [progressValues, setProgressValues] = useState<Record<number, string>>({});

  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  async function loadData() {
    setError(null);
    setIsLoading(true);

    try {
      const [goalsData, lifeAreasData] = await Promise.all([
        getGoals(),
        getMyLifeAreas(),
      ]);

      setGoals(goalsData);
      setLifeAreas(lifeAreasData);

      if (!lifeAreaId && lifeAreasData.length > 0) {
        setLifeAreaId(String(lifeAreasData[0].id));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load goals.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCreateGoal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!lifeAreaId) {
      setError("Please select a life area first.");
      return;
    }

    setError(null);
    setMessage(null);
    setIsSaving(true);

    try {
      await createGoal({
        life_area_id: Number(lifeAreaId),
        title,
        description: toNullableString(description),
        goal_type: goalType,
        target_value: toNullableNumber(targetValue),
        target_unit: toNullableString(targetUnit),
        start_date: toNullableString(startDate),
        end_date: toNullableString(endDate),
        priority,
        difficulty,
      });

      setTitle("");
      setDescription("");
      setTargetValue("");
      setTargetUnit("");
      setStartDate("");
      setEndDate("");
      setGoalType("project");
      setPriority("medium");
      setDifficulty("medium");

      setMessage("Goal created successfully.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create goal.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleUpdateProgress(goalId: number) {
    const rawValue = progressValues[goalId];

    if (!rawValue || Number(rawValue) < 0) {
      setError("Please enter a valid progress value.");
      return;
    }

    setError(null);
    setMessage(null);

    try {
      await updateGoalProgress(goalId, {
        current_value: Number(rawValue),
      });

      setMessage("Goal progress updated successfully.");
      await loadData();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not update goal progress."
      );
    }
  }

  async function handleCompleteGoal(goalId: number) {
    setError(null);
    setMessage(null);

    try {
      await completeGoal(goalId);
      setMessage("Goal completed successfully.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not complete goal.");
    }
  }

  function getLifeAreaName(areaId: number): string {
    return lifeAreas.find((area) => area.id === areaId)?.name ?? "Unknown";
  }

  useEffect(() => {
    loadData();
  }, []);

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <h1>Goals</h1>
          <p>Create measurable goals for your selected life areas.</p>
        </div>

        <button onClick={loadData}>Refresh</button>
      </header>

      {error && <p className="error-message">{error}</p>}
      {message && <p className="success-message">{message}</p>}

      <section className="content-grid">
        <article className="panel form-panel">
          <h2>Create goal</h2>

          {lifeAreas.length === 0 ? (
            <p>Please select at least one life area before creating goals.</p>
          ) : (
            <form onSubmit={handleCreateGoal} className="form">
              <label>
                Life area
                <select
                  value={lifeAreaId}
                  onChange={(event) => setLifeAreaId(event.target.value)}
                >
                  {lifeAreas.map((area) => (
                    <option key={area.id} value={area.id}>
                      {area.name}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Title
                <input
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="Build GrowthEra MVP"
                />
              </label>

              <label>
                Description
                <textarea
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  rows={4}
                  placeholder="Describe what this goal means and why it matters."
                />
              </label>

              <div className="form-row">
                <label>
                  Goal type
                  <select
                    value={goalType}
                    onChange={(event) =>
                      setGoalType(event.target.value as GoalType)
                    }
                  >
                    <option value="outcome">Outcome</option>
                    <option value="process">Process</option>
                    <option value="habit">Habit</option>
                    <option value="limit">Limit</option>
                    <option value="project">Project</option>
                  </select>
                </label>

                <label>
                  Priority
                  <select
                    value={priority}
                    onChange={(event) =>
                      setPriority(event.target.value as GoalPriority)
                    }
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </label>

                <label>
                  Difficulty
                  <select
                    value={difficulty}
                    onChange={(event) =>
                      setDifficulty(event.target.value as GoalDifficulty)
                    }
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </label>
              </div>

              <div className="form-row">
                <label>
                  Target value
                  <input
                    type="number"
                    min="0"
                    value={targetValue}
                    onChange={(event) => setTargetValue(event.target.value)}
                    placeholder="60"
                  />
                </label>

                <label>
                  Target unit
                  <input
                    value={targetUnit}
                    onChange={(event) => setTargetUnit(event.target.value)}
                    placeholder="minutes, pages, sessions..."
                  />
                </label>
              </div>

              <div className="form-row">
                <label>
                  Start date
                  <input
                    type="date"
                    value={startDate}
                    onChange={(event) => setStartDate(event.target.value)}
                  />
                </label>

                <label>
                  End date
                  <input
                    type="date"
                    value={endDate}
                    onChange={(event) => setEndDate(event.target.value)}
                  />
                </label>
              </div>

              <button type="submit" disabled={isSaving}>
                {isSaving ? "Creating..." : "Create goal"}
              </button>
            </form>
          )}
        </article>

        <article className="panel">
          <h2>Your goals</h2>

          {isLoading ? (
            <p>Loading goals...</p>
          ) : goals.length === 0 ? (
            <p>No goals created yet.</p>
          ) : (
            <div className="list">
              {goals.map((goal) => (
                <div key={goal.id} className="list-item goal-item">
                  <div>
                    <strong>{goal.title}</strong>
                    <p>
                      {getLifeAreaName(goal.life_area_id)} • {goal.goal_type} •{" "}
                      {goal.status}
                    </p>
                    <p>
                      Progress:{" "}
                      {goal.progress_percentage !== null
                        ? `${goal.progress_percentage}%`
                        : "N/A"}
                    </p>
                  </div>

                  <div className="inline-actions">
                    <input
                      className="small-input"
                      type="number"
                      min="0"
                      placeholder="Progress"
                      value={progressValues[goal.id] ?? ""}
                      onChange={(event) =>
                        setProgressValues((current) => ({
                          ...current,
                          [goal.id]: event.target.value,
                        }))
                      }
                    />

                    <button onClick={() => handleUpdateProgress(goal.id)}>
                      Update
                    </button>

                    {goal.status !== "completed" && (
                      <button onClick={() => handleCompleteGoal(goal.id)}>
                        Complete
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>
      </section>
    </main>
  );
}