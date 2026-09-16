import Layout from "../../components/Layout";
import { Card, Loading, Table } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";

export default function AdminParents() {
  const { data: parents, loading } = useApiData("/accounts/parents/");

  return (
    <Layout title="Parents">
      <Card>
        {loading ? (
          <Loading />
        ) : (
          <Table
            columns={[
              { key: "name", header: "Name", render: (r) => `${r.user.first_name} ${r.user.last_name}` },
              { key: "email", header: "Email", render: (r) => r.user.email },
              {
                key: "children",
                header: "Children",
                render: (r) => (r.children || []).map((c) => c.student_id).join(", ") || "—",
              },
            ]}
            rows={parents || []}
            rowKey={(r) => r.id}
          />
        )}
      </Card>
    </Layout>
  );
}
