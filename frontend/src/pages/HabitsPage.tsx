import { FormEvent, useEffect, useState } from "react";
import { createHabit, getHabits, logHabit } from "../api/habits";
import { getMyLifeAreas } from "../api/lifeAreas";
import { getActiveGoals } from "../api/goals";
import type { GoalResponse } from "../types/goal";
import type { HabitFrequency, HabitResponse } from "../types/habit";
import type { LifeAreaResponse } from "../types/lifeArea";

function getTodayDateString(): string {
  const now = new Date();
  const timezoneOffset = now.getTimezoneOffset();
  const localDate = new Date(now.getTime() - timezoneOffset * 60 * 1000);

  return localDate.toISOString().slice(0, 10);
}

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

export function HabitsPage() {
  const [habits, setHabits] = useState<HabitResponse[]>([]);
  const [lifeAreas, setLifeAreas] = useState<LifeAreaResponse[]>([]);
  const [goals, setGoals] = useState<GoalResponse[]>([]);

  const [lifeAreaId, setLifeAreaId] = useState("");
  const [goalId, setGoalId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [frequency, setFrequency] = useState<HabitFrequency>("daily");
  const [targetValue, setTargetValue] = useState("");
  const [targetUnit, setTargetUnit] = useState("");

  const [logValues, setLogValues] = useState<Record<number, string>>({});

  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  async function loadData() {
    setError(null);
    setIsLoading(true);

    try {
      const [habitsData, lifeAreasData, goalsData] = await Promise.all([
        getHabits(),
        getMyLifeAreas(),
        getActiveGoals(),
      ]);

      setHabits(habitsData);
      setLifeAreas(lifeAreasData);
      setGoals(goalsData);

      if (!lifeAreaId && lifeAreasData.length > 0) {
        setLifeAreaId(String(lifeAreasData[0].id));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load habits.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCreateHabit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!lifeAreaId) {
      setError("Please select a life area first.");
      return;
    }

    setError(null);
    setMessage(null);
    setIsSaving(true);

    try {
      await createHabit({
        life_area_id: Number(lifeAreaId),
        goal_id: goalId ? Number(goalId) : null,
        title,
        description: toNullableString(description),
        frequency,
        target_value: toNullableNumber(targetValue),
        target_unit: toNullableString(targetUnit),
      });

      setGoalId("");
      setTitle("");
      setDescription("");
      setFrequency("daily");
      setTargetValue("");
      setTargetUnit("");

      setMessage("Habit created successfully.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create habit.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleLogHabit(habit: HabitResponse) {
    setError(null);
    setMessage(null);

    try {
      const rawValue = logValues[habit.id];

      if (habit.target_value !== null && !rawValue) {
        setError("Please enter today's value for this habit.");
        return;
      }

      await logHabit(habit.id, {
        log_date: getTodayDateString(),
        value: rawValue ? Number(rawValue) : null,
        is_completed: true,
        note: "Saved from GrowthEra frontend.",
      });

      setMessage("Habit log saved successfully.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not log habit.");
    }
  }

  function getLifeAreaName(areaId: number): string {
    return lifeAreas.find((area) => area.id === areaId)?.name ?? "Unknown";
  }

  function getGoalTitle(goalIdValue: number | null): string {
    if (goalIdValue === null) {
      return "No linked goal";
    }

    return goals.find((goal) => goal.id === goalIdValue)?.title ?? "Linked goal";
  }

  const filteredGoals = goals.filter((goal) => {
    if (!lifeAreaId) {
      return true;
    }

    return goal.life_area_id === Number(lifeAreaId);
  });

  useEffect(() => {
    loadData();
  }, []);

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <h1>Habits</h1>
          <p>Create repeatable actions that support your goals.</p>
        </div>

        <button onClick={loadData}>Refresh</button>
      </header>

      {error && <p className="error-message">{error}</p>}
      {message && <p className="success-message">{message}</p>}

      <section className="content-grid">
        <article className="panel form-panel">
          <h2>Create habit</h2>

          {lifeAreas.length === 0 ? (
            <p>Please select at least one life area before creating habits.</p>
          ) : (
            <form onSubmit={handleCreateHabit} className="form">
              <label>
                Life area
                <select
                  value={lifeAreaId}
                  onChange={(event) => {
                    setLifeAreaId(event.target.value);
                    setGoalId("");
                  }}
                >
                  {lifeAreas.map((area) => (
                    <option key={area.id} value={area.id}>
                      {area.name}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Contributes to goal optional
                <select
                  value={goalId}
                  onChange={(event) => setGoalId(event.target.value)}
                >
                  <option value="">No linked goal</option>

                  {filteredGoals.map((goal) => (
                    <option key={goal.id} value={goal.id}>
                      {goal.title}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Title
                <input
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="Code for 60 minutes daily"
                />
              </label>

              <label>
                Description
                <textarea
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  rows={4}
                  placeholder="Describe the behavior you want to repeat."
                />
              </label>

              <div className="form-row">
                <label>
                  Frequency
                  <select
                    value={frequency}
                    onChange={(event) =>
                      setFrequency(event.target.value as HabitFrequency)
                    }
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="custom">Custom</option>
                  </select>
                </label>

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
                    placeholder="minutes, pages..."
                  />
                </label>
              </div>

              <button type="submit" disabled={isSaving}>
                {isSaving ? "Creating..." : "Create habit"}
              </button>
            </form>
          )}
        </article>

        <article className="panel">
          <h2>Your habits</h2>

          {isLoading ? (
            <p>Loading habits...</p>
          ) : habits.length === 0 ? (
            <p>No habits created yet.</p>
          ) : (
            <div className="list">
              {habits.map((habit) => (
                <div key={habit.id} className="list-item goal-item">
                  <div>
                    <strong>{habit.title}</strong>
                    <p>
                      {getLifeAreaName(habit.life_area_id)} • {habit.frequency} •{" "}
                      {habit.status}
                    </p>
                    <p>{getGoalTitle(habit.goal_id)}</p>
                    <p>
                      Target:{" "}
                      {habit.target_value !== null
                        ? `${habit.target_value} ${habit.target_unit ?? ""}`
                        : "N/A"}
                    </p>
                  </div>

                  <div className="inline-actions">
                    <input
                      className="small-input"
                      type="number"
                      min="0"
                      placeholder="Today value"
                      value={logValues[habit.id] ?? ""}
                      onChange={(event) =>
                        setLogValues((current) => ({
                          ...current,
                          [habit.id]: event.target.value,
                        }))
                      }
                    />

                    <button onClick={() => handleLogHabit(habit)}>
                      Save today
                    </button>
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