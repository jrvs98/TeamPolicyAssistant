import { useState } from "react";

import { searchPolicy, type SearchResult } from "./api";

export function PolicySearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
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
      const matches = await searchPolicy(query.trim());
      setResults(matches);
      if (matches.length === 0) setMessage("No indexed policy sections matched that question.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Search failed.");
      setResults([]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="search-panel">
      <p className="eyebrow">POLICY SEARCH</p>
      <h2>Find the source before you decide.</h2>
      <p className="panel-copy">Search indexed policy sections and inspect the source passages returned by retrieval.</p>
      <form className="question-form" onSubmit={handleSubmit}>
        <input
          aria-label="Policy question"
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Ask about remote work, leave, or benefits"
          value={query}
        />
        <button className="primary-action" disabled={busy} type="submit">{busy ? "Searching..." : "Search policy"}</button>
      </form>
      {message && <p className="hint">{message}</p>}
      {results.length > 0 && (
        <div className="search-results">
          {results.map((result, index) => (
            <article className="result-row" key={result.chunk_id}>
              <div className="result-meta">SOURCE {index + 1} · {result.filename}{result.page_number ? ` · PAGE ${result.page_number}` : ""}</div>
              <p>{result.content}</p>
              <small>Match distance: {result.distance.toFixed(4)}</small>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
