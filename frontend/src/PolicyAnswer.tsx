import { useState } from "react";

import { askPolicy, type AnswerResponse } from "./api";

export function PolicyAnswer() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<AnswerResponse>();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string>();

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!query.trim()) {
      setMessage("Enter a policy question first.");
      return;
    }
    setBusy(true);
    setMessage(undefined);
    try {
      setResult(await askPolicy(query.trim()));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Question failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="answer-panel">
      <p className="eyebrow">GROUNDED ANSWER</p>
      <h2>Ask the policy library.</h2>
      <form className="question-form" onSubmit={handleSubmit}>
        <input aria-label="Policy question" onChange={(event) => setQuery(event.target.value)} placeholder="Can I work remotely?" value={query} />
        <button className="primary-action" disabled={busy} type="submit">{busy ? "Checking..." : "Ask policy"}</button>
      </form>
      {message && <p className="hint">{message}</p>}
      {result && <>
        <p className="answer-copy">{result.answer}</p>
        <div className="answer-citations">
          {result.citations.map((citation, index) => <div className="citation-row" key={citation.chunk_id}>[{index + 1}] {citation.filename}{citation.page_number ? `, page ${citation.page_number}` : ""}</div>)}
        </div>
      </>}
    </section>
  );
}
