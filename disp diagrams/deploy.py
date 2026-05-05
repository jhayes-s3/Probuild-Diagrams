"""Deploy every .bpmn and .form in this folder to the local Camunda 8 REST API.

Usage: python deploy.py
"""

import json
import sys
import uuid
from pathlib import Path
from urllib import error, request

ENDPOINT = "http://localhost:8080/v2/deployments"
EXTS = {".bpmn", ".form"}


def build_multipart(files):
    boundary = uuid.uuid4().hex
    parts = []
    for path in files:
        safe_name = path.name.replace("\\", "\\\\").replace('"', '\\"')
        parts.append(f"--{boundary}".encode())
        parts.append(
            f'Content-Disposition: form-data; name="resources"; filename="{safe_name}"'.encode()
        )
        parts.append(b"Content-Type: application/octet-stream")
        parts.append(b"")
        parts.append(path.read_bytes())
    parts.append(f"--{boundary}--".encode())
    parts.append(b"")
    return b"\r\n".join(parts), f"multipart/form-data; boundary={boundary}"


def main():
    folder = Path(__file__).resolve().parent
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix in EXTS)

    if not files:
        print(f"No .bpmn or .form files in {folder}")
        return 1

    print(f"Deploying {len(files)} resource(s) to {ENDPOINT}")
    for f in files:
        print(f"  {f.name}")
    print()

    body, content_type = build_multipart(files)
    req = request.Request(ENDPOINT, data=body, method="POST")
    req.add_header("Content-Type", content_type)
    req.add_header("Content-Length", str(len(body)))

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

    try:
        data = json.loads(response_body)
    except json.JSONDecodeError:
        print(response_body)
        return 1 if status >= 400 else 0

    if status >= 400:
        print(f"Deployment rejected (HTTP {status}):")
        print(json.dumps(data, indent=2))
        return 1

    if "deploymentKey" in data:
        print(f"deploymentKey: {data['deploymentKey']}")
        count = len(data.get("deployments") or [])
        print(f"{count} resource(s) deployed")
    else:
        print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
