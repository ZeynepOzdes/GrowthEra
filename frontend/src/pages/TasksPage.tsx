import { type FormEvent, useEffect, useMemo, useState } from "react";
import {
  archiveTask,
  completeTask,
  createTask,
  getTasks,
  markTaskAsFire,
  normalizeTaskUrgency,
  startTask,
} from "../api/tasks";
import {
  getActiveFocusSession,
  getTaskFocusSummary,
  startFocusSession,
} from "../api/focusSessions";
import { getGoals } from "../api/goals";
import { getMyLifeAreas } from "../api/lifeAreas";
import type { GoalResponse } from "../types/goal";
import type { LifeAreaResponse } from "../types/lifeArea";
import type { FocusTaskSummaryResponse } from "../types/focusSession";
import type {
  TaskElementType,
  TaskPriority,
  TaskResponse,
  TaskShape,
} from "../types/task";

function formatDate(value: string | null): string {
  if (!value) {
    return "No date";
  }

  return new Date(value).toLocaleDateString();
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "No session yet";
  }

  return new Date(value).toLocaleString();
}

function formatSecondsForDisplay(totalSeconds: number): string {
  if (totalSeconds <= 0) {
    return "0 min";
  }

  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.round((totalSeconds % 3600) / 60);

  if (hours > 0 && minutes > 0) {
    return `${hours}h ${minutes}m`;
  }

  if (hours > 0) {
    return `${hours}h`;
  }

  return `${Math.max(minutes, 1)} min`;
}

function getTodayDateString(): string {
  const now = new Date();
  const timezoneOffset = now.getTimezoneOffset();
  const localDate = new Date(now.getTime() - timezoneOffset * 60 * 1000);

  return localDate.toISOString().slice(0, 10);
}

function getTaskVisualLabel(task: TaskResponse): string {
  if (task.urgency_state === "fire") {
    return "Fire";
  }

  if (task.element_type === "earth" && task.task_shape === "flower") {
    return "Flower";
  }

  if (task.element_type === "earth" && task.task_shape === "rock") {
    return "Rock";
  }

  if (task.element_type === "water") {
    return "Water";
  }

  return "Air";
}

function getPlannedDurationForTimer(task: TaskResponse): number | null {
  if (task.element_type === "earth" && task.task_shape === "flower") {
    return task.planned_duration_minutes;
  }

  return null;
}

function getTotalFocusedSeconds(
  summary: FocusTaskSummaryResponse | undefined
): number {
  if (!summary) {
    return 0;
  }

  return summary.total_focus_seconds + summary.active_session_seconds;
}

function getSafeProgressPercentage(
  summary: FocusTaskSummaryResponse | undefined
): number | null {
  if (!summary || summary.progress_percentage === null) {
    return null;
  }

  return Math.min(Math.round(summary.progress_percentage), 100);
}

function notifyFocusSessionChanged() {
  window.dispatchEvent(new Event("growthera:focus-session-changed"));
}

function notifyTaskUpdated() {
  window.dispatchEvent(new Event("growthera:task-updated"));
}

