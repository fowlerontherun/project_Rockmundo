from __future__ import annotations
import json, argparse, urllib.request, pathlib
from typing import Any, Dict

POSTMAN_VERSION = "2.1.0"


def _load_openapi(ref: str) -> Dict[str, Any]:
    if ref.startswith("http://") or ref.startswith("https://"):
        with urllib.request.urlopen(ref) as r:
            return json.loads(r.read().decode("utf-8"))
    else:
        return json.loads(pathlib.Path(ref).read_text(encoding="utf-8"))


def _to_pm_item(base_url_var: str, path: str, method: str, op: Dict[str, Any]) -> Dict[str, Any]:
    name = op.get("summary") or f"{method.upper()} {path}"
    url = f"{{{{{base_url_var}}}}}{path}"
    headers = [{"key": "Authorization", "value": "Bearer {{token}}"}]
    body = None
    req_body = op.get("requestBody", {})
    content = req_body.get("content", {}) if isinstance(req_body, dict) else {}
    app_json = content.get("application/json", {})
    examples = app_json.get("examples", {}) if isinstance(app_json, dict) else {}
    example_val = None
    if examples:
        first = next(iter(examples.values()))
        example_val = first.get("value")
    elif "example" in app_json:
        example_val = app_json.get("example")
    if example_val is not None:
        body = {"mode": "raw", "raw": json.dumps(example_val, indent=2), "options": {"raw": {"language": "json"}}}

    item = {"name": name, "request": {"method": method.upper(), "header": headers, "url": {"raw": url, "host": [f"{{{{{base_url_var}}}}}"], "path": path.strip("/").split("/")}}}
    if body:
        item["request"]["body"] = body
    return item


def openapi_to_postman(openapi: Dict[str, Any], name: str, base_url_var: str = "baseUrl") -> Dict[str, Any]:
    items = []
    paths = openapi.get("paths", {})
    for p, p_obj in paths.items():
        for method, op in p_obj.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            items.append(_to_pm_item(base_url_var, p, method, op))

    collection = {
        "info": {
            "name": name,
            "_postman_id": "rockmundo-" + name.lower().replace(" ", "-"),
            "schema": f"https://schema.getpostman.com/json/collection/v{POSTMAN_VERSION}/collection.json",
        },
        "item": items,
        "variable": [{"key": base_url_var, "value": "http://localhost:8000"}, {"key": "token", "value": "<paste JWT here>"}],
        "auth": {"type": "bearer", "bearer": [{"key": "token", "value": "{{token}}", "type": "string"}]},
    }
    return collection


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--openapi", required=True, help="URL or file path to openapi.json")
    ap.add_argument("--name", default="API", help="Collection name")
    ap.add_argument("--out", required=True, help="Output path for the Postman collection JSON")
    args = ap.parse_args()

    openapi = _load_openapi(args.openapi)
    col = openapi_to_postman(openapi, args.name)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(col, indent=2), encoding="utf-8")
    print(f"Wrote Postman collection → {out_path}")


if __name__ == "__main__":
    main()
