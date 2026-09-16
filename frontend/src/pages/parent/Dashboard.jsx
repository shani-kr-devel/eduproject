import Layout from "../../components/Layout";
import { Card, Loading, StatCard } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";

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
        </>
      )}
    </Layout>
  );
}
