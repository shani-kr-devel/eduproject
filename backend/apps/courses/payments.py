"""
Payment gateway abstraction.

India-based UPI / Google Pay / PhonePe / Paytm collection is normally done
through a single PSP aggregator (Razorpay, Cashfree, etc.) rather than
integrating each wallet separately - the aggregator exposes all four rails
under one checkout + one webhook. This module ships:

  * MockGateway   - simulates the full flow with no external account, so the
                    entire Student -> Course -> Checkout -> Payment ->
                    Enrollment pipeline can be built/tested/demoed today.
  * RazorpayGateway - thin real adapter. Drop in real keys (RAZORPAY_KEY_ID /
                    RAZORPAY_KEY_SECRET / RAZORPAY_WEBHOOK_SECRET) and swap
                    PAYMENT_GATEWAY=razorpay in .env to go live; no other
                    code in the project needs to change because views only
                    ever talk to `get_gateway()`.

Whichever gateway is active, this project NEVER stores card/UPI credentials -
only opaque gateway order/payment IDs and whatever non-sensitive metadata the
gateway returns, and every payment is confirmed via signature-verified
webhook rather than trusting the client's "it succeeded" callback alone.
"""
import hashlib
import hmac
import json
import uuid

from django.conf import settings


class PaymentGatewayError(Exception):
    pass


class BaseGateway:
    def create_order(self, *, amount_rupees, receipt, notes=None):
        """Returns dict: {gateway_order_id, checkout_config}"""
        raise NotImplementedError

    def verify_webhook_signature(self, *, payload_body: bytes, signature: str) -> bool:
        raise NotImplementedError

    def verify_client_checkout_payload(self, *, order, data) -> bool:
        """Optional secondary check of the signature the checkout SDK returns
        client-side, BEFORE relying on the async webhook. Either path alone
        is sufficient for correctness; using both reduces latency."""
        raise NotImplementedError


class MockGateway(BaseGateway):
    """No network calls. 'Succeeds' deterministically so the whole purchase
    flow (including webhook-style verification) can be exercised in dev/CI."""

    def create_order(self, *, amount_rupees, receipt, notes=None):
        gateway_order_id = f"mock_order_{uuid.uuid4().hex[:16]}"
        return {
            "gateway_order_id": gateway_order_id,
            "checkout_config": {
                "gateway": "mock",
                "order_id": gateway_order_id,
                "amount": str(amount_rupees),
                "currency": "INR",
                "supported_methods": ["upi", "google_pay", "phonepe", "paytm"],
            },
        }

    def verify_webhook_signature(self, *, payload_body: bytes, signature: str) -> bool:
        # Mock signature is just an HMAC of the body with the (fake) secret,
        # so local webhook-simulation tests can still exercise real logic.
        expected = hmac.new(b"mock-secret", payload_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature or "")

    def verify_client_checkout_payload(self, *, order, data) -> bool:
        return data.get("mock_payment_id", "").startswith("mock_pay_")


class RazorpayGateway(BaseGateway):
    """Real adapter. Requires the `razorpay` package and live keys.
    Only imports the SDK lazily so the rest of the project works without it
    installed while PAYMENT_GATEWAY=mock."""

    def __init__(self):
        import razorpay  # noqa: F401 (import guarded/lazy on purpose)

        self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    def create_order(self, *, amount_rupees, receipt, notes=None):
        order = self.client.order.create(
            {
                "amount": int(amount_rupees * 100),  # paise
                "currency": "INR",
                "receipt": receipt,
                "notes": notes or {},
                "payment_capture": 1,
            }
        )
        return {
            "gateway_order_id": order["id"],
            "checkout_config": {
                "gateway": "razorpay",
                "key": settings.RAZORPAY_KEY_ID,
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                # method: "upi" lets Razorpay Checkout present UPI intent /
                # collect flows plus the Google Pay, PhonePe and Paytm apps
                # automatically - no separate integration needed per wallet.
                "method_hint": "upi",
            },
        }

    def verify_webhook_signature(self, *, payload_body: bytes, signature: str) -> bool:
        try:
            self.client.utility.verify_webhook_signature(
                payload_body.decode(), signature, settings.RAZORPAY_WEBHOOK_SECRET
            )
            return True
        except Exception:
            return False

    def verify_client_checkout_payload(self, *, order, data) -> bool:
        try:
            self.client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": order.gateway_order_id,
                    "razorpay_payment_id": data.get("razorpay_payment_id"),
                    "razorpay_signature": data.get("razorpay_signature"),
                }
            )
            return True
        except Exception:
            return False


def get_gateway() -> BaseGateway:
    if settings.PAYMENT_GATEWAY == "razorpay":
        return RazorpayGateway()
    return MockGateway()
