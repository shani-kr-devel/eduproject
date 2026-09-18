import { useState } from "react";
import Layout from "../../components/Layout";
import { Card, Empty, Loading, Pill } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";
import api from "../../api/axiosClient";

const mediaUrl = (url) => (url?.startsWith("http") ? url : `${window.location.origin}${url}`);

export default function StudentHomework() {
  const { data: homework, loading, reload } = useApiData("/academics/homework/");
  const [drafts, setDrafts] = useState({});
  const [busy, setBusy] = useState(null);
  const [message, setMessage] = useState("");

  function updateDraft(id, field, value) {
    setDrafts((current) => ({ ...current, [id]: { ...(current[id] || {}), [field]: value } }));
  }

  async function submitHomework(event, item) {
    event.preventDefault();
    const draft = drafts[item.id] || {};
    const payload = new FormData();
    if (draft.submission_text) payload.append("submission_text", draft.submission_text);
    if (draft.submission_file) payload.append("submission_file", draft.submission_file);
    setBusy(item.id);
    setMessage("");
    try {
      await api.post(`/academics/homework/${item.id}/submit/`, payload);
      setMessage("Homework submitted successfully.");
      reload();
    } catch (error) {
      setMessage(error.response?.data?.detail || "Could not submit homework.");
    } finally {
      setBusy(null);
    }
  }

  function renderMaterial(item) {
    if (item.material_type === "text") return <p className="homework-material-text">{item.material_text}</p>;
    if (item.material_type === "link") return <a href={item.material_url} target="_blank" rel="noreferrer">Open homework link</a>;
    if (item.material_file) return <a href={mediaUrl(item.material_file)} target="_blank" rel="noreferrer">Open {item.material_type.replace("_", " ")}</a>;
    return null;
  }

  return (
    <Layout title="Homework">
      {message && <div className="card homework-message">{message}</div>}
      {loading ? <Loading /> : (homework || []).length === 0 ? <Empty>No homework assigned yet.</Empty> : (
        <div className="homework-list">
          {(homework || []).map((item) => {
            const submitted = item.status === "submitted";
            const draft = drafts[item.id] || {};
            return (
              <Card key={item.id} title={item.title} actions={<Pill tone={submitted ? "blue" : "slate"}>{submitted ? "Submitted" : `Due ${item.due_date}`}</Pill>}>
                <p className="homework-meta">From {item.teacher_name} · Due {item.due_date}</p>
                {item.description && <p>{item.description}</p>}
                <div className="homework-material">
                  <strong>Homework material</strong>
                  {renderMaterial(item)}
                </div>
                {submitted ? (
                  <div className="homework-submission">
                    <strong>Your submission</strong>
                    {item.submission_text && <p>{item.submission_text}</p>}
                    {item.submission_file && <a href={mediaUrl(item.submission_file)} target="_blank" rel="noreferrer">Open submitted file</a>}
                  </div>
                ) : (
                  <form onSubmit={(event) => submitHomework(event, item)} className="homework-submit-form">
                    <div className="form-field">
                      <label>Your answer</label>
                      <textarea rows="4" value={draft.submission_text || ""} onChange={(event) => updateDraft(item.id, "submission_text", event.target.value)} placeholder="Write your answer here" />
                    </div>
                    <div className="form-field">
                      <label>Or attach an image, PDF, or text file</label>
                      <input type="file" accept="image/*,.pdf,.txt,.text,application/pdf,text/plain" onChange={(event) => updateDraft(item.id, "submission_file", event.target.files[0] || null)} />
                    </div>
                    <button className="btn btn-primary" disabled={busy === item.id}>{busy === item.id ? "Submitting..." : "Submit homework"}</button>
                  </form>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </Layout>
  );
}
