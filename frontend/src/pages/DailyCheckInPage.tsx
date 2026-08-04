import { FormEvent, useEffect, useState } from "react";
import {
  createOrUpdateDailyCheckIn,
  getTodayCheckIn,
} from "../api/dailyCheckins";

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

function toInputValue(value: number | null): string {
  return value === null ? "" : String(value);
}

export function DailyCheckInPage() {
  const [checkinDate, setCheckinDate] = useState(getTodayDateString());

  const [moodScore, setMoodScore] = useState("");
  const [energyScore, setEnergyScore] = useState("");
  const [focusScore, setFocusScore] = useState("");
  const [stressScore, setStressScore] = useState("");
  const [sleepQualityScore, setSleepQualityScore] = useState("");
  const [note, setNote] = useState("");

  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  async function loadTodayCheckIn() {
    setError(null);
    setIsLoading(true);

    try {
      const todayCheckIn = await getTodayCheckIn();

      if (todayCheckIn) {
        setCheckinDate(todayCheckIn.checkin_date);
        setMoodScore(toInputValue(todayCheckIn.mood_score));
        setEnergyScore(toInputValue(todayCheckIn.energy_score));
        setFocusScore(toInputValue(todayCheckIn.focus_score));
        setStressScore(toInputValue(todayCheckIn.stress_score));
        setSleepQualityScore(toInputValue(todayCheckIn.sleep_quality_score));
        setNote(todayCheckIn.note ?? "");
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load today's check-in."
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError(null);
    setMessage(null);
    setIsSaving(true);

    try {
      await createOrUpdateDailyCheckIn({
        checkin_date: checkinDate,
        mood_score: toNullableNumber(moodScore),
        energy_score: toNullableNumber(energyScore),
        focus_score: toNullableNumber(focusScore),
        stress_score: toNullableNumber(stressScore),
        sleep_quality_score: toNullableNumber(sleepQualityScore),
        note: note.trim() ? note : null,
      });

      setMessage("Daily check-in saved successfully.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not save daily check-in."
      );
    } finally {
      setIsSaving(false);
    }
  }

  useEffect(() => {
    loadTodayCheckIn();
  }, []);

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <h1>Daily Check-in</h1>
          <p>Reflect on your mood, energy, focus, stress, and sleep quality.</p>
        </div>
      </header>

      {isLoading ? (
        <section className="panel">
          <p>Loading today&apos;s check-in...</p>
        </section>
      ) : (
        <section className="panel form-panel">
          <form onSubmit={handleSubmit} className="form">
            <label>
              Date
              <input
                type="date"
                value={checkinDate}
                onChange={(event) => setCheckinDate(event.target.value)}
              />
            </label>

            <div className="score-grid">
              <label>
                Mood
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={moodScore}
                  onChange={(event) => setMoodScore(event.target.value)}
                  placeholder="1-10"
                />
              </label>

              <label>
                Energy
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={energyScore}
                  onChange={(event) => setEnergyScore(event.target.value)}
                  placeholder="1-10"
                />
              </label>

              <label>
                Focus
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={focusScore}
                  onChange={(event) => setFocusScore(event.target.value)}
                  placeholder="1-10"
                />
              </label>

              <label>
                Stress
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={stressScore}
                  onChange={(event) => setStressScore(event.target.value)}
                  placeholder="1-10"
                />
              </label>

              <label>
                Sleep quality
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={sleepQualityScore}
                  onChange={(event) =>
                    setSleepQualityScore(event.target.value)
                  }
                  placeholder="1-10"
                />
              </label>
            </div>

            <label>
              Note
              <textarea
                value={note}
                onChange={(event) => setNote(event.target.value)}
                placeholder="Write a short reflection about your day..."
                rows={5}
              />
            </label>

            {error && <p className="error-message">{error}</p>}
            {message && <p className="success-message">{message}</p>}

            <button type="submit" disabled={isSaving}>
              {isSaving ? "Saving..." : "Save check-in"}
            </button>
          </form>
        </section>
      )}
    </main>
  );
}