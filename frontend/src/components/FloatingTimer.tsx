import { useEffect, useState } from "react";
import { completeTask } from "../api/tasks";
import {
  cancelFocusSession,
  completeFocusSession,
  getActiveFocusSession,
  getFocusSessions,
  pauseFocusSession,
  resumeFocusSession,
} from "../api/focusSessions";
import type { FocusSessionResponse } from "../types/focusSession";

function parseApiDate(value: string): Date {
  const hasTimezone =
    value.endsWith("Z") ||
    value.includes("+") ||
    /-\d{2}:\d{2}$/.test(value);

  if (hasTimezone) {
    return new Date(value);
  }

  return new Date(`${value}Z`);
}

function calculateCurrentSessionSeconds(
  session: FocusSessionResponse | null
): number {
  if (!session) {
    return 0;
  }

  const baseSeconds = session.accumulated_seconds ?? 0;

  if (session.status !== "running" || !session.last_resumed_at) {
    return baseSeconds;
  }

  const lastResumedAt = parseApiDate(session.last_resumed_at).getTime();
  const now = Date.now();

  const currentIntervalSeconds = Math.floor((now - lastResumedAt) / 1000);

  return baseSeconds + Math.max(currentIntervalSeconds, 0);
}

function formatSeconds(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  const paddedHours = String(hours).padStart(2, "0");
  const paddedMinutes = String(minutes).padStart(2, "0");
  const paddedSeconds = String(seconds).padStart(2, "0");

  if (hours > 0) {
    return `${paddedHours}:${paddedMinutes}:${paddedSeconds}`;
  }

  return `${paddedMinutes}:${paddedSeconds}`;
}

function notifyFocusSessionChanged() {
  window.dispatchEvent(new Event("growthera:focus-session-changed"));
}

function notifyTaskUpdated() {
  window.dispatchEvent(new Event("growthera:task-updated"));
}

async function getPreviousCompletedSecondsForTask(
  session: FocusSessionResponse
): Promise<number> {
  if (session.task_id === null) {
    return 0;
  }

  const taskSessions = await getFocusSessions({
    task_id: session.task_id,
    limit: 100,
  });

  return taskSessions
    .filter(
      (taskSession) =>
        taskSession.id !== session.id && taskSession.status === "completed"
    )
    .reduce((total, taskSession) => {
      return total + (taskSession.duration_seconds ?? 0);
    }, 0);
}

