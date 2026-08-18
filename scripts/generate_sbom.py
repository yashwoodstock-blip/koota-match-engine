"""Generate CycloneDX-style Software Bill of Materials (SBOM) for backend and mobile."""
import json
import os
from datetime import datetime, timezone

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_backend_sbom():
    req_file = os.path.join(ROOT_DIR, "requirements.txt")
    components = []
    if os.path.exists(req_file):
        with open(req_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("==")
                    name = parts[0].strip()
                    version = parts[1].strip() if len(parts) > 1 else "latest"
                    components.append({
                        "type": "library",
                        "name": name,
                        "version": version,
                        "purl": f"pkg:pypi/{name}@{version}",
                        "scope": "required",
                    })

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": "urn:uuid:koota-match-engine-backend-sbom",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": {
                "type": "application",
                "name": "koota-match-engine-backend",
                "version": "1.0.0",
                "description": "FastAPI 42-Koota Match Engine Backend",
            },
        },
        "components": components,
    }

    out_path = os.path.join(ROOT_DIR, "sbom-backend.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2)
    print(f"Generated {out_path} ({len(components)} components)")


def generate_mobile_sbom():
    pkg_file = os.path.join(ROOT_DIR, "mobile", "package.json")
    components = []
    if os.path.exists(pkg_file):
        with open(pkg_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})

            for name, version in deps.items():
                components.append({
                    "type": "library",
                    "name": name,
                    "version": version.lstrip("^~"),
                    "purl": f"pkg:npm/{name}@{version.lstrip('^~')}",
                    "scope": "required",
                })
            for name, version in dev_deps.items():
                components.append({
                    "type": "library",
                    "name": name,
                    "version": version.lstrip("^~"),
                    "purl": f"pkg:npm/{name}@{version.lstrip('^~')}",
                    "scope": "optional",
                })

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": "urn:uuid:koota-match-mobile-sbom",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": {
                "type": "application",
                "name": "koota-match-mobile",
                "version": "1.0.0",
                "description": "React Native Expo Client for Koota Match Engine",
            },
        },
        "components": components,
    }

    out_path = os.path.join(ROOT_DIR, "sbom-mobile.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2)
    print(f"Generated {out_path} ({len(components)} components)")


if __name__ == "__main__":
    generate_backend_sbom()
    generate_mobile_sbom()
