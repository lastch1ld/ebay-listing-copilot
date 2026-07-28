export type Environment = "sandbox" | "production";

export function App({ environment }: { environment: Environment }) {
  return (
    <main>
      <strong>{environment === "sandbox" ? "Sandbox" : "Production"}</strong>
    </main>
  );
}