export function FloatingTimer() {
  const [activeSession, setActiveSession] =
    useState<FocusSessionResponse | null>(null);

  const [previousTaskSeconds, setPreviousTaskSeconds] = useState(0);
  const [currentSessionSeconds, setCurrentSessionSeconds] = useState(0);

  const [error, setError] = useState<string | null>(null);
  const [isWorking, setIsWorking] = useState(false);

  async function loadActiveSession() {
    try {
      const session = await getActiveFocusSession();

      if (!session) {
        setActiveSession(null);
        setPreviousTaskSeconds(0);
        setCurrentSessionSeconds(0);
        setError(null);
        return;
      }

      const previousSeconds = await getPreviousCompletedSecondsForTask(session);

      setActiveSession(session);
      setPreviousTaskSeconds(previousSeconds);
      setCurrentSessionSeconds(calculateCurrentSessionSeconds(session));
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load active timer."
      );
    }
  }

  async function handlePause() {
    if (!activeSession) {
      return;
    }

    setIsWorking(true);
    setError(null);

    try {
      const updatedSession = await pauseFocusSession(activeSession.id);

      setActiveSession(updatedSession);
      setCurrentSessionSeconds(calculateCurrentSessionSeconds(updatedSession));

      notifyFocusSessionChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not pause timer.");
    } finally {
      setIsWorking(false);
    }
  }

  async function handleResume() {
    if (!activeSession) {
      return;
    }

    setIsWorking(true);
    setError(null);

    try {
      const updatedSession = await resumeFocusSession(activeSession.id);

      setActiveSession(updatedSession);
      setCurrentSessionSeconds(calculateCurrentSessionSeconds(updatedSession));

      notifyFocusSessionChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not resume timer.");
    } finally {
      setIsWorking(false);
    }
  }

  async function handleFinish() {
    if (!activeSession) {
      return;
    }

    setIsWorking(true);
    setError(null);

    try {
      const completedSession = await completeFocusSession(activeSession.id);

      let shouldCompleteLinkedTask = false;

      if (completedSession.task_id !== null) {
        shouldCompleteLinkedTask = window.confirm(
          "Focus session saved. Did you also complete this task?"
        );
      }

      if (shouldCompleteLinkedTask && completedSession.task_id !== null) {
        await completeTask(completedSession.task_id);
        notifyTaskUpdated();
      } else if (completedSession.task_id !== null) {
        window.alert(
          "Focus session saved. The task is still ongoing. You can continue it later from the task card."
        );
        notifyTaskUpdated();
      }

      setActiveSession(null);
      setPreviousTaskSeconds(0);
      setCurrentSessionSeconds(0);

      notifyFocusSessionChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not finish timer.");
    } finally {
      setIsWorking(false);
    }
  }

  async function handleCancel() {
    if (!activeSession) {
      return;
    }

    const confirmed = window.confirm(
      "Do you want to cancel this focus session? The task will not be completed."
    );

    if (!confirmed) {
      return;
    }

    setIsWorking(true);
    setError(null);

    try {
      await cancelFocusSession(activeSession.id);

      setActiveSession(null);
      setPreviousTaskSeconds(0);
      setCurrentSessionSeconds(0);

      notifyFocusSessionChanged();
      notifyTaskUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not cancel timer.");
    } finally {
      setIsWorking(false);
    }
  }

  useEffect(() => {
    loadActiveSession();

    window.addEventListener("focus", loadActiveSession);
    window.addEventListener("growthera:focus-session-changed", loadActiveSession);

    return () => {
      window.removeEventListener("focus", loadActiveSession);
      window.removeEventListener(
        "growthera:focus-session-changed",
        loadActiveSession
      );
    };
  }, []);

  useEffect(() => {
    if (!activeSession || activeSession.status !== "running") {
      return;
    }

    const intervalId = window.setInterval(() => {
      setCurrentSessionSeconds(calculateCurrentSessionSeconds(activeSession));
    }, 1000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [activeSession]);

  if (!activeSession) {
    return null;
  }

  const totalTaskSeconds = previousTaskSeconds + currentSessionSeconds;

  const plannedSeconds = activeSession.planned_duration_minutes
    ? activeSession.planned_duration_minutes * 60
    : null;

  const progressPercentage =
    plannedSeconds && plannedSeconds > 0
      ? Math.min(Math.round((totalTaskSeconds / plannedSeconds) * 100), 100)
      : null;

  const hasReachedPlannedDuration =
    plannedSeconds !== null && totalTaskSeconds >= plannedSeconds;

  const overtimeSeconds =
    plannedSeconds !== null && totalTaskSeconds > plannedSeconds
      ? totalTaskSeconds - plannedSeconds
      : 0;

  return (
    <aside className="floating-timer">
      <div className="floating-timer-header">
        <div>
          <span className="floating-timer-label">
            {activeSession.status === "paused"
              ? "Paused"
              : hasReachedPlannedDuration
                ? "Planned time reached"
                : "Focus timer"}
          </span>
          <h3>{activeSession.title}</h3>
        </div>

        <button
          type="button"
          className="timer-close-button"
          onClick={handleCancel}
          disabled={isWorking}
        >
          ×
        </button>
      </div>

      <div className="timer-time">{formatSeconds(totalTaskSeconds)}</div>

      {previousTaskSeconds > 0 && (
        <p className="timer-planned">
          Current session: {formatSeconds(currentSessionSeconds)} • Previous:{" "}
          {formatSeconds(previousTaskSeconds)}
        </p>
      )}

      {activeSession.planned_duration_minutes && (
        <p className="timer-planned">
          Planned: {activeSession.planned_duration_minutes} min
          {progressPercentage !== null && ` • ${progressPercentage}%`}
        </p>
      )}

      {progressPercentage !== null && (
        <div className="timer-progress">
          <div
            className={`timer-progress-bar ${
              hasReachedPlannedDuration ? "timer-progress-bar-complete" : ""
            }`}
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      )}

      {hasReachedPlannedDuration && (
        <div className="timer-status-box">
          <strong>Planned time reached.</strong>
          <p>
            You have reached the planned focus duration for this task. You can
            finish the session now or continue working if the task still needs
            more time.
          </p>

          {overtimeSeconds > 0 && (
            <p>Over planned time: {formatSeconds(overtimeSeconds)}</p>
          )}
        </div>
      )}

      {error && <p className="timer-error">{error}</p>}

      <div className="timer-actions">
        {activeSession.status === "running" ? (
          <button onClick={handlePause} disabled={isWorking}>
            Pause
          </button>
        ) : (
          <button onClick={handleResume} disabled={isWorking}>
            Resume
          </button>
        )}

        <button onClick={handleFinish} disabled={isWorking}>
          Finish
        </button>
      </div>
    </aside>
  );
}