import { AppRouter } from "./router";

export type Environment = "sandbox" | "production";

export function App({ environment }: { environment: Environment }) {
  return (
    <>
      <header>
        <strong>{environment === "sandbox" ? "Sandbox" : "Production"}</strong>
      </header>
      <AppRouter />
    </>
  );
}
