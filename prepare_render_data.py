"""Download the current OSU section data while Render builds the API."""

from __future__ import annotations

import json

from OSU_Class_Optimizer import OUTPUT_PATH, fetch_all_sections


def main() -> None:
    sections = fetch_all_sections()
    OUTPUT_PATH.write_text(json.dumps(sections), encoding="utf-8")
    print(f"Saved {len(sections):,} sections to {OUTPUT_PATH.name}.")


if __name__ == "__main__":
    main()
