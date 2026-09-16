import Layout from "../../components/Layout";
import { Card, Loading, Table } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";

export default function AdminTeachers() {
  const { data: teachers, loading } = useApiData("/accounts/teachers/");

  return (
    <Layout title="Teachers">
      <Card>
        {loading ? (
          <Loading />
        ) : (
          <Table
            columns={[
              { key: "name", header: "Name", render: (r) => `${r.user.first_name} ${r.user.last_name}` },
              { key: "email", header: "Email", render: (r) => r.user.email },
              { key: "subject_specialization", header: "Subject" },
            ]}
            rows={teachers || []}
            rowKey={(r) => r.id}
          />
        )}
      </Card>
    </Layout>
  );
}
