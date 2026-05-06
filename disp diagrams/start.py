"""Kick off a new Probuild process instance.

Publishes Message-new-purchase-order with the standard test scaffold variables.
A fresh purchaseOrderId is generated each run so Zeebe doesn't dedupe.

Usage: python start.py [purchase_order_id]
"""

import json
import sys
import uuid
from urllib import error, request

ENDPOINT = "http://localhost:8080/v2/messages/publication"


def main() -> int:
    po_id = sys.argv[1] if len(sys.argv) > 1 else f"po-{uuid.uuid4().hex[:8]}"

    payload = {
        "name": "Message-new-purchase-order",
        "correlationKey": po_id,
        "variables": {
            "purchaseOrderId": po_id,
            "deliveryOrder": True,
            "deliveryOrderId": f"DO-{po_id}",
            "deliveryLocation": "123 Test Street, London",
            "tradeCardBeingUsed": True,
            "customerName": "Alex Customer",
            "customerEmail": "alex@example.com",
            "customerAddress": "456 Home Avenue, London",
            "customerPhone": "+44 20 7946 0123",
        },
    }

    body = json.dumps(payload).encode()
    req = request.Request(ENDPOINT, data=body, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        with request.urlopen(req) as resp:
            response_body = resp.read().decode()
            status = resp.status
    except error.HTTPError as e:
        response_body = e.read().decode()
        status = e.code
    except error.URLError as e:
        print(f"Connection failed: {e.reason}")
        print("Is Camunda running on localhost:8080?")
        return 1

    print(f"POST {ENDPOINT} -> HTTP {status}")
    print(f"purchaseOrderId: {po_id}")
    try:
        print(json.dumps(json.loads(response_body), indent=2))
    except json.JSONDecodeError:
        print(response_body)

    return 0 if status < 400 else 1


if __name__ == "__main__":
    sys.exit(main())
