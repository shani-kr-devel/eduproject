import { useState } from "react";
import Layout from "../../components/Layout";
import { Card, Loading } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";
import api from "../../api/axiosClient";

export default function TeacherStudents() {
  const { data: students, loading } = useApiData("/accounts/students/");
  const [feedbackDraft, setFeedbackDraft] = useState({});
  const [busyId, setBusyId] = useState(null);
  const [sentId, setSentId] = useState(null);

  async function sendFeedback(student) {
    setBusyId(student.id);
    try {
      await api.post("/academics/feedback/", {
        student: student.id,
        message: feedbackDraft[student.id],
      });
      setFeedbackDraft((d) => ({ ...d, [student.id]: "" }));
      setSentId(student.id);
      setTimeout(() => setSentId(null), 2000);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <Layout title="My Students">
      {loading ? (
        <Loading />
      ) : (
        <div className="grid grid-2">
          {(students || []).map((s) => (
            <Card key={s.id} title={`${s.user.first_name} ${s.user.last_name}`}>
              <p style={{ fontSize: "0.85rem", color: "#64748b" }}>
                {s.student_id} · Grade {s.grade_level || "—"}
              </p>
              <div className="form-field">
                <label>Send feedback</label>
                <textarea
                  rows={2}
                  value={feedbackDraft[s.id] || ""}
                  onChange={(e) => setFeedbackDraft((d) => ({ ...d, [s.id]: e.target.value }))}
                />
              </div>
              <button
                className="btn btn-primary btn-sm"
                disabled={busyId === s.id || !feedbackDraft[s.id]}
                onClick={() => sendFeedback(s)}
              >
                {sentId === s.id ? "Sent ✓" : "Send"}
              </button>
            </Card>
          ))}
        </div>
      )}
    </Layout>
  );
}
