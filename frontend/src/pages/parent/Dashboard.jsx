import Layout from "../../components/Layout";
import { Card, Empty, Loading, StatCard } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";

function Status({ completed }) {
  return <span className={`pill ${completed ? "pill-blue" : "pill-slate"}`}>{completed ? "Completed" : "Pending"}</span>;
}

function ChildDailyReport({ child }) {
  const { data: report, loading } = useApiData(`/academics/daily-report/${child.id}/`);

  if (loading) return <Card title={`${child.user.first_name}'s Daily Report`}><Loading /></Card>;
  if (!report) return null;

  const hasItems = report.homework.length || report.tests.length || report.tasks.length;
  return (
    <Card title={`${child.user.first_name}'s Daily Report`}>
      <div style={{ color: "#64748b", fontSize: "0.85rem", marginBottom: 12 }}>{report.date}</div>
      <div className="grid grid-3">
        <StatCard label="Homework" value={`${report.summary.homework_completed}/${report.summary.homework_total}`} />
        <StatCard label="Tests" value={`${report.summary.tests_completed}/${report.summary.tests_total}`} />
        <StatCard label="Tasks completed" value={report.summary.tasks_completed} />
      </div>
      {!hasItems ? <Empty>No homework, tests, or learning tasks scheduled today.</Empty> : (
        <div style={{ marginTop: 16 }}>
          {report.homework.map((item) => (
            <div key={`homework-${item.id}`} className="teacher-report-row">
              <span><strong>Homework:</strong> {item.title}</span><Status completed={item.completed} />
            </div>
          ))}
          {report.tests.map((item) => (
            <div key={`test-${item.id}`} className="teacher-report-row">
              <span><strong>Test:</strong> {item.title} <small>({item.subject})</small></span><Status completed={item.completed} />
            </div>
          ))}
          {report.tasks.map((item) => (
            <div key={`task-${item.id}`} className="teacher-report-row">
              <span><strong>Task:</strong> {item.title} <small>({item.course})</small></span><Status completed />
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default function ParentDashboard() {
  const { data: profile, loading } = useApiData("/accounts/parents/");
  const me = profile?.[0];

  return (
    <Layout title="Parent Dashboard">
      {loading ? (
        <Loading />
      ) : (
        <>
          <div className="grid grid-2">
            <StatCard label="Linked Children" value={(me?.children || []).length} />
          </div>
          <Card title="Your Children">
            {(me?.children || []).map((child) => (
              <div key={child.id} style={{ padding: "10px 0", borderBottom: "1px solid #f1f5f9" }}>
                <strong>{child.user.first_name} {child.user.last_name}</strong>{" "}
                <span className="pill pill-slate">{child.student_id}</span>
                <div style={{ fontSize: "0.85rem", color: "#64748b" }}>
                  Grade {child.grade_level || "—"}
                </div>
              </div>
            ))}
            {(me?.children || []).length === 0 && <p>No children linked yet — use "Add a Child".</p>}
          </Card>
          {(me?.children || []).map((child) => <ChildDailyReport key={child.id} child={child} />)}
        </>
      )}
    </Layout>
  );
}
