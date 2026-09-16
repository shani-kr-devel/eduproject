import Layout from "../../components/Layout";
import { Card, Loading, Table, Pill } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";

export default function AdminOrders() {
  const { data: orders, loading } = useApiData("/courses/orders/");

  return (
    <Layout title="Orders">
      <Card>
        {loading ? (
          <Loading />
        ) : (
          <Table
            columns={[
              { key: "order_id", header: "Order ID" },
              { key: "student_id_code", header: "Student" },
              { key: "course_title", header: "Course" },
              { key: "amount", header: "Amount", render: (r) => `₹${r.amount}` },
              {
                key: "status",
                header: "Status",
                render: (r) => <Pill tone={r.status === "paid" ? "blue" : "slate"}>{r.status}</Pill>,
              },
              { key: "created_at", header: "Date", render: (r) => new Date(r.created_at).toLocaleString() },
            ]}
            rows={orders || []}
            rowKey={(r) => r.id}
          />
        )}
      </Card>
    </Layout>
  );
}
