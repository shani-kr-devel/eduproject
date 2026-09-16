import { useState } from "react";
import Layout from "../../components/Layout";
import { Loading } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";
import api from "../../api/axiosClient";

export default function StudentStore() {
  const { data: courses, loading, reload } = useApiData("/courses/courses/");
  const [checkoutState, setCheckoutState] = useState(null); // {course, order, checkout_config}
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function startCheckout(course) {
    setMessage("");
    setBusy(true);
    try {
      const res = await api.post("/courses/checkout/", { course_id: course.id });
      setCheckoutState({ course, ...res.data });
    } catch (err) {
      setMessage(err.response?.data?.detail || "Could not start checkout.");
    } finally {
      setBusy(false);
    }
  }

  async function payNow(method) {
    setBusy(true);
    try {
      if (checkoutState.checkout_config.gateway === "mock") {
        await api.post("/courses/mock/simulate-payment/", {
          order_id: checkoutState.order.order_id,
          method,
        });
      }
      setMessage(`Payment successful via ${method.replace("_", " ")}. You're enrolled!`);
      setCheckoutState(null);
      reload();
    } catch (err) {
      setMessage(err.response?.data?.detail || "Payment failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Layout title="Course Store">
      {message && (
        <div className="card" style={{ marginBottom: 16, borderColor: "#2563EB" }}>
          {message}
        </div>
      )}

      {checkoutState && (
        <div className="card" style={{ marginBottom: 20 }}>
          <h3>Checkout — {checkoutState.course.title}</h3>
          <p>
            Amount: <strong>₹{checkoutState.order.amount}</strong> · Order ID: {checkoutState.order.order_id}
          </p>
          <p style={{ color: "#64748b", fontSize: "0.85rem" }}>
            Choose a payment method to simulate the secure gateway checkout (UPI / Google Pay / PhonePe / Paytm all
            route through the same payment aggregator in production).
          </p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {["upi", "google_pay", "phonepe", "paytm"].map((m) => (
              <button key={m} className="btn btn-primary btn-sm" disabled={busy} onClick={() => payNow(m)}>
                Pay with {m.replace("_", " ")}
              </button>
            ))}
            <button className="btn btn-outline btn-sm" onClick={() => setCheckoutState(null)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <Loading />
      ) : (
        <div className="course-grid">
          {(courses || []).map((c) => (
            <div className="course-card" key={c.id}>
              <div className="course-thumb" />
              <div className="course-body">
                <strong>{c.title}</strong>
                <span style={{ fontSize: "0.82rem", color: "#64748b" }}>{c.description}</span>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "auto" }}>
                  <strong>₹{c.price}</strong>
                  {c.is_enrolled ? (
                    <span className="pill pill-blue">Owned</span>
                  ) : (
                    <button className="btn btn-primary btn-sm" disabled={busy} onClick={() => startCheckout(c)}>
                      Buy
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
