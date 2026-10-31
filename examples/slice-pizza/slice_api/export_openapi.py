"""Write openapi.json next to the README: `python -m slice_api.export_openapi`."""

import json
from pathlib import Path

from slice_api.main import app

if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "openapi.json"
    out.write_text(json.dumps(app.openapi(), indent=2) + "\n")
    print(f"wrote {out}")
