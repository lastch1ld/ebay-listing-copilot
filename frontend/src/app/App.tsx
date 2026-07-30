import { AppRouter } from "./router";

export type Environment = "sandbox" | "production";

export function App({ environment }: { environment: Environment }) {
  return (
    <div className="app-shell">
      <header className="app-topbar">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">
            <i />
            <i />
            <i />
            <i />
          </span>
          <span>
            <strong className="app-topbar__brand">Listing Copilot</strong>
            <span className="app-topbar__descriptor">Seller workspace</span>
          </span>
        </div>
        <strong
          aria-label="Active environment"
          role="status"
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
