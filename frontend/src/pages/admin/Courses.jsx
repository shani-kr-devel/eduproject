import { useState } from "react";
import Layout from "../../components/Layout";
import { Card, Loading } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";
import api from "../../api/axiosClient";

const CATEGORIES = ["math", "science", "language", "programming", "test_prep", "other"];
const emptyCourse = { title: "", description: "", category: "other", price: "", teacher_ids: [] };
const emptyContent = { course: "", title: "", content_type: "video", external_url: "", file: null, order: 0 };
const emptyQuestion = { content: "", prompt: "", options: "", correct_answer: "", points: 1, order: 0 };

export default function AdminCourses() {
  const { data: courses, loading, reload } = useApiData("/courses/courses/");
  const { data: teachers } = useApiData("/accounts/teachers/");
  const [course, setCourse] = useState(emptyCourse);
  const [content, setContent] = useState(emptyContent);
  const [question, setQuestion] = useState(emptyQuestion);
  const [questionFile, setQuestionFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("success");
  const quizContents = (courses || []).flatMap((item) => (item.contents || []).filter((contentItem) => contentItem.content_type === "quiz"));

  async function createCourse(event) {
    event.preventDefault();
    setBusy(true);
    try {
      await api.post("/courses/courses/", course);
      setCourse(emptyCourse);
      reload();
      setMessage("Course created.");
    } finally {
      setBusy(false);
    }
  }

  async function createContent(event) {
    event.preventDefault();
    const payload = new FormData();
    Object.entries(content).forEach(([key, value]) => {
      if (value !== null && value !== "") payload.append(key, value);
    });
    await api.post("/courses/course-content/", payload);
    setContent(emptyContent);
    reload();
    setMessage("Course lesson saved.");
  }

  async function createQuestion(event) {
    event.preventDefault();
    await api.post("/courses/quiz-questions/", {
      ...question,
      options: question.options.split(",").map((option) => option.trim()).filter(Boolean),
    });
    setQuestion(emptyQuestion);
    reload();
    setMessage("Question added.");
  }

  async function importQuestions(event) {
    event.preventDefault();
    if (!questionFile || !question.content) return;
    const payload = new FormData();
    payload.append("file", questionFile);
    await api.post(`/courses/course-content/${question.content}/import-questions/`, payload);
    setQuestionFile(null);
    event.target.reset();
    reload();
    setMessage("Question file imported.");
  }

  async function togglePublish(item) {
    await api.post(`/courses/courses/${item.id}/${item.is_published ? "unpublish" : "publish"}/`);
    reload();
  }

  async function remove(item) {
    if (!confirm(`Delete "${item.title}"?`)) return;
    try {
      await api.delete(`/courses/courses/${item.id}/`);
      reload();
      setMessageType("success");
      setMessage("Course deleted.");
    } catch (error) {
      const detail = error.response?.data?.detail;
      setMessageType("error");
      setMessage(typeof detail === "string" ? detail : "The course could not be deleted.");
    }
  }

  return (
    <Layout title="Courses">
      {message && <p className={messageType === "error" ? "error-text" : "success-text"}>{message}</p>}
      <Card title="Create a course">
        <form onSubmit={createCourse} className="grid grid-2">
          <input placeholder="Course title" value={course.title} onChange={(e) => setCourse((f) => ({ ...f, title: e.target.value }))} required />
          <input type="number" step="0.01" placeholder="Price (₹)" value={course.price} onChange={(e) => setCourse((f) => ({ ...f, price: e.target.value }))} required />
          <select value={course.category} onChange={(e) => setCourse((f) => ({ ...f, category: e.target.value }))}>
            {CATEGORIES.map((category) => <option key={category} value={category}>{category}</option>)}
          </select>
          <select multiple value={course.teacher_ids.map(String)} onChange={(e) => setCourse((f) => ({
            ...f, teacher_ids: Array.from(e.target.selectedOptions, (option) => Number(option.value)),
          }))} required>
            {(teachers || []).map((teacher) => <option key={teacher.id} value={teacher.id}>{teacher.user.first_name} {teacher.user.last_name}</option>)}
          </select>
          <textarea style={{ gridColumn: "1 / -1" }} rows={2} placeholder="Description" value={course.description} onChange={(e) => setCourse((f) => ({ ...f, description: e.target.value }))} />
          <button className="btn btn-primary" disabled={busy}>Create course</button>
        </form>
      </Card>

      <Card title="Add video, PDF, article, or quiz">
        <form onSubmit={createContent} className="grid grid-3">
          <select value={content.course} onChange={(e) => setContent((f) => ({ ...f, course: e.target.value }))} required>
            <option value="">Select course</option>
            {(courses || []).map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
          </select>
          <input placeholder="Lesson title" value={content.title} onChange={(e) => setContent((f) => ({ ...f, title: e.target.value }))} required />
          <select value={content.content_type} onChange={(e) => setContent((f) => ({ ...f, content_type: e.target.value }))}>
            <option value="video">Video</option><option value="quiz">Quiz</option><option value="pdf">PDF</option><option value="article">Article</option>
          </select>
          <input type="url" placeholder="External video/article URL (optional)" value={content.external_url} onChange={(e) => setContent((f) => ({ ...f, external_url: e.target.value }))} />
          <input type="file" accept={content.content_type === "video" ? "video/*" : content.content_type === "pdf" ? "application/pdf" : "*/*"} onChange={(e) => setContent((f) => ({ ...f, file: e.target.files[0] || null }))} />
          <button className="btn btn-primary">Save content</button>
        </form>
      </Card>

      <Card title="Add course Q&A">
        <form onSubmit={createQuestion} className="grid grid-3">
          <select value={question.content} onChange={(e) => setQuestion((f) => ({ ...f, content: e.target.value }))} required>
            <option value="">Select quiz lesson</option>
            {quizContents.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
          </select>
          <input placeholder="Question" value={question.prompt} onChange={(e) => setQuestion((f) => ({ ...f, prompt: e.target.value }))} required />
          <input placeholder="Options separated by commas" value={question.options} onChange={(e) => setQuestion((f) => ({ ...f, options: e.target.value }))} required />
          <input placeholder="Correct option" value={question.correct_answer} onChange={(e) => setQuestion((f) => ({ ...f, correct_answer: e.target.value }))} required />
          <button className="btn btn-primary">Add question</button>
        </form>
        <form onSubmit={importQuestions} className="grid grid-2" style={{ marginTop: 12 }}>
          <input type="file" accept=".csv,.json,application/json,text/csv" onChange={(e) => setQuestionFile(e.target.files[0] || null)} required />
          <button className="btn btn-outline">Import question file</button>
        </form>
        <p style={{ color: "#64748b", fontSize: "0.8rem" }}>
          CSV columns: prompt, options (separate options with |), correct_answer, points, order. JSON uses the same field names.
        </p>
      </Card>

      {loading ? <Loading /> : <div className="grid grid-3">
        {(courses || []).map((item) => (
          <Card key={item.id} title={item.title}>
            <p style={{ color: "#64748b", fontSize: "0.85rem" }}>{item.description}</p>
            <p><strong>₹{item.price}</strong> · {item.category} · {(item.contents || []).length} content item(s)</p>
            <span className={`pill ${item.is_published ? "pill-blue" : "pill-slate"}`}>{item.is_published ? "Published" : "Draft"}</span>
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <button className="btn btn-outline btn-sm" onClick={() => togglePublish(item)}>{item.is_published ? "Unpublish" : "Publish"}</button>
              <button className="btn btn-outline btn-sm" onClick={() => remove(item)}>Delete</button>
            </div>
          </Card>
        ))}
      </div>}
    </Layout>
  );
}
