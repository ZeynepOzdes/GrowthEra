import type { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router";
import { TOKEN_STORAGE_KEY } from "../api/client";
import { FloatingTimer } from "./FloatingTimer";

type AppLayoutProps = {
  children: ReactNode;
};

export function AppLayout({ children }: AppLayoutProps) {
  const navigate = useNavigate();

  function handleLogout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <div className="brand">
            <div className="brand-icon">G</div>
            <div>
              <strong>GrowthEra</strong>
              <span>Personal growth system</span>
            </div>
          </div>

          <nav className="sidebar-nav">
            <NavLink to="/dashboard">Dashboard</NavLink>
            <NavLink to="/life-areas">Life Areas</NavLink>
            <NavLink to="/goals">Goals</NavLink>
            <NavLink to="/habits">Habits</NavLink>
            <NavLink to="/tasks">Tasks</NavLink>
            <NavLink to="/daily-checkin">Daily Check-in</NavLink>
            <NavLink to="/ai-insights">AI Insights</NavLink>
          </nav>
        </div>

        <button className="logout-button" onClick={handleLogout}>
          Logout
        </button>
      </aside>

      <div className="app-content">{children}</div>

      <FloatingTimer />
    </div>
  );
}