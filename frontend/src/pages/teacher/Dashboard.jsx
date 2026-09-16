import Layout from "../../components/Layout";
import { Card, Loading, StatCard } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";

export default function TeacherDashboard() {
  const { data: students, loading: sLoading } = useApiData("/accounts/students/");
  const { data: tests, loading: tLoading } = useApiData("/academics/tests/");

  return (
    <Layout title="Teacher Dashboard">
      {sLoading || tLoading ? (
        <Loading />
      ) : (
        <>
          <div className="grid grid-3">
            <StatCard label="My Students" value={(students || []).length} />
            <StatCard label="Tests created" value={(tests || []).length} />
          </div>
          <Card title="My Students">
            {(students || []).map((s) => (
              <div key={s.id} style={{ padding: "8px 0", borderBottom: "1px solid #f1f5f9" }}>
                {s.user.first_name} {s.user.last_name} — <span className="pill pill-slate">{s.student_id}</span>
              </div>
            ))}
          </Card>
        </>
      )}
    </Layout>
  );
}
