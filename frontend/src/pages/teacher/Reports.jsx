import { useState } from "react";
import Layout from "../../components/Layout";
import { Card, Loading, Empty, StatCard } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";

export default function TeacherReports() {
  const { data: students, loading } = useApiData("/accounts/students/");
  const [selected, setSelected] = useState(null);
  const { data: report, loading: reportLoading } = useApiData(
    selected ? `/academics/performance/${selected}/` : null,
    { enabled: !!selected }
  );

  return (
    <Layout title="Student Reports">
      {loading ? (
        <Loading />
      ) : (students || []).length === 0 ? (
        <Empty>No students assigned yet.</Empty>
      ) : (
        <>
          <div className="form-field" style={{ maxWidth: 320 }}>
            <label>Choose a student</label>
            <select value={selected || ""} onChange={(e) => setSelected(e.target.value)}>
              <option value="">Select…</option>
              {students.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.user.first_name} {s.user.last_name} ({s.student_id})
                </option>
              ))}
            </select>
          </div>

          {selected && (reportLoading || !report ? (
            <Loading />
          ) : (
            <>
              <div className="grid grid-2">
                <StatCard
                  label="Average test score"
                  value={report.average_test_score_pct != null ? `${report.average_test_score_pct}%` : "—"}
                />
                <StatCard label="Tests taken" value={report.tests_taken} />
              </div>
            <Card title="Test report" style={{ marginTop: 16 }}>
              {(report.test_reports || []).length === 0 ? <p>No completed tests yet.</p> : (
                <table className="table">
                  <thead><tr><th>Test</th><th>Score</th><th>Time</th><th>Answers</th></tr></thead>
                  <tbody>{report.test_reports.map((test) => (
                    <tr key={test.id}>
                      <td>{test.title}<br /><small>{test.subject}</small></td>
                      <td>{test.score}/{test.max_score} ({test.percentage}%)</td>
                      <td>{test.duration_seconds}s</td>
                      <td>{(test.answers || []).map((answer) => `${answer.is_correct ? "✓" : "✗"} ${answer.answer || "—"}`).join(", ")}</td>
                    </tr>
                  ))}</tbody>
                </table>
              )}
            </Card>
              <Card title="Course report" style={{ marginTop: 16 }}>
              {(report.course_reports || []).length === 0 ? <p>No course activity yet.</p> : (
                <table className="table">
                  <thead><tr><th>Course</th><th>Progress</th><th>Videos</th><th>Quizzes</th><th>Quiz average</th></tr></thead>
                  <tbody>{report.course_reports.map((course) => (
                    <tr key={course.course_id}>
                      <td>{course.title}</td>
                      <td>{course.completion_pct}% ({course.completed_lessons}/{course.total_lessons})</td>
                      <td>{course.completed_video_lessons}/{course.video_lessons} completed</td>
                      <td>{course.quizzes_attempted}/{course.quizzes} attempted</td>
                      <td>{course.average_quiz_score_pct == null ? "—" : `${course.average_quiz_score_pct}%`}</td>
                    </tr>
                  ))}</tbody>
                </table>
              )}
              </Card>
            </>
          ))}
        </>
      )}
    </Layout>
  );
}
