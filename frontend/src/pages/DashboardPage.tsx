import { useEffect, useState } from "react";
import { getDashboardSummary } from "../api/dashboard";
import { getFocusDashboardSummary } from "../api/focusSessions";
import type { DashboardSummaryResponse } from "../types/dashboard";
import type { FocusDashboardSummaryResponse } from "../types/focusSession";

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

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [focusSummary, setFocusSummary] =
    useState<FocusDashboardSummaryResponse | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  async function loadDashboard() {
    setError(null);
    setIsLoading(true);

    try {
      const [dashboardData, focusData] = await Promise.all([
        getDashboardSummary(),
        getFocusDashboardSummary(),
      ]);

      setSummary(dashboardData);
      setFocusSummary(focusData);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load dashboard."
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();

    window.addEventListener("growthera:task-updated", loadDashboard);
    window.addEventListener("growthera:focus-session-changed", loadDashboard);

    return () => {
      window.removeEventListener("growthera:task-updated", loadDashboard);
      window.removeEventListener(
        "growthera:focus-session-changed",
        loadDashboard
      );
    };
  }, []);

  if (isLoading) {
    return (
      <main className="page">
        <p>Loading dashboard...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page">
        <section className="panel">
          <p className="error-message">{error}</p>
          <button onClick={loadDashboard}>Try again</button>
        </section>
      </main>
    );
  }

  if (!summary || !focusSummary) {
    return null;
  }

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>Your personal growth overview for today.</p>
        </div>

        <button onClick={loadDashboard}>Refresh</button>
      </header>

      <section className="stats-grid">
        <article className="stat-card">
          <span>Active goals</span>
          <strong>{summary.active_goals_count}</strong>
        </article>

        <article className="stat-card">
          <span>Active habits</span>
          <strong>{summary.active_habits_count}</strong>
        </article>

        <article className="stat-card">
          <span>Completed today</span>
          <strong>
            {summary.completed_habits_today}/{summary.active_habits_count}
          </strong>
        </article>

        <article className="stat-card">
          <span>Completion rate</span>
          <strong>
            {summary.habit_completion_rate_today !== null
              ? `${summary.habit_completion_rate_today}%`
              : "N/A"}
          </strong>
        </article>
      </section>

      <section className="stats-grid">
        <article className="stat-card stat-card-focus">
          <span>Today focused</span>
          <strong>
            {formatSecondsForDisplay(focusSummary.today_focus_seconds)}
          </strong>
        </article>

        <article className="stat-card stat-card-focus">
          <span>Sessions today</span>
          <strong>{focusSummary.completed_sessions_today}</strong>
        </article>

        <article className="stat-card stat-card-focus">
          <span>Total focused</span>
          <strong>
            {formatSecondsForDisplay(focusSummary.total_focus_seconds)}
          </strong>
        </article>

        <article className="stat-card stat-card-focus">
          <span>Total sessions</span>
          <strong>{focusSummary.completed_sessions_total}</strong>
        </article>
      </section>

      <section className="content-grid">
        <article className="panel">
          <h2>Active timer</h2>

          {focusSummary.has_active_session ? (
            <div className="active-focus-card">
              <span className="active-focus-label">
                {focusSummary.active_session_status}
              </span>

              <h3>{focusSummary.active_session_title}</h3>

              <p>
                Current session:{" "}
                <strong>
                  {formatSecondsForDisplay(focusSummary.active_session_seconds)}
                </strong>
              </p>

              {focusSummary.active_session_task_id !== null && (
                <p>Linked task ID: {focusSummary.active_session_task_id}</p>
              )}

              <p className="note">
                Use the floating timer panel to pause, resume, finish, or cancel
                this session.
              </p>
            </div>
          ) : (
            <p>No active focus timer right now.</p>
          )}
        </article>

        <article className="panel">
          <h2>Selected life areas</h2>

          {summary.selected_life_areas.length === 0 ? (
            <p>No life areas selected yet.</p>
          ) : (
            <div className="pill-list">
              {summary.selected_life_areas.map((area) => (
                <span key={area.id} className="pill">
                  {area.name}
                </span>
              ))}
            </div>
          )}
        </article>

        <article className="panel">
          <h2>Today&apos;s check-in</h2>

          {summary.today_checkin ? (
            <div className="checkin-grid">
              <span>Mood: {summary.today_checkin.mood_score ?? "N/A"}</span>
              <span>Energy: {summary.today_checkin.energy_score ?? "N/A"}</span>
              <span>Focus: {summary.today_checkin.focus_score ?? "N/A"}</span>
              <span>Stress: {summary.today_checkin.stress_score ?? "N/A"}</span>
              <span>
                Sleep: {summary.today_checkin.sleep_quality_score ?? "N/A"}
              </span>

              {summary.today_checkin.note && (
                <p className="note">{summary.today_checkin.note}</p>
              )}
            </div>
          ) : (
            <p>You have not completed today&apos;s check-in yet.</p>
          )}
        </article>

        <article className="panel">
          <h2>Top active goals</h2>

          {summary.top_active_goals.length === 0 ? (
            <p>No active goals yet.</p>
          ) : (
            <div className="list">
              {summary.top_active_goals.map((goal) => (
                <div key={goal.id} className="list-item">
                  <div>
                    <strong>{goal.title}</strong>
                    <p>
                      {goal.goal_type} • {goal.priority}
                    </p>
                  </div>

                  <span>
                    {goal.progress_percentage !== null
                      ? `${goal.progress_percentage}%`
                      : "N/A"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </article>

        <article className="panel">
          <h2>Today&apos;s habits</h2>

          {summary.today_habits.length === 0 ? (
            <p>No active habits yet.</p>
          ) : (
            <div className="list">
              {summary.today_habits.map((habit) => (
                <div key={habit.id} className="list-item">
                  <div>
                    <strong>{habit.title}</strong>
                    <p>
                      Target:{" "}
                      {habit.target_value !== null
                        ? `${habit.target_value} ${habit.target_unit ?? ""}`
                        : "N/A"}
                    </p>

                    {habit.today_value !== null && (
                      <p>
                        Today: {habit.today_value} {habit.target_unit ?? ""}
                      </p>
                    )}
                  </div>

                  <span
                    className={
                      habit.completed_today ? "status-done" : "status-pending"
                    }
                  >
                    {habit.completed_today
                      ? "Done"
                      : habit.today_value !== null
                        ? "Partial"
                        : "Pending"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </article>
      </section>
    </main>
  );
}