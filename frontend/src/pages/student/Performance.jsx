import Layout from "../../components/Layout";
import { Card, Loading, StatCard } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";

export default function StudentPerformance() {
  const { data: mine } = useApiData("/accounts/students/");
  const studentPk = mine?.[0]?.id;
  const { data: report, loading } = useApiData(
    studentPk ? `/academics/performance/${studentPk}/` : null,
    { enabled: !!studentPk }
  );

  return (
    <Layout title="Performance Report">
      {loading || !report ? (
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
          <Card title="Teacher Feedback">
            {(report.recent_feedback || []).length === 0 && <p>No feedback yet.</p>}
            {(report.recent_feedback || []).map((f) => (
              <div key={f.id} style={{ padding: "10px 0", borderBottom: "1px solid #f1f5f9" }}>
                <strong>{f.author_name}</strong>
                <p style={{ margin: "4px 0 0 0" }}>{f.message}</p>
              </div>
            ))}
          </Card>
          <Card title="Course Progress">
            {(report.course_reports || []).length === 0 ? <p>No course activity yet.</p> : (
              <table className="table">
                <thead><tr><th>Course</th><th>Progress</th><th>Videos</th><th>Quizzes</th></tr></thead>
                <tbody>{report.course_reports.map((course) => (
                  <tr key={course.course_id}>
                    <td>{course.title}</td>
                    <td>{course.completion_pct}% ({course.completed_lessons}/{course.total_lessons} lessons)</td>
                    <td>{course.completed_video_lessons}/{course.video_lessons} completed</td>
                    <td>{course.quizzes_attempted}/{course.quizzes} attempted</td>
                  </tr>
                ))}</tbody>
              </table>
            )}
          </Card>
        </>
      )}
    </Layout>
  );
}
