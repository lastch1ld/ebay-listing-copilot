import { AppRouter } from "./router";

export type Environment = "sandbox" | "production";

export function App({ environment }: { environment: Environment }) {
  return (
    <>
      <header className="app-topbar">
        <span className="app-topbar__brand">eBay Listing Copilot</span>
        <strong className={`env-badge${environment === "production" ? " env-badge--production" : ""}`}>
          {environment === "sandbox" ? "Sandbox" : "Production"}
        </strong>
      </header>
      <AppRouter />
    </>
  );
}
