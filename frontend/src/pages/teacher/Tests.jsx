import { useState } from "react";
import Layout from "../../components/Layout";
import { Card, Loading } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";
import api from "../../api/axiosClient";

const emptyQuestion = { prompt: "", options: "", correct_answer: "", points: 1 };

export default function TeacherTests() {
  const { data: tests, loading, reload } = useApiData("/academics/tests/");
  const { data: students } = useApiData("/accounts/students/");
  const { data: groups, reload: reloadGroups } = useApiData("/academics/student-groups/");
  const { data: attempts } = useApiData("/academics/test-attempts/");
  const [test, setTest] = useState({ title: "", subject: "", date: "", duration_minutes: 30 });
  const [question, setQuestion] = useState(emptyQuestion);
  const [selectedTest, setSelectedTest] = useState("");
  const [group, setGroup] = useState({ name: "", students: [] });
  const [assign, setAssign] = useState({ test: "", group_ids: [] });

  async function createTest(event) {
    event.preventDefault();
    await api.post("/academics/tests/", { ...test, max_score: 100 });
    setTest({ title: "", subject: "", date: "", duration_minutes: 30 });
    reload();
  }

  async function createQuestion(event) {
    event.preventDefault();
    await api.post("/academics/test-questions/", {
      test: selectedTest,
      prompt: question.prompt,
      question_type: "multiple_choice",
      options: question.options.split(",").map((option) => option.trim()).filter(Boolean),
      correct_answer: question.correct_answer,
      points: question.points,
    });
    setQuestion(emptyQuestion);
    reload();
  }

  async function createGroup(event) {
    event.preventDefault();
    await api.post("/academics/student-groups/", group);
    setGroup({ name: "", students: [] });
    reloadGroups();
  }

  async function assignTest(event) {
    event.preventDefault();
    await api.post(`/academics/tests/${assign.test}/assign/`, { group_ids: assign.group_ids });
    setAssign({ test: "", group_ids: [] });
    reload();
  }

  return (
    <Layout title="Tests">
      <Card title="Create timed MCQ test">
        <form onSubmit={createTest} className="grid grid-3">
          <input placeholder="Test title" value={test.title} onChange={(e) => setTest((f) => ({ ...f, title: e.target.value }))} required />
          <input placeholder="Subject" value={test.subject} onChange={(e) => setTest((f) => ({ ...f, subject: e.target.value }))} required />
          <input type="date" value={test.date} onChange={(e) => setTest((f) => ({ ...f, date: e.target.value }))} required />
          <input type="number" min="1" value={test.duration_minutes} onChange={(e) => setTest((f) => ({ ...f, duration_minutes: e.target.value }))} required />
          <button className="btn btn-primary">Create test</button>
        </form>
      </Card>

      <Card title="Create question">
        <form onSubmit={createQuestion} className="grid grid-3">
          <select value={selectedTest} onChange={(e) => setSelectedTest(e.target.value)} required>
            <option value="">Select test</option>
            {(tests || []).map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
          </select>
          <input placeholder="Question" value={question.prompt} onChange={(e) => setQuestion((f) => ({ ...f, prompt: e.target.value }))} required />
          <input placeholder="Options separated by commas" value={question.options} onChange={(e) => setQuestion((f) => ({ ...f, options: e.target.value }))} required />
          <input placeholder="Correct option" value={question.correct_answer} onChange={(e) => setQuestion((f) => ({ ...f, correct_answer: e.target.value }))} required />
          <input type="number" min="1" value={question.points} onChange={(e) => setQuestion((f) => ({ ...f, points: e.target.value }))} />
          <button className="btn btn-primary">Add MCQ</button>
        </form>
      </Card>

      <Card title="Create student group">
        <form onSubmit={createGroup} className="grid grid-2">
          <input placeholder="Group name (for example Group 1 - 8 students)" value={group.name} onChange={(e) => setGroup((f) => ({ ...f, name: e.target.value }))} required />
          <select multiple value={group.students} onChange={(e) => setGroup((f) => ({ ...f, students: Array.from(e.target.selectedOptions, (option) => Number(option.value)) }))} required>
            {(students || []).map((student) => <option key={student.id} value={student.id}>{student.user.first_name} {student.user.last_name}</option>)}
          </select>
          <button className="btn btn-primary">Save group</button>
        </form>
      </Card>

      <Card title="Assign test to groups">
        <form onSubmit={assignTest} className="grid grid-2">
          <select value={assign.test} onChange={(e) => setAssign((f) => ({ ...f, test: e.target.value }))} required>
            <option value="">Select test</option>
            {(tests || []).map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
          </select>
          <select multiple value={assign.group_ids} onChange={(e) => setAssign((f) => ({ ...f, group_ids: Array.from(e.target.selectedOptions, (option) => Number(option.value)) }))} required>
            {(groups || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
          <button className="btn btn-primary">Assign test</button>
        </form>
      </Card>

      {loading ? <Loading /> : (tests || []).map((item) => (
        <Card key={item.id} title={`${item.title} - ${item.subject}`}>
          <p>{item.duration_minutes} minutes · {item.questions?.length || 0} questions</p>
          <h4>Student results</h4>
          {(attempts || []).filter((attempt) => attempt.test === item.id).map((attempt) => (
            <div key={attempt.id} style={{ padding: "8px 0", borderBottom: "1px solid #f1f5f9" }}>
              <strong>{attempt.student_name}</strong> — {attempt.score}/{attempt.max_score}, {attempt.duration_seconds}s
              <div>{(attempt.answers || []).map((answer) => `${answer.question_prompt}: ${answer.answer || "No answer"}`).join(" | ")}</div>
            </div>
          ))}
        </Card>
      ))}
    </Layout>
  );
}
