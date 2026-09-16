import Layout from "../../components/Layout";
import { Card, Loading, Table } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";

export default function AdminStudents() {
  const { data: students, loading } = useApiData("/accounts/students/");

  return (
    <Layout title="Students">
      <Card>
        {loading ? (
          <Loading />
        ) : (
          <Table
            columns={[
              { key: "name", header: "Name", render: (r) => `${r.user.first_name} ${r.user.last_name}` },
              { key: "student_id", header: "Student ID" },
              { key: "grade_level", header: "Grade" },
              { key: "teacher_names", header: "Teachers", render: (r) => (r.teacher_names || []).join(", ") },
            ]}
            rows={students || []}
            rowKey={(r) => r.id}
          />
        )}
      </Card>
    </Layout>
  );
}