export function TasksPage() {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [taskSummaries, setTaskSummaries] = useState<FocusTaskSummaryResponse[]>(
    []
  );
  const [lifeAreas, setLifeAreas] = useState<LifeAreaResponse[]>([]);
  const [goals, setGoals] = useState<GoalResponse[]>([]);

  const [lifeAreaId, setLifeAreaId] = useState("");
  const [goalId, setGoalId] = useState("");

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const [elementType, setElementType] = useState<TaskElementType>("earth");
  const [taskShape, setTaskShape] = useState<TaskShape>("flower");
  const [priority, setPriority] = useState<TaskPriority>("medium");

  const [plannedDate, setPlannedDate] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [plannedDurationMinutes, setPlannedDurationMinutes] = useState("");

  const [filterElement, setFilterElement] = useState<TaskElementType | "all">(
    "all"
  );

  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);

  const todayDateString = getTodayDateString();

  const shouldShowPlannedDuration =
    elementType === "earth" && taskShape === "flower";

  const visibleGoals = useMemo(() => {
    if (!lifeAreaId) {
      return goals;
    }

    return goals.filter((goal) => goal.life_area_id === Number(lifeAreaId));
  }, [goals, lifeAreaId]);

  const taskSummaryByTaskId = useMemo(() => {
    return new Map(
      taskSummaries.map((summary) => [summary.task_id, summary])
    );
  }, [taskSummaries]);

  async function loadData() {
    setError(null);
    setIsLoading(true);

    try {
      const [tasksData, taskSummaryData, lifeAreasData, goalsData] =
        await Promise.all([
          getTasks(),
          getTaskFocusSummary(),
          getMyLifeAreas(),
          getGoals(),
        ]);

      const visibleTasks = tasksData.filter(
        (task) => task.status === "active" || task.status === "ongoing"
      );

      setTasks(visibleTasks);
      setTaskSummaries(taskSummaryData);
      setLifeAreas(lifeAreasData);
      setGoals(goalsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load tasks.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCreateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError(null);
    setMessage(null);

    if (!lifeAreaId) {
      setError("Please select a life area.");
      return;
    }

    if (plannedDate && plannedDate < todayDateString) {
      setError("Planned date cannot be in the past.");
      return;
    }

    if (dueDate && dueDate < todayDateString) {
      setError("Due date cannot be in the past.");
      return;
    }

    if (plannedDate && dueDate && plannedDate > dueDate) {
      setError("Planned date cannot be later than due date.");
      return;
    }

    if (elementType === "earth" && !dueDate) {
      setError("Earth tasks require a due date.");
      return;
    }

    if (elementType === "earth" && !taskShape) {
      setError("Earth tasks require a flower or rock type.");
      return;
    }

    setIsCreating(true);

    try {
      await createTask({
        life_area_id: Number(lifeAreaId),
        goal_id: goalId ? Number(goalId) : null,

        title,
        description: description || null,

        element_type: elementType,
        urgency_state: "normal",
        task_shape: elementType === "earth" ? taskShape : null,

        planned_date: plannedDate || null,
        due_date: dueDate || null,

        planned_duration_minutes:
          shouldShowPlannedDuration && plannedDurationMinutes
            ? Number(plannedDurationMinutes)
            : null,

        priority,
      });

      setMessage("Task created successfully.");

      setTitle("");
      setDescription("");
      setGoalId("");
      setPlannedDate("");
      setDueDate("");
      setPlannedDurationMinutes("");
      setElementType("earth");
      setTaskShape("flower");
      setPriority("medium");

      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create task.");
    } finally {
      setIsCreating(false);
    }
  }

  async function handleStartTask(task: TaskResponse) {
    setError(null);
    setMessage(null);

    try {
      const activeSession = await getActiveFocusSession();

      if (activeSession) {
        if (activeSession.task_id === task.id) {
          window.alert(
            "This task already has an active focus timer. Please use the timer panel to pause, resume, finish, or cancel it."
          );
        } else {
          window.alert(
            "A focus timer is already active. Please finish or cancel the current timer before starting a new one."
          );
        }

        return;
      }

      const wantsTimer = window.confirm(
        "Start a timer for this task? Press OK to start a timer, or Cancel to mark it as ongoing without a timer."
      );

      if (wantsTimer) {
        await startFocusSession({
          life_area_id: task.life_area_id,
          goal_id: task.goal_id,
          habit_id: null,
          task_id: task.id,
          title: task.title,
          session_type: "task",
          planned_duration_minutes: getPlannedDurationForTimer(task),
          note: "Started from the task screen.",
        });

        setMessage("Timer started. Task marked as ongoing.");
        notifyFocusSessionChanged();
      } else {
        await startTask(task.id);
        setMessage("Task marked as ongoing without timer.");
      }

      notifyTaskUpdated();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start task.");
    }
  }

  async function handleCompleteTask(taskId: number) {
    setError(null);
    setMessage(null);

    try {
      await completeTask(taskId);
      setMessage("Task completed successfully.");
      notifyTaskUpdated();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not complete task.");
    }
  }

  async function handleArchiveTask(taskId: number) {
    setError(null);
    setMessage(null);

    try {
      await archiveTask(taskId);
      setMessage("Task archived successfully.");
      notifyTaskUpdated();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not archive task.");
    }
  }

  async function handleToggleFire(task: TaskResponse) {
    setError(null);
    setMessage(null);

    try {
      if (task.urgency_state === "fire") {
        await normalizeTaskUrgency(task.id);
        setMessage("Task urgency normalized.");
      } else {
        await markTaskAsFire(task.id);
        setMessage("Task moved to fire urgency.");
      }

      notifyTaskUpdated();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update urgency.");
    }
  }

  useEffect(() => {
    loadData();

    window.addEventListener("growthera:task-updated", loadData);
    window.addEventListener("growthera:focus-session-changed", loadData);

    return () => {
      window.removeEventListener("growthera:task-updated", loadData);
      window.removeEventListener("growthera:focus-session-changed", loadData);
    };
  }, []);

  useEffect(() => {
    if (!shouldShowPlannedDuration) {
      setPlannedDurationMinutes("");
    }
  }, [shouldShowPlannedDuration]);

  const filteredTasks =
    filterElement === "all"
      ? tasks
      : tasks.filter((task) => task.element_type === filterElement);

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <h1>Tasks</h1>
          <p>
            Organize your work with earth, water, air, flowers, rocks, and fire
            urgency.
          </p>
        </div>

        <button onClick={loadData}>Refresh</button>
      </header>

      {error && <p className="error-message">{error}</p>}
      {message && <p className="success-message">{message}</p>}

      <section className="panel">
        <h2>Create task</h2>

        <form className="form-grid" onSubmit={handleCreateTask}>
          <label>
            Life area
            <select
              value={lifeAreaId}
              onChange={(event) => {
                setLifeAreaId(event.target.value);
                setGoalId("");
              }}
              required
            >
              <option value="">Select life area</option>
              {lifeAreas.map((lifeArea) => (
                <option key={lifeArea.id} value={lifeArea.id}>
                  {lifeArea.name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Goal optional
            <select
              value={goalId}
              onChange={(event) => setGoalId(event.target.value)}
            >
              <option value="">No linked goal</option>
              {visibleGoals.map((goal) => (
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
              placeholder="Plan GrowthEra timer module"
              required
            />
          </label>

          <label>
            Description
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Describe what needs to be done."
            />
          </label>

          <label>
            Element
            <select
              value={elementType}
              onChange={(event) => {
                const nextElement = event.target.value as TaskElementType;

                setElementType(nextElement);

                if (nextElement !== "earth") {
                  setTaskShape("flower");
                }
              }}
            >
              <option value="earth">Earth</option>
              <option value="water">Water</option>
              <option value="air">Air</option>
            </select>
          </label>

          {elementType === "earth" && (
            <label>
              Earth type
              <select
                value={taskShape}
                onChange={(event) =>
                  setTaskShape(event.target.value as TaskShape)
                }
              >
                <option value="flower">Flower</option>
                <option value="rock">Rock</option>
              </select>
            </label>
          )}

          <label>
            Priority
            <select
              value={priority}
              onChange={(event) =>
                setPriority(event.target.value as TaskPriority)
              }
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </label>

          <label>
            Planned date
            <input
              type="date"
              min={todayDateString}
              value={plannedDate}
              onChange={(event) => {
                const nextPlannedDate = event.target.value;

                setPlannedDate(nextPlannedDate);

                if (dueDate && nextPlannedDate && dueDate < nextPlannedDate) {
                  setDueDate(nextPlannedDate);
                }
              }}
            />
          </label>

          <label>
            Due date {elementType === "earth" ? "" : "optional"}
            <input
              type="date"
              min={plannedDate || todayDateString}
              value={dueDate}
              onChange={(event) => setDueDate(event.target.value)}
              required={elementType === "earth"}
            />
          </label>

          {shouldShowPlannedDuration && (
            <label>
              Planned duration minutes
              <input
                type="number"
                min="1"
                max="1440"
                value={plannedDurationMinutes}
                onChange={(event) =>
                  setPlannedDurationMinutes(event.target.value)
                }
                placeholder="45"
              />
            </label>
          )}

          <button type="submit" disabled={isCreating}>
            {isCreating ? "Creating..." : "Create task"}
          </button>
        </form>
      </section>

      <section className="panel">
        <div className="section-header">
          <h2>Active and ongoing tasks</h2>

          <select
            value={filterElement}
            onChange={(event) =>
              setFilterElement(event.target.value as TaskElementType | "all")
            }
          >
            <option value="all">All elements</option>
            <option value="earth">Earth</option>
            <option value="water">Water</option>
            <option value="air">Air</option>
          </select>
        </div>

        {isLoading ? (
          <p>Loading tasks...</p>
        ) : filteredTasks.length === 0 ? (
          <p>No active or ongoing tasks found.</p>
        ) : (
          <div className="task-list">
            {filteredTasks.map((task) => {
              const summary = taskSummaryByTaskId.get(task.id);
              const totalFocusedSeconds = getTotalFocusedSeconds(summary);
              const progressPercentage = getSafeProgressPercentage(summary);

              return (
                <article key={task.id} className="task-card">
                  <div className="task-card-header">
                    <div>
                      <span
                        className={`task-badge task-badge-${task.element_type} ${
                          task.urgency_state === "fire" ? "task-badge-fire" : ""
                        }`}
                      >
                        {getTaskVisualLabel(task)}
                      </span>

                      <h3>{task.title}</h3>

                      {task.description && <p>{task.description}</p>}
                    </div>

                    <span className={`priority priority-${task.priority}`}>
                      {task.priority}
                    </span>
                  </div>

                  <div className="task-meta">
                    <span>Status: {task.status}</span>
                    <span>Planned: {formatDate(task.planned_date)}</span>
                    <span>Due: {formatDate(task.due_date)}</span>

                    {task.element_type === "earth" &&
                      task.task_shape === "flower" && (
                        <span>
                          Duration:{" "}
                          {task.planned_duration_minutes
                            ? `${task.planned_duration_minutes} min`
                            : "Not planned"}
                        </span>
                      )}
                  </div>

                  <div className="task-focus-summary">
                    <div className="task-focus-summary-row">
                      <span>Focused total</span>
                      <strong>{formatSecondsForDisplay(totalFocusedSeconds)}</strong>
                    </div>

                    <div className="task-focus-summary-row">
                      <span>Sessions</span>
                      <strong>{summary?.completed_sessions_count ?? 0}</strong>
                    </div>

                    <div className="task-focus-summary-row">
                      <span>Last session</span>
                      <strong>{formatDateTime(summary?.last_session_at ?? null)}</strong>
                    </div>

                    {summary?.has_active_session && (
                      <div className="task-focus-summary-row">
                        <span>Active now</span>
                        <strong>
                          {formatSecondsForDisplay(summary.active_session_seconds)}
                        </strong>
                      </div>
                    )}

                    {progressPercentage !== null && (
                      <>
                        <div className="task-focus-summary-row">
                          <span>Time progress</span>
                          <strong>
                            {progressPercentage}%
                            {summary?.is_over_planned ? " • Over planned" : ""}
                          </strong>
                        </div>

                        <div className="task-card-progress">
                          <div
                            className={`task-card-progress-bar ${
                              summary?.is_over_planned
                                ? "task-card-progress-bar-over"
                                : ""
                            }`}
                            style={{ width: `${progressPercentage}%` }}
                          />
                        </div>
                      </>
                    )}
                  </div>

                  <div className="task-actions">
                    {(task.status === "active" || task.status === "ongoing") && (
                      <button onClick={() => handleStartTask(task)}>
                        {task.status === "ongoing"
                          ? "Continue"
                          : "Start / Ongoing"}
                      </button>
                    )}

                    <button onClick={() => handleCompleteTask(task.id)}>
                      Complete
                    </button>

                    {task.element_type === "earth" && (
                      <button onClick={() => handleToggleFire(task)}>
                        {task.urgency_state === "fire"
                          ? "Normalize"
                          : "Mark as fire"}
                      </button>
                    )}

                    <button onClick={() => handleArchiveTask(task.id)}>
                      Archive
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}