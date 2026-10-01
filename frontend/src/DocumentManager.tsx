import { useEffect, useState } from "react";

import { listDocuments, retryDocument, type DocumentRecord, uploadDocument } from "./api";

export function DocumentManager() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selectedFile, setSelectedFile] = useState<File>();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string>();

  const refresh = () => listDocuments().then(setDocuments).catch((error: Error) => setMessage(error.message));

  useEffect(() => { void refresh(); }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!selectedFile) {
      setMessage("Choose a PDF or Markdown file first.");
      return;
    }
    setBusy(true);
    setMessage(undefined);
    try {
      await uploadDocument(selectedFile);
      setSelectedFile(undefined);
      form.reset();
      setMessage("Document uploaded and queued for processing.");
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleRetry(documentId: string) {
    setBusy(true);
    setMessage(undefined);
    try {
      await retryDocument(documentId);
      setMessage("Document queued for reprocessing.");
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Retry failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="document-panel">
      <div>
        <p className="eyebrow">ADMIN LIBRARY</p>
        <h2>Policy documents</h2>
        <p className="panel-copy">Upload a policy source and track it as it moves through indexing.</p>
      </div>
      <form className="upload-form" onSubmit={handleSubmit}>
        <input accept=".pdf,.md,.markdown,application/pdf,text/markdown" onChange={(event) => setSelectedFile(event.target.files?.[0])} type="file" />
        <button className="primary-action" disabled={busy} type="submit">{busy ? "Uploading..." : "Upload document"}</button>
      </form>
      {message && <p className="hint">{message}</p>}
      <div className="document-list">
        {documents.length === 0 ? <p className="hint">No documents uploaded yet.</p> : documents.map((document) => (
          <div className="document-row" key={document.id}>
            <strong>{document.filename}</strong>
            <span>{document.status}</span>
            {(document.status === "uploaded" || document.status === "failed") && (
              <button className="row-action" disabled={busy} onClick={() => void handleRetry(document.id)} type="button">Retry</button>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
