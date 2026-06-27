#!/usr/bin/env python3
"""Compile a capture runbook from script.json.

Reads script.json, walks every scene, extracts any `tour_action` or
`screenshot_action` block, and emits a unified Playwright runbook that the
capture pass (run_capture_pass.py) executes in a single authenticated session.

Each entry in the runbook is one capture — either a tour MP4 (per-scene
recording driven by the scene's tour_action.steps) or a UI-state PNG (per-scene
screenshot driven by the scene's screenshot_action.steps). The output paths are
deterministic so build_props.py can auto-wire them to the right scenes.

Usage:
    python compile_capture_spec.py \\
        --script script.json \\
        --auth ~/Desktop/CLAUDE/Claude\\ VIDEOS/Site\\ Credentials/koala.json \\
        --tour-out-dir broll/tour \\
        --screenshot-out-dir screenshots/scene \\
        --output capture_spec.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VIEWPORT = {"width": 1920, "height": 1080}

VALID_DO = {"wait", "goto", "click", "type", "hover", "highlight", "scroll", "key", "dismiss_overlay"}


def validate_steps(scene_id: str, steps: list[dict], action_type: str) -> list[str]:
    """Lightweight schema check — returns a list of error strings."""
    errors: list[str] = []
    if not isinstance(steps, list) or not steps:
        return [f"{scene_id}: {action_type}.steps must be a non-empty list"]
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"{scene_id}: {action_type}.steps[{i}] is not an object")
            continue
        do = step.get("do")
        if do not in VALID_DO:
            errors.append(f"{scene_id}: {action_type}.steps[{i}].do='{do}' not in {sorted(VALID_DO)}")
            continue
        # per-do arg checks
        if do == "wait" and not isinstance(step.get("ms"), (int, float)):
            errors.append(f"{scene_id}: wait step needs numeric ms")
        if do == "goto" and not step.get("url"):
            errors.append(f"{scene_id}: goto step needs url")
        if do in {"click", "hover", "type"} and not step.get("selector"):
            errors.append(f"{scene_id}: {do} step needs selector")
        if do == "type" and "text" not in step:
            errors.append(f"{scene_id}: type step needs text")
        if do == "highlight":
            if not step.get("selector"):
                errors.append(f"{scene_id}: highlight step needs selector")
            if not isinstance(step.get("ms"), (int, float)):
                errors.append(f"{scene_id}: highlight step needs numeric ms")
        if do == "scroll" and not (step.get("selector") or step.get("pixels") is not None):
            errors.append(f"{scene_id}: scroll step needs selector OR pixels")
        if do == "key" and not step.get("combo"):
            errors.append(f"{scene_id}: key step needs combo")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile capture runbook from script.json")
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--auth", type=Path, default=None,
                        help="Path to credentials JSON (storage_state). Optional — if missing, tour entries are skipped with a warning.")
    parser.add_argument("--tour-out-dir", type=Path, default=Path("broll/tour"))
    parser.add_argument("--screenshot-out-dir", type=Path, default=Path("screenshots/scene"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    raw = json.loads(args.script.read_text())
    scenes = raw["scenes"] if isinstance(raw, dict) and "scenes" in raw else raw

    storage_state_path: str | None = None
    auth_available = False
    if args.auth and args.auth.exists():
        try:
            cred = json.loads(args.auth.read_text())
            ss = cred.get("storage_state") or cred.get("auth", {}).get("storage_state_path")
            if ss:
                storage_state_path = str(Path(ss).expanduser())
                auth_available = True
        except Exception as e:
            print(f"WARN: could not parse auth file: {e}", file=sys.stderr)

    entries: list[dict] = []
    errors: list[str] = []
    auth_required_no_auth: list[str] = []  # tour scenes flagged requires_auth but auth isn't loaded

    for scene in scenes:
        sid = scene.get("id")
        if not sid:
            errors.append("scene missing id")
            continue

        tour = scene.get("tour_action")
        shot = scene.get("screenshot_action")

        if tour:
            errs = validate_steps(sid, tour.get("steps", []), "tour_action")
            if not tour.get("url"):
                errs.append(f"{sid}: tour_action.url is required")
            errors.extend(errs)
            # In v4 we ALWAYS include tour entries — public-page tours
            # (homepage scrolls, marketing pages, etc.) are just as script-driven
            # as authenticated tours. The capture pass opens an unauthenticated
            # context when storage_state is None; Playwright handles that fine.
            #
            # We do flag scenes whose tour_action explicitly says requires_auth
            # if no auth is currently loaded, so the operator knows those will
            # likely hit a login wall. validate_capture.py will catch any black
            # frames / 401 redirects too.
            requires_auth = bool(tour.get("requires_auth", False))
            if requires_auth and not auth_available:
                auth_required_no_auth.append(sid)
            entries.append({
                "scene_id": sid,
                "type": "tour",
                "url": tour["url"],
                "steps": tour["steps"],
                "expected_duration_sec": float(tour.get("expected_duration_sec", 8.0)),
                "requires_auth": requires_auth,
                "output_path": str(args.tour_out_dir / f"{sid}.mp4"),
            })

        if shot:
            errs = validate_steps(sid, shot.get("steps", []), "screenshot_action")
            if not shot.get("url"):
                errs.append(f"{sid}: screenshot_action.url is required")
            errors.extend(errs)
            entries.append({
                "scene_id": sid,
                "type": "screenshot",
                "url": shot["url"],
                "steps": shot["steps"],
                "viewport_focus": shot.get("viewport_focus"),
                "output_path": str(args.screenshot_out_dir / f"{sid}.png"),
            })

        # Multi-shot: screenshot_actions[] for screenshot-burst layouts (lean v2 addition).
        # Each entry in the array becomes its own capture; output filename includes the
        # scene id + the action's `output_name` so build_props can wire all 3 into the
        # screenshot-burst scene.
        shots = scene.get("screenshot_actions")
        if shots:
            if not isinstance(shots, list):
                errors.append(f"{sid}: screenshot_actions must be an array")
            else:
                for i, multi in enumerate(shots):
                    if not isinstance(multi, dict):
                        errors.append(f"{sid}: screenshot_actions[{i}] must be an object")
                        continue
                    name = multi.get("output_name") or f"{i + 1}"
                    errs = validate_steps(sid, multi.get("steps", []), f"screenshot_actions[{i}]")
                    if not multi.get("url"):
                        errs.append(f"{sid}: screenshot_actions[{i}].url is required")
                    errors.extend(errs)
                    entries.append({
                        "scene_id": sid,
                        "type": "screenshot",
                        "burst_index": i,
                        "burst_total": len(shots),
                        "url": multi["url"],
                        "steps": multi["steps"],
                        "viewport_focus": multi.get("viewport_focus"),
                        "output_path": str(args.screenshot_out_dir / f"{sid}-{name}.png"),
                    })

        if scene.get("layout") == "tour-full" and not tour:
            errors.append(f"{sid}: layout=tour-full but no tour_action declared")
        # Lean-skill rule: screenshot-burst MUST declare screenshot_actions[]
        # (single screenshot_action is wrong shape for a 3-up grid)
        if scene.get("layout") == "screenshot-burst" and not shots:
            errors.append(
                f"{sid}: layout=screenshot-burst requires screenshot_actions[] "
                f"(typically 3 entries for the 3-up grid). Got screenshot_action only."
                if shot else
                f"{sid}: layout=screenshot-burst requires screenshot_actions[]"
            )

    if errors:
        print("Capture spec validation errors:", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        sys.exit(2)

    spec = {
        "viewport": VIEWPORT,
        "auth_storage_state": storage_state_path,
        "auth_available": auth_available,
        "auth_required_no_auth": auth_required_no_auth,
        "entries": entries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(spec, indent=2))

    n_tour = sum(1 for e in entries if e["type"] == "tour")
    n_tour_auth = sum(1 for e in entries if e["type"] == "tour" and e.get("requires_auth"))
    n_tour_public = n_tour - n_tour_auth
    n_shot = sum(1 for e in entries if e["type"] == "screenshot")
    print(
        f"\nCapture spec: {len(entries)} entries "
        f"({n_tour} tour [{n_tour_public} public, {n_tour_auth} auth], {n_shot} screenshot)",
        file=sys.stderr,
    )
    if auth_required_no_auth:
        print(
            f"WARN: {len(auth_required_no_auth)} tour scene(s) flagged requires_auth=true but no "
            f"auth loaded — they will run anyway and likely hit a login wall. Capture them after "
            f"running playwright-auth-capture, or remove requires_auth if the URL is actually public: "
            f"{', '.join(auth_required_no_auth)}",
            file=sys.stderr,
        )
    print(f"Wrote: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
