import { useEffect, useState } from "react";
import {
  createDailyReview,
  getAiInsights,
  updateAiInsightStatus,
} from "../api/ai";
import type { AiInsightResponse } from "../types/ai";

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

export function AIInsightsPage() {
  const [insights, setInsights] = useState<AiInsightResponse[]>([]);

  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isCreatingReview, setIsCreatingReview] = useState(false);

  async function loadInsights() {
    setError(null);
    setIsLoading(true);

    try {
      const data = await getAiInsights();
      setInsights(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load insights.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCreateDailyReview() {
    setError(null);
    setMessage(null);
    setIsCreatingReview(true);

    try {
      await createDailyReview();
      setMessage("Daily review generated successfully.");
      await loadInsights();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not generate daily review."
      );
    } finally {
      setIsCreatingReview(false);
    }
  }

  async function handleArchiveInsight(insightId: number) {
    setError(null);
    setMessage(null);

    try {
      await updateAiInsightStatus(insightId, "archived");
      setMessage("Insight archived successfully.");
      await loadInsights();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not archive insight."
      );
    }
  }

  useEffect(() => {
    loadInsights();
  }, []);

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <h1>AI Insights</h1>
          <p>Review personalized feedback based on your goals, habits, and check-ins.</p>
        </div>

        <div className="header-actions">
          <button onClick={loadInsights}>Refresh</button>
          <button onClick={handleCreateDailyReview} disabled={isCreatingReview}>
            {isCreatingReview ? "Generating..." : "Generate daily review"}
          </button>
        </div>
      </header>

      {error && <p className="error-message">{error}</p>}
      {message && <p className="success-message">{message}</p>}

      {isLoading ? (
        <section className="panel">
          <p>Loading AI insights...</p>
        </section>
      ) : insights.length === 0 ? (
        <section className="panel">
          <h2>No insights yet</h2>
          <p>
            Generate a daily review after adding goals, habits, and a daily check-in.
          </p>
        </section>
      ) : (
        <section className="insight-list">
          {insights.map((insight) => (
            <article key={insight.id} className="insight-card">
              <div className="insight-card-header">
                <div>
                  <span className="insight-type">{insight.insight_type}</span>
                  <h2>{insight.title}</h2>
                  <p>
                    {insight.source} • {formatDate(insight.created_at)}
                  </p>
                </div>

                <button onClick={() => handleArchiveInsight(insight.id)}>
                  Archive
                </button>
              </div>

              <p className="insight-content">{insight.content}</p>

              {insight.recommendation && (
                <div className="recommendation-box">
                  <strong>Recommendation</strong>
                  <p>{insight.recommendation}</p>
                </div>
              )}
            </article>
          ))}
        </section>
      )}
    </main>
  );
}