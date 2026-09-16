import { Link } from "react-router-dom";
import Layout from "../../components/Layout";
import { Card, Loading, StatCard } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";
import { useAuth } from "../../context/AuthContext";

export default function StudentDashboard() {
  const { user } = useAuth();
  const { data: tests, loading: testsLoading } = useApiData("/academics/tests/");
  const { data: enrollments, loading: enrollLoading } = useApiData("/courses/enrollments/");

  const profile = user?.profile;

  return (
    <Layout title="Student Dashboard">
      {testsLoading || enrollLoading ? (
        <Loading />
      ) : (
        <>
          <div className="grid grid-4">
            <StatCard label="Student ID" value={user?.student_id} />
            <StatCard label="Tests on Record" value={(tests || []).length} />
            <StatCard label="Purchased Courses" value={(enrollments || []).length} />
          </div>

          <div className="grid grid-2" style={{ marginTop: 16 }}>
            <Card title="Profile">
              <p><strong>Grade level:</strong> {profile?.grade_level || "—"}</p>
              <p><strong>Teachers:</strong> {(profile?.teacher_names || []).join(", ") || "—"}</p>
            </Card>
            <Card title="Tests">
              <p>Complete your assigned timed tests and review your results.</p>
              <Link to="/student/tests">Open tests →</Link>
            </Card>
          </div>
        </>
      )}
    </Layout>
  );
}
