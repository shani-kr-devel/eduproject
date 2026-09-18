import { useState } from "react";
import Layout from "../../components/Layout";
import { Card, Empty, Loading, Pill } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";
import api from "../../api/axiosClient";

const initialForm = {
  title: "",
  description: "",
  due_date: "",
  material_type: "text",
  material_text: "",
  material_url: "",
  material_file: null,
};

export default function TeacherHomework() {
  const { data: students, loading: studentsLoading } = useApiData("/accounts/students/");
  const { data: homework, loading: homeworkLoading, reload } = useApiData("/academics/homework/");
  const [form, setForm] = useState(initialForm);
  const [selectedStudents, setSelectedStudents] = useState([]);
  const [assignAll, setAssignAll] = useState(true);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function createHomework(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    const payload = new FormData();
    Object.entries(form).forEach(([key, value]) => {
      if (value) payload.append(key, value);
    });
    const recipients = assignAll ? (students || []).map((student) => student.id) : selectedStudents;
    recipients.forEach((studentId) => payload.append("student_ids", studentId));
    try {
      await api.post("/academics/homework/", payload);
      setForm(initialForm);
      setSelectedStudents([]);
      setAssignAll(true);
      setMessage(`Homework sent to ${recipients.length} student${recipients.length === 1 ? "" : "s"}.`);
      reload();
    } catch (error) {
      setMessage(error.response?.data?.detail || "Could not send homework.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Layout title="Homework">
      <Card title="Send homework">
        {studentsLoading ? <Loading /> : (
          <form onSubmit={createHomework} className="homework-form">
            <div className="grid grid-2">
              <div className="form-field">
                <label>Title</label>
                <input value={form.title} onChange={(event) => update("title", event.target.value)} required />
              </div>
              <div className="form-field">
                <label>Due date</label>
                <input type="date" value={form.due_date} onChange={(event) => update("due_date", event.target.value)} required />
              </div>
            </div>
            <div className="form-field">
              <label>Instructions</label>
              <textarea rows="3" value={form.description} onChange={(event) => update("description", event.target.value)} />
            </div>
            <div className="grid grid-2">
              <div className="form-field">
                <label>Homework format</label>
                <select value={form.material_type} onChange={(event) => update("material_type", event.target.value)}>
                  <option value="text">Text</option>
                  <option value="link">Link</option>
                  <option value="image">Image</option>
                  <option value="pdf">PDF</option>
                  <option value="text_file">Text file</option>
                </select>
              </div>
              <div className="form-field">
                <label>Students</label>
                <select value={assignAll ? "all" : "selected"} onChange={(event) => setAssignAll(event.target.value === "all")}>
                  <option value="all">All my students</option>
                  <option value="selected">Choose students</option>
                </select>
              </div>
            </div>
            {!assignAll && (
              <div className="form-field">
                <label>Choose students</label>
                <select multiple value={selectedStudents.map(String)} onChange={(event) => setSelectedStudents(Array.from(event.target.selectedOptions, (option) => option.value))} required>
                  {(students || []).map((student) => (
                    <option key={student.id} value={student.id}>{student.user.first_name} {student.user.last_name} ({student.student_id})</option>
                  ))}
                </select>
              </div>
            )}
            {form.material_type === "text" && (
              <div className="form-field">
                <label>Homework text</label>
                <textarea rows="5" value={form.material_text} onChange={(event) => update("material_text", event.target.value)} required />
              </div>
            )}
            {form.material_type === "link" && (
              <div className="form-field">
                <label>Homework link</label>
                <input type="url" value={form.material_url} onChange={(event) => update("material_url", event.target.value)} required />
              </div>
            )}
            {form.material_type !== "text" && form.material_type !== "link" && (
              <div className="form-field">
                <label>Homework file</label>
                <input type="file" accept={form.material_type === "image" ? "image/*" : form.material_type === "pdf" ? ".pdf,application/pdf" : ".txt,.text,text/plain"} onChange={(event) => update("material_file", event.target.files[0] || null)} required />
              </div>
            )}
            <button className="btn btn-primary" disabled={busy}>{busy ? "Sending..." : "Send homework"}</button>
            {message && <p>{message}</p>}
          </form>
        )}
      </Card>

      <Card title="Sent homework">
        {homeworkLoading ? <Loading /> : (homework || []).length === 0 ? <Empty>No homework sent yet.</Empty> : (
          <div className="homework-list">
            {(homework || []).map((item) => (
              <div className="homework-row" key={item.id}>
                <div><strong>{item.title}</strong><small>{item.student_name} · Due {item.due_date}</small></div>
                <Pill tone={item.status === "submitted" ? "blue" : "slate"}>{item.status}</Pill>
              </div>
            ))}
          </div>
        )}
      </Card>
    </Layout>
  );
}
