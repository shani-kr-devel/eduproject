import { useState } from "react";
import Layout from "../../components/Layout";
import { Card, Loading, Empty, Table } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";

export default function ParentChildren() {
  const { data: profile, loading } = useApiData("/accounts/parents/");
  const me = profile?.[0];
  const [selected, setSelected] = useState(null);

  const { data: enrollments } = useApiData(
    selected ? "/courses/enrollments/" : null,
    { enabled: !!selected, params: { student: selected } }
  );

  return (
    <Layout title="My Children">
      {loading ? (
        <Loading />
      ) : (me?.children || []).length === 0 ? (
        <Empty>No children linked yet — use "Add a Child" in the sidebar.</Empty>
      ) : (
        <div className="two-col">
          <div className="card">
            {me.children.map((child) => (
              <button
                key={child.id}
                className={`list-item-btn ${selected === child.id ? "active" : ""}`}
                onClick={() => setSelected(child.id)}
              >
                {child.user.first_name} {child.user.last_name} — {child.student_id}
              </button>
            ))}
          </div>
          <div>
            {!selected ? (
              <Empty>Select a child to view their courses.</Empty>
            ) : (
              <>
                <Card title="Purchased Courses">
                  <Table
                    columns={[
                      { key: "title", header: "Course", render: (r) => r.course.title },
                      { key: "enrolled_at", header: "Enrolled" },
                    ]}
                    rows={enrollments || []}
                    rowKey={(r) => r.id}
                  />
                </Card>
              </>
            )}
          </div>
        </div>
      )}
    </Layout>
  );
}
