"""Deploy every .bpmn and .form in this folder to the local Camunda 8 REST API.

Usage: python deploy.py

Each file is sent as its own deployment. Camunda's gateway has a low cap on
parts-per-multipart-request, so a single 60-file upload fails with HTTP 500;
looping one-by-one mirrors what manual Postman deploys do.
"""

import json
import subprocess
import sys
from pathlib import Path

ENDPOINT = "http://localhost:8080/v2/deployments"
EXTS = {".bpmn", ".form"}


def deploy_one(path: Path) -> tuple[bool, str]:
    cmd = [
        "curl.exe", "-sS", "-X", "POST", ENDPOINT,
        "-F", f"resources=@{path}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, f"curl exit {result.returncode}: {result.stderr.strip()}"

    body = result.stdout.strip()
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return False, body

    if isinstance(data, dict):
        status = data.get("status")
        if isinstance(status, int) and status >= 400:
            detail = data.get("detail") or data.get("title") or json.dumps(data)
            return False, f"HTTP {status}: {detail}"
        if "deploymentKey" in data:
            return True, str(data["deploymentKey"])
    return False, body


def main() -> int:
    folder = Path(__file__).resolve().parent
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix in EXTS)

    if not files:
        print(f"No .bpmn or .form files in {folder}")
        return 1

    print(f"Deploying {len(files)} resource(s) to {ENDPOINT}\n")

    ok = 0
    failures: list[tuple[str, str]] = []
    for f in files:
        success, msg = deploy_one(f)
        if success:
            ok += 1
            print(f"  [ok]   {f.name}  (deploymentKey {msg})")
        else:
            failures.append((f.name, msg))
            print(f"  [fail] {f.name}  {msg}")

    print()
    print(f"{ok}/{len(files)} deployed.")
    if failures:
        print(f"{len(failures)} failure(s):")
        for name, msg in failures:
            print(f"  - {name}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
