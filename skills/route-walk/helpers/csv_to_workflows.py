#!/usr/bin/env python3
"""Convert a route-walk CSV to a qa-walk workflows.yaml skeleton.

Usage:
    python3 csv_to_workflows.py <csv-path> <app-slug> [--exclude-tavus] [--persona-map <json>]

The output is a YAML skeleton. Definitions of done and route entries need
human editing afterward  -  this script gives the bones, not the meat.

CSV row -> workflow entry mapping:
    route_id       -> id
    flow + auth + tier -> name (synthesized)
    tier+auth_state -> persona (via --persona-map or default mapping)
    start_surface  -> entry_route (default: /<start_surface>)
    coverage_notes -> definition_of_done seed
    coverage_notes -> do_not_change (empty by default; reviewer adds)

Rows skipped when --exclude-tavus:
    conversation_mode == avatar
    start_surface in {demo, chat_mirror}
    auth_method == demo_public
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


DEFAULT_PERSONA_MAP = {
    ("signed_out", "guest"): "guest",
    ("anonymous_guest", "guest"): "guest",
    ("registered_onboarded", "standard"): "standard",
    ("registered_onboarded", "premium"): "premium",
    ("registered_onboarded", "black_label"): "black_label",
    ("registered", "standard"): "standard",
}


def is_tavus_row(row: dict[str, str]) -> bool:
    if row.get("conversation_mode") == "avatar":
        return True
    if row.get("start_surface") in ("demo", "chat_mirror"):
        return True
    if row.get("auth_method") == "demo_public":
        return True
    return False


def synth_name(row: dict[str, str]) -> str:
    return f"{row['flow']} {row['route_id']}  -  {row.get('coverage_notes', '')[:60].split(chr(46))[0]}"


def synth_route(row: dict[str, str]) -> str:
    surface = row.get("start_surface", "").strip()
    if not surface or surface == "NA":
        return "/"
    # Expo Router strips group parens on web; map known surface names.
    aliases = {
        "welcome": "/",
        "home": "/",
        "upgrading": "/upgrading",
        "demo": "/demo",
        "chat": "/chat",
        "chat_list": "/chat",
        "chat_mirror": "/chat/mirror",
        "venue": "/venue",
        "discover": "/discover",
        "trips": "/trips",
        "squad": "/squad",
        "profile": "/profile",
        "booking": "/booking",
        "bookings_detail": "/bookings",
        "itinerary": "/itinerary",
        "notifications": "/notifications",
    }
    return aliases.get(surface, f"/{surface}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("app_slug")
    ap.add_argument("--exclude-tavus", action="store_true")
    ap.add_argument("--persona-map", help="JSON dict overriding default persona mapping")
    args = ap.parse_args()

    persona_map = DEFAULT_PERSONA_MAP.copy()
    if args.persona_map:
        persona_map.update(
            {tuple(k.split(",")): v for k, v in json.loads(args.persona_map).items()}
        )

    with open(args.csv_path) as f:
        rows = list(csv.DictReader(f))

    kept = []
    skipped = []
    for r in rows:
        if args.exclude_tavus and is_tavus_row(r):
            skipped.append(r["route_id"])
            continue
        persona = persona_map.get((r.get("auth_state", ""), r.get("tier", "")), "guest")
        kept.append({
            "id": r["route_id"],
            "name": synth_name(r),
            "persona": persona,
            "entry_route": synth_route(r),
            "test_data": {},
            "definition_of_done": r.get("coverage_notes", "").strip() or f"Walk path {r['route_id']}.",
            "do_not_change": "",
            "regression_checks": [],
        })

    out = {
        "app": args.app_slug,
        "last_scaffold": "TBD",
        "workflows": kept,
    }

    import yaml  # local import to avoid cost when --help

    print(yaml.safe_dump(out, sort_keys=False, default_flow_style=False, width=120))
    print(f"# kept={len(kept)} skipped_tavus={len(skipped)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
