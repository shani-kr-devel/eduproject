import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/Layout";
import { Card, Empty, Loading, Pill, StatCard } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";

export default function TeacherDashboard() {
  const { data: students, loading: sLoading } = useApiData("/accounts/students/");
  const { data: tests, loading: tLoading } = useApiData("/academics/tests/");
  const { data: homework, loading: hLoading } = useApiData("/academics/homework/");
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const { data: report, loading: reportLoading } = useApiData(
    selectedId ? `/academics/performance/${selectedId}/` : null,
    { enabled: Boolean(selectedId) }
  );

  const filteredStudents = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return students || [];
    return (students || []).filter((student) => {
      const name = `${student.user.first_name} ${student.user.last_name}`.toLowerCase();
      return [name, student.student_id, student.user.email, student.grade_level].some((value) =>
        String(value || "").toLowerCase().includes(query)
      );
    });
  }, [search, students]);

  const selectedStudent = (students || []).find((student) => student.id === Number(selectedId));
  const submittedHomework = (homework || []).filter((item) => item.status === "submitted");
  const isLoading = sLoading || tLoading || hLoading;
  const formatDate = (value) => (value ? new Date(value).toLocaleDateString() : "-");

  return (
    <Layout title="Teacher Dashboard">
      {isLoading ? (
        <Loading />
      ) : (
        <>
          <div className="grid grid-3">
            <StatCard label="My Students" value={(students || []).length} />
            <StatCard label="Tests created" value={(tests || []).length} />
            <StatCard label="Homework to check" value={submittedHomework.length} />
          </div>

          <div className="teacher-dashboard-grid">
            <Card title="Find a student">
              <div className="form-field">
                <label htmlFor="student-search">Search by name, ID, email, or grade</label>
                <input
                  id="student-search"
                  type="search"
                  placeholder="Start typing..."
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </div>
              <div className="student-search-results">
                {filteredStudents.length === 0 ? <Empty>No matching students.</Empty> : filteredStudents.map((student) => (
                  <button
                    className={`student-search-result ${selectedId === student.id ? "selected" : ""}`}
                    key={student.id}
                    onClick={() => setSelectedId(student.id)}
                    type="button"
                  >
                    <span>
                      <strong>{student.user.first_name} {student.user.last_name}</strong>
                      <small>{student.student_id} · Grade {student.grade_level || "-"}</small>
                    </span>
                    <span aria-hidden="true">&gt;</span>
                  </button>
                ))}
              </div>
            </Card>

            <Card title="Daily tasks">
              <div className="dashboard-task-list">
                <Link className="dashboard-task" to="/teacher/homework">
                  <span className="dashboard-task-icon">{submittedHomework.length}</span>
                  <span className="dashboard-task-copy">
                    <strong>Check submitted homework</strong>
                    <span>{submittedHomework.length ? "Submissions are waiting for review" : "No submissions waiting"}</span>
                  </span>
                  <span className="dashboard-task-arrow">&gt;</span>
                </Link>
                <Link className="dashboard-task" to="/teacher/tests">
                  <span className="dashboard-task-icon">+</span>
                  <span className="dashboard-task-copy">
                    <strong>Create a test for students</strong>
                    <span>Build questions and assign a test to a group</span>
                  </span>
                  <span className="dashboard-task-arrow">&gt;</span>
                </Link>
              </div>
              {submittedHomework.length > 0 && (
                <div className="dashboard-pending-list">
                  {submittedHomework.slice(0, 5).map((item) => (
                    <div className="dashboard-pending-item" key={item.id}>
                      <span><strong>{item.student_name}</strong><small>{item.title} · Submitted {formatDate(item.submitted_at)}</small></span>
                      <Pill tone="blue">Review</Pill>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {selectedId && (
            <Card title={selectedStudent ? `${selectedStudent.user.first_name} ${selectedStudent.user.last_name} - Full report` : "Student report"}>
              {reportLoading || !report ? <Loading /> : (
                <>
                  <div className="student-detail-grid">
                    <div><span className="dashboard-section-note">Student ID</span><strong>{report.student.student_id}</strong></div>
                    <div><span className="dashboard-section-note">Email</span><strong>{report.student.user.email || "-"}</strong></div>
                    <div><span className="dashboard-section-note">Grade</span><strong>{report.student.grade_level || "-"}</strong></div>
                    <div><span className="dashboard-section-note">Teachers</span><strong>{(report.student.teacher_names || []).join(", ") || "-"}</strong></div>
                  </div>
                  <div className="grid grid-2" style={{ marginTop: 16 }}>
                    <StatCard label="Average test score" value={report.average_test_score_pct == null ? "-" : `${report.average_test_score_pct}%`} />
                    <StatCard label="Tests taken" value={report.tests_taken} />
                  </div>
                  <div className="teacher-report-sections">
                    <div>
                      <h4>Test history</h4>
                      {report.test_reports.length === 0 ? <p>No completed tests.</p> : report.test_reports.map((item) => (
                        <div className="teacher-report-row" key={item.id}>
                          <span><strong>{item.title}</strong><small>{item.subject} · {formatDate(item.date)}</small></span>
                          <strong>{item.percentage}%</strong>
                        </div>
                      ))}
                    </div>
                    <div>
                      <h4>Course progress</h4>
                      {report.course_reports.length === 0 ? <p>No course activity.</p> : report.course_reports.map((course) => (
                        <div className="teacher-report-row" key={course.course_id}>
                          <span><strong>{course.title}</strong><small>{course.completed_lessons}/{course.total_lessons} lessons · {course.quizzes_attempted}/{course.quizzes} quizzes</small></span>
                          <strong>{course.completion_pct}%</strong>
                        </div>
                      ))}
                    </div>
                  </div>
                  <h4>Recent feedback</h4>
                  {report.recent_feedback.length === 0 ? <p>No feedback yet.</p> : report.recent_feedback.map((feedback) => (
                    <div className="feedback-row" key={feedback.id}><strong>{feedback.author_name}</strong><span>{feedback.message}</span></div>
                  ))}
                </>
              )}
            </Card>
          )}
        </>
      )}
    </Layout>
  );
}
