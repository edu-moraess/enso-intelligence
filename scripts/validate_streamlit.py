"""Smoke-test the current single-page Streamlit observatory."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest


def main() -> None:
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
    app.run(timeout=120)
    if app.exception:
        raise SystemExit("Streamlit rendered with exceptions: " + " | ".join(str(e) for e in app.exception))

    text = "\n".join(element.value for element in app.markdown if hasattr(element, "value"))
    required = [
        "CURRENT CONDITIONS",
        "ENSO SIGNAL",
        "HISTORICAL ANALOGUES",
        "PACIFIC CONDITIONS",
        "ANALYTICAL VIEW",
        "METHODOLOGY",
        "DATA & PROVENANCE",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(f"Missing rendered sections: {missing}")

    print(
        f"Streamlit render: PASS markdown={len(app.markdown)} "
        f"charts={len(app.get('plotly_chart'))} metrics={len(app.metric)}"
    )
    print("Rendered sections:", ", ".join(required))


if __name__ == "__main__":
    main()
