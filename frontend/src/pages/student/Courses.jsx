import { useState } from "react";
import Layout from "../../components/Layout";
import { Card, Loading, Empty } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";
import api from "../../api/axiosClient";

export default function StudentCourses() {
  const { data: enrollments, loading } = useApiData("/courses/enrollments/");
  const { data: assignments, loading: assignmentsLoading } = useApiData("/courses/assignments/");
  const [open, setOpen] = useState(null);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState({});
  const [completed, setCompleted] = useState({});

  async function completeLesson(content) {
    await api.post(`/courses/course-content/${content.id}/complete/`);
    setCompleted((current) => ({ ...current, [content.id]: true }));
  }

  const courses = [
    ...(enrollments || []).map((item) => item.course),
    ...(assignments || []).map((item) => item.course),
  ].filter((course, index, all) => all.findIndex((candidate) => candidate.id === course.id) === index);

  async function submitQuiz(event, content) {
    event.preventDefault();
    const response = await api.post("/courses/quiz-attempts/", {
      content: content.id,
      answers: answers[content.id] || {},
    });
    setSubmitted((current) => ({ ...current, [content.id]: response.data }));
  }

  return (
    <Layout title="My Courses">
      {loading || assignmentsLoading ? <Loading /> : courses.length === 0 ? (
        <Empty>You have no courses yet.</Empty>
      ) : (
        <div className="grid grid-2">
          {courses.map((course) => (
            <Card key={course.id} title={course.title}>
              <p style={{ color: "#64748b" }}>{course.description}</p>
              <button className="btn btn-outline btn-sm" onClick={() => setOpen(open === course.id ? null : course.id)}>
                {open === course.id ? "Hide contents" : "View contents"}
              </button>
              {open === course.id && (
                <div style={{ marginTop: 12 }}>
                  {(course.contents || []).length === 0 && <p>No content uploaded yet.</p>}
                  {(course.contents || []).map((content) => (
                    <div key={content.id} style={{ marginBottom: 16 }}>
                      <strong>{content.title} {((content.is_completed || completed[content.id])) && <span className="pill pill-blue">Done</span>}</strong>
                      {content.content_type === "video" && (content.file || content.external_url) && (
                        <video
                          controls
                          width="100%"
                          style={{ display: "block", marginTop: 8 }}
                          src={content.file || content.external_url}
                          onEnded={() => completeLesson(content)}
                        />
                      )}
                      {content.content_type === "video" && content.file && (
                        <a
                          href={content.file}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-outline btn-sm"
                          style={{ display: "inline-block", marginTop: 8 }}
                        >
                          Open video in a new tab
                        </a>
                      )}
                      {content.content_type === "pdf" && content.file && (
                        <a
                          href={content.file}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-outline btn-sm"
                          style={{ display: "inline-block", marginTop: 8 }}
                        >
                          Open PDF lesson
                        </a>
                      )}
                      {content.content_type === "article" && content.external_url && (
                        <a
                          href={content.external_url}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-outline btn-sm"
                          style={{ display: "inline-block", marginTop: 8 }}
                        >
                          Read lesson
                        </a>
                      )}
                      {content.content_type === "quiz" && (
                        <form onSubmit={(event) => submitQuiz(event, content)} style={{ marginTop: 8 }}>
                          {(content.questions || []).map((question) => (
                            <div key={question.id} className="form-field">
                              <label>{question.prompt}</label>
                              {question.question_type === "multiple_choice" ? (
                                <select required onChange={(event) => setAnswers((current) => ({
                                  ...current,
                                  [content.id]: { ...(current[content.id] || {}), [question.id]: event.target.value },
                                }))}>
                                  <option value="">Choose an answer</option>
                                  {(question.options || []).map((option) => <option key={option} value={option}>{option}</option>)}
                                </select>
                              ) : (
                                <input required onChange={(event) => setAnswers((current) => ({
                                  ...current,
                                  [content.id]: { ...(current[content.id] || {}), [question.id]: event.target.value },
                                }))} />
                              )}
                            </div>
                          ))}
                          <button className="btn btn-primary btn-sm">Submit quiz</button>
                          {submitted[content.id] && <span> Score: {submitted[content.id].score}/{submitted[content.id].max_score}</span>}
                        </form>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </Layout>
  );
}
