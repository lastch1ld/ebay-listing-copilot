import { AppRouter } from "./router";

export type Environment = "sandbox" | "production";

export function App({ environment }: { environment: Environment }) {
  return (
    <div className="app-shell">
      <header className="app-topbar">
        <div className="brand-lockup">
          <strong className="app-topbar__brand">Listing Copilot</strong>
        </div>
        <strong
          aria-label="Active environment"
          aria-live="polite"
          className={`env-badge${environment === "production" ? " env-badge--production" : ""}`}
        >
          <span className="env-badge__dot" />
          {environment === "sandbox" ? "Sandbox" : "Production"}
        </strong>
      </header>
      <AppRouter />
    </div>
  );
}
