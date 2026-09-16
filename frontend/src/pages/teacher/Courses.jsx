import { useState } from "react";
import Layout from "../../components/Layout";
import { Card, Empty, Loading } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";
import api from "../../api/axiosClient";

const blankContent = { course: "", title: "", content_type: "video", external_url: "", order: 0 };
const blankQuestion = { content: "", prompt: "", question_type: "multiple_choice", options: "", correct_answer: "", points: 1 };

export default function TeacherCourses() {
  const { data: courses, loading, reload } = useApiData("/courses/courses/");
  const { data: students } = useApiData("/accounts/students/");
  const [content, setContent] = useState(blankContent);
  const [question, setQuestion] = useState(blankQuestion);
  const [assignment, setAssignment] = useState({ course_id: "", student: "" });
  const [message, setMessage] = useState("");

  async function addContent(e) {
    e.preventDefault();
    await api.post("/courses/course-content/", content);
    setContent(blankContent);
    reload();
    setMessage("Lesson saved.");
  }

  async function addQuestion(e) {
    e.preventDefault();
    await api.post("/courses/quiz-questions/", {
      ...question,
      options: question.options.split(",").map((option) => option.trim()).filter(Boolean),
    });
    setQuestion(blankQuestion);
    reload();
    setMessage("Question saved.");
  }

  async function assignCourse(e) {
    e.preventDefault();
    await api.post("/courses/assignments/", assignment);
    setAssignment({ course_id: "", student: "" });
    setMessage("Course assigned.");
  }

  return (
    <Layout title="My Courses">
      {message && <p className="success-text">{message}</p>}
      <Card title="Add video or end-of-video quiz">
        <form onSubmit={addContent} className="grid grid-3">
          <select value={content.course} onChange={(e) => setContent((f) => ({ ...f, course: e.target.value }))} required>
            <option value="">Select course</option>
            {(courses || []).map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}
          </select>
          <input placeholder="Lesson title" value={content.title} onChange={(e) => setContent((f) => ({ ...f, title: e.target.value }))} required />
          <select value={content.content_type} onChange={(e) => setContent((f) => ({ ...f, content_type: e.target.value }))}>
            <option value="video">Video</option>
            <option value="quiz">End-of-video quiz</option>
          </select>
          <input placeholder="Video URL" value={content.external_url} onChange={(e) => setContent((f) => ({ ...f, external_url: e.target.value }))} />
          <button className="btn btn-primary">Save lesson</button>
        </form>
      </Card>

      <Card title="Design a quiz question">
        <form onSubmit={addQuestion} className="grid grid-3">
          <select value={question.content} onChange={(e) => setQuestion((f) => ({ ...f, content: e.target.value }))} required>
            <option value="">Select quiz</option>
            {(courses || []).flatMap((course) => (course.contents || []).filter((item) => item.content_type === "quiz").map((item) => (
              <option key={item.id} value={item.id}>{course.title} - {item.title}</option>
            )))}
          </select>
          <input placeholder="Question" value={question.prompt} onChange={(e) => setQuestion((f) => ({ ...f, prompt: e.target.value }))} required />
          <select value={question.question_type} onChange={(e) => setQuestion((f) => ({ ...f, question_type: e.target.value }))}>
            <option value="multiple_choice">Multiple choice</option>
            <option value="short_answer">Short answer</option>
          </select>
          {question.question_type === "multiple_choice" && (
            <input placeholder="Options separated by commas" value={question.options} onChange={(e) => setQuestion((f) => ({ ...f, options: e.target.value }))} required />
          )}
          <input placeholder="Correct answer" value={question.correct_answer} onChange={(e) => setQuestion((f) => ({ ...f, correct_answer: e.target.value }))} required />
          <button className="btn btn-primary">Save question</button>
        </form>
      </Card>

      <Card title="Assign a course to a student">
        <form onSubmit={assignCourse} className="grid grid-3">
          <select value={assignment.course_id} onChange={(e) => setAssignment((f) => ({ ...f, course_id: e.target.value }))} required>
            <option value="">Select course</option>
            {(courses || []).map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}
          </select>
          <select value={assignment.student} onChange={(e) => setAssignment((f) => ({ ...f, student: e.target.value }))} required>
            <option value="">Select student</option>
            {(students || []).map((student) => <option key={student.id} value={student.id}>{student.user.first_name} {student.user.last_name}</option>)}
          </select>
          <button className="btn btn-primary">Assign course</button>
        </form>
      </Card>

      {loading ? <Loading /> : (courses || []).length === 0 ? <Empty>No courses have been assigned to you.</Empty> : (
        <div className="grid grid-2">
          {(courses || []).map((course) => <Card key={course.id} title={course.title}>
            <p>{course.description}</p>
            <p>{(course.contents || []).length} lesson(s), including videos and quizzes.</p>
          </Card>)}
        </div>
      )}
    </Layout>
  );
}
