import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { useEffect, useState } from "react";

import { getRoles, getUsername, initializeAuthentication, login, logout } from "./auth";
import { DocumentManager } from "./DocumentManager";
import { PolicySearch } from "./PolicySearch";
import "./styles.css";

function App({ authenticated }: { authenticated: boolean }) {
  if (!authenticated) {
    return (
      <main className="shell auth-shell">
        <p className="eyebrow">TEAM POLICY ASSISTANT</p>
        <h1>Policy answers with a paper trail.</h1>
        <p className="intro">Sign in to search the team policy library and see the source behind every answer.</p>
        <button className="primary-action" onClick={() => void login()} type="button">
          Sign in
        </button>
        <p className="hint">Local development uses the Keycloak realm configured in Docker Compose.</p>
      </main>
    );
  }

  const roles = getRoles();
  return (
    <main className="shell">
      <header className="topbar">
        <p className="eyebrow">TEAM POLICY ASSISTANT</p>
        <button className="secondary-action" onClick={() => void logout()} type="button">
          Sign out
        </button>
      </header>
      <section className="content">
        <p className="eyebrow">{roles.join(" / ") || "AUTHENTICATED USER"}</p>
        <h1>Ask what your policy actually says.</h1>
        <p className="intro">Welcome, {getUsername() ?? "team member"}. Your protected workspace is ready for policy search.</p>
        <div className="status">Authentication: connected to Keycloak</div>
        <PolicySearch />
        {roles.includes("admin") && <DocumentManager />}
      </section>
    </main>
  );
}

function Root() {
  const [state, setState] = useState<"loading" | "ready" | "signed-out" | "error">("loading");

  useEffect(() => {
    initializeAuthentication()
      .then((authenticated) => setState(authenticated ? "ready" : "signed-out"))
      .catch(() => setState("error"));
  }, []);

  if (state === "loading") return <main className="shell"><p className="eyebrow">CONNECTING TO KEYCLOAK</p></main>;
  if (state === "error") return <main className="shell"><p className="eyebrow">AUTHENTICATION UNAVAILABLE</p><h1>Keycloak is not reachable.</h1><p className="intro">Start Docker Compose and reload this page.</p></main>;
  return <App authenticated={state === "ready"} />;
}

createRoot(document.getElementById("root")!).render(<StrictMode><Root /></StrictMode>);
