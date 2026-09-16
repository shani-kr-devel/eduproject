import { useState } from "react";
import Layout from "../../components/Layout";
import { Card, Loading, Empty, StatCard } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";

export default function ParentReports() {
  const { data: profile, loading } = useApiData("/accounts/parents/");
  const me = profile?.[0];
  const [selected, setSelected] = useState(null);
  const { data: report, loading: reportLoading } = useApiData(
    selected ? `/academics/performance/${selected}/` : null,
    { enabled: !!selected }
  );

  return (
    <Layout title="Performance Reports">
      {loading ? (
        <Loading />
      ) : (me?.children || []).length === 0 ? (
        <Empty>No children linked yet.</Empty>
      ) : (
        <>
          <div className="form-field" style={{ maxWidth: 320 }}>
            <label>Choose a child</label>
            <select value={selected || ""} onChange={(e) => setSelected(e.target.value)}>
              <option value="">Select…</option>
              {me.children.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.user.first_name} {c.user.last_name} ({c.student_id})
                </option>
              ))}
            </select>
          </div>

          {selected && (reportLoading || !report ? (
            <Loading />
          ) : (
            <>
              <div className="grid grid-3">
                <StatCard
                  label="Average test score"
                  value={report.average_test_score_pct != null ? `${report.average_test_score_pct}%` : "—"}
                />
                <StatCard label="Tests taken" value={report.tests_taken} />
              </div>
              <Card title="Feedback">
                {(report.recent_feedback || []).map((f) => (
                  <div key={f.id} style={{ padding: "8px 0", borderBottom: "1px solid #f1f5f9" }}>
                    <strong>{f.author_name}</strong>
                    <p style={{ margin: "4px 0 0 0" }}>{f.message}</p>
                  </div>
                ))}
                {(report.recent_feedback || []).length === 0 && <p>No feedback yet.</p>}
              </Card>
              <Card title="Test report">
                {(report.test_reports || []).length === 0 ? <p>No completed tests yet.</p> : (
                  <table className="table">
                    <thead><tr><th>Test</th><th>Score</th><th>Time</th><th>Submitted</th></tr></thead>
                    <tbody>{report.test_reports.map((test) => (
                      <tr key={test.id}>
                        <td>{test.title}<br /><small>{test.subject}</small></td>
                        <td>{test.score}/{test.max_score} ({test.percentage}%)</td>
                        <td>{test.duration_seconds}s</td>
                        <td>{new Date(test.submitted_at).toLocaleString()}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                )}
              </Card>
              <Card title="Course report">
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
