import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router";
import { loginUser, saveToken } from "../api/auth";

export function LoginPage() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("zeyne");
  const [password, setPassword] = useState("123456");

  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError(null);
    setIsLoading(true);

    try {
      const tokenResponse = await loginUser({
        username,
        password,
      });

      saveToken(tokenResponse.access_token);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="brand">
          <span className="brand-mark">G</span>
          <div>
            <h1>GrowthEra</h1>
            <p>Build your personal growth system.</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="form">
          <label>
            Username
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="Enter your username"
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
            />
          </label>

          {error && <p className="error-message">{error}</p>}

          <button type="submit" disabled={isLoading}>
            {isLoading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="auth-footer">
          Do not have an account? <Link to="/register">Create one</Link>
        </p>
      </section>
    </main>
  );
}