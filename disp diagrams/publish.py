"""Publish a single message to the local Camunda 8 REST API.

Usage:
    python publish.py <message-name> <correlation-key> [var=value ...]

Examples:
    python publish.py Message-recieve-location-to-deliver "123 Test Street, London"
    python publish.py Message-recieve-delivery-order DO-po-86e7d890
    python publish.py Message-some-event some-key foo=bar count=3
"""

import json
import sys
from urllib import error, request

ENDPOINT = "http://localhost:8080/v2/messages/publication"


def parse_var(token: str):
    if "=" not in token:
        raise ValueError(f"Variable '{token}' is not in key=value form")
    key, raw = token.split("=", 1)
    if raw == "true":
        return key, True
    if raw == "false":
        return key, False
    try:
        return key, int(raw)
    except ValueError:
        pass
    try:
        return key, float(raw)
    except ValueError:
        pass
    return key, raw


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2

    name = sys.argv[1]
    correlation_key = sys.argv[2]
    variables = dict(parse_var(t) for t in sys.argv[3:])

    payload = {
        "name": name,
        "correlationKey": correlation_key,
        "variables": variables,
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
        return 1

    print(f"POST {ENDPOINT} -> HTTP {status}")
    print(f"  name:           {name}")
    print(f"  correlationKey: {correlation_key}")
    if variables:
        print(f"  variables:      {variables}")
    try:
        print(json.dumps(json.loads(response_body), indent=2))
    except json.JSONDecodeError:
        print(response_body)

    return 0 if status < 400 else 1


if __name__ == "__main__":
    sys.exit(main())
