import { Navigate, Route, Routes } from "react-router";
import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AIInsightsPage } from "./pages/AIInsightsPage";
import { DailyCheckInPage } from "./pages/DailyCheckInPage";
import { DashboardPage } from "./pages/DashboardPage";
import { GardenPage } from "./pages/GardenPage";
import { GoalsPage } from "./pages/GoalsPage";
import { HabitsPage } from "./pages/HabitsPage";
import { LifeAreasPage } from "./pages/LifeAreasPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { TasksPage } from "./pages/TasksPage";

function ProtectedPage({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        path="/dashboard"
        element={
          <ProtectedPage>
            <DashboardPage />
          </ProtectedPage>
        }
      />

      <Route
        path="/life-areas"
        element={
          <ProtectedPage>
            <LifeAreasPage />
          </ProtectedPage>
        }
      />

      <Route
        path="/goals"
        element={
          <ProtectedPage>
            <GoalsPage />
          </ProtectedPage>
        }
      />

      <Route
        path="/habits"
        element={
          <ProtectedPage>
            <HabitsPage />
          </ProtectedPage>
        }
      />

      <Route
        path="/tasks"
        element={
          <ProtectedPage>
            <TasksPage />
          </ProtectedPage>
        }
      />

      <Route
        path="/garden"
        element={
          <ProtectedPage>
            <GardenPage />
          </ProtectedPage>
        }
      />

      <Route
        path="/daily-checkin"
        element={
          <ProtectedPage>
            <DailyCheckInPage />
          </ProtectedPage>
        }
      />

      <Route
        path="/ai-insights"
        element={
          <ProtectedPage>
            <AIInsightsPage />
          </ProtectedPage>
        }
      />

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}