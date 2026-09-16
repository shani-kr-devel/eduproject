import { useState } from "react";
import Layout from "../../components/Layout";
import { Card } from "../../components/ui";
import api from "../../api/axiosClient";

export default function ParentSearchChild() {
  const [studentId, setStudentId] = useState("");
  const [result, setResult] = useState(null);
  const [searchError, setSearchError] = useState("");
  const [linkError, setLinkError] = useState("");
  const [linked, setLinked] = useState(false);
  const [busy, setBusy] = useState(false);

  async function search(e) {
    e.preventDefault();
    setSearchError("");
    setLinkError("");
    setResult(null);
    setLinked(false);
    setBusy(true);
    try {
      const res = await api.get("/accounts/parent/search-child/", { params: { student_id: studentId.trim() } });
      setResult(res.data);
    } catch (err) {
      setSearchError(err.response?.data?.detail || "No student found with that Student ID.");
    } finally {
      setBusy(false);
    }
  }

  async function linkChild() {
    setLinkError("");
    setBusy(true);
    try {
      await api.post("/accounts/parent/link-child/", { student_id: result.student_id });
      setLinked(true);
    } catch (err) {
      const data = err.response?.data;
      const message =
        data?.detail ||
        (Array.isArray(data?.non_field_errors) && data.non_field_errors[0]) ||
        "Could not link this child.";
      setLinkError(message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Layout title="Add a Child">
      <Card title="Search by Student ID">
        <form onSubmit={search} style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
          <div className="form-field" style={{ flex: 1, marginBottom: 0 }}>
            <label>Student ID</label>
            <input
              placeholder="STU-XXXXXXXX"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              required
            />
          </div>
          <button className="btn btn-primary" disabled={busy}>Search</button>
        </form>
        {searchError && <div className="error-text" style={{ marginTop: 10 }}>{searchError}</div>}
      </Card>

      {result && (
        <Card title="Student found">
          <p>
            <strong>{result.user.first_name} {result.user.last_name}</strong> — {result.student_id}
          </p>
          <p style={{ color: "#64748b" }}>Grade level: {result.grade_level || "—"}</p>
          {linked ? (
            <p style={{ color: "#2563EB", fontWeight: 600 }}>Linked to your account ✓</p>
          ) : (
            <>
              <button className="btn btn-primary" disabled={busy} onClick={linkChild}>
                Link this child to my account
              </button>
              <p style={{ color: "#64748b", fontSize: "0.8rem", marginTop: 8 }}>
                Only works if the school has authorized your account for this student.
              </p>
              {linkError && <div className="error-text">{linkError}</div>}
            </>
          )}
        </Card>
      )}
    </Layout>
  );
}
