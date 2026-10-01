import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";

function App() {
  return (
    <main className="shell">
      <p className="eyebrow">TEAM POLICY ASSISTANT</p>
      <h1>Ask what your policy actually says.</h1>
      <p className="intro">
        The workspace is ready. Authentication, document ingestion, and grounded answers will be
        added in the next roadmap slices.
      </p>
      <div className="status">Backend foundation: ready for local development</div>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
