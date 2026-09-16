import Layout from "../../components/Layout";
import { Loading, StatCard } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";

export default function AdminDashboard() {
  const { data: students, loading: l1 } = useApiData("/accounts/students/");
  const { data: teachers, loading: l2 } = useApiData("/accounts/teachers/");
  const { data: parents, loading: l3 } = useApiData("/accounts/parents/");
  const { data: courses, loading: l5 } = useApiData("/courses/courses/");
  const { data: orders, loading: l6 } = useApiData("/courses/orders/");

  const loading = l1 || l2 || l3 || l5 || l6;
  const revenue = (orders || [])
    .filter((o) => o.status === "paid")
    .reduce((sum, o) => sum + Number(o.amount), 0);

  return (
    <Layout title="Admin Dashboard">
      {loading ? (
        <Loading />
      ) : (
        <div className="grid grid-4">
          <StatCard label="Students" value={(students || []).length} />
          <StatCard label="Teachers" value={(teachers || []).length} />
          <StatCard label="Parents" value={(parents || []).length} />
          <StatCard label="Courses" value={(courses || []).length} />
          <StatCard label="Total Orders" value={(orders || []).length} />
          <StatCard label="Paid Orders" value={(orders || []).filter((o) => o.status === "paid").length} />
          <StatCard label="Revenue" value={`₹${revenue.toLocaleString("en-IN")}`} />
        </div>
      )}
    </Layout>
  );
}
