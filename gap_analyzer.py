#!/usr/bin/env python3
"""
ISO 27001 Gap Analyzer

Features
- Robust CLI with explicit inputs/outputs
- Accepts multiple JSON shapes (compatibility mode)
  * Controls file:
      1) {"controls": ["A.5.1", "A.5.2", ...]}
      2) ["A.5.1", "A.5.2", ...]
      3) {"A.5.1": {"title": "..."} , "A.5.2": {"title": "..."}}
  * Implementation file:
      1) {"controls": ["A.5.1", "A.5.2", ...]}
      2) ["A.5.1", "A.5.2", ...]
      3) {"A.5.1": true, "A.5.2": false, ...}
- Emits machine-readable JSON + human-readable Markdown
- Deterministic, CI-friendly exit codes

Exit codes
0  success
1  bad CLI usage / missing files
2  JSON parse errors
3  schema/validation errors
"""

from __future__ import annotations
import argparse
import json
import sys
import os
import pathlib
from datetime import datetime
from typing import Dict, List, Tuple, Any, Set


# ---------------------------
# I/O helpers
# ---------------------------

def _read_json(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found - {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Failed to parse JSON file {path}. Details: {e}", file=sys.stderr)
        sys.exit(2)


def _ensure_parent_dir(path: str) -> None:
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)


# ---------------------------
# Flexible schema loaders
# ---------------------------

def _as_string_list(obj: Any) -> List[str]:
    """If obj is a list of strings, return it; else []"""
    if isinstance(obj, list) and all(isinstance(x, str) for x in obj):
        return obj
    return []

def _as_controls_map(obj: Any) -> Dict[str, Dict[str, Any]]:
    """
    If obj looks like a map of control_id -> metadata dict, normalize to that.
    Values don't have to include 'title'; we keep whatever is present.
    """
    if isinstance(obj, dict):
        # Heuristic: keys look like ISO control IDs; values dict-like or str
        # We'll coerce str values into {"title": str}
        out: Dict[str, Dict[str, Any]] = {}
        for k, v in obj.items():
            if isinstance(v, dict):
                out[k] = dict(v)
            elif isinstance(v, str):
                out[k] = {"title": v}
            elif isinstance(v, bool):
                # This might be an implementation map; don't treat as controls map.
                return {}
            else:
                # Unknown shape; skip
                return {}
        if out:
            return out
    return {}

def load_controls(controls_json: Any) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """
    Returns:
      controls_map: {control_id: {"title": "...", ...}}
      controls_ids: list of control IDs (order not guaranteed)
    Accepts:
      - {"controls": ["A.5.1", ...]}
      - ["A.5.1", ...]
      - {"A.5.1": {"title": "..."} , ...}
    """
    # Case 1: root has "controls": [ids]
    if isinstance(controls_json, dict) and "controls" in controls_json:
        ids = _as_string_list(controls_json.get("controls"))
        if ids:
            return ({cid: {} for cid in ids}, ids)

    # Case 2: root is list of ids
    ids = _as_string_list(controls_json)
    if ids:
        return ({cid: {} for cid in ids}, ids)

    # Case 3: map of id -> metadata
    cmap = _as_controls_map(controls_json)
    if cmap:
        return (cmap, list(cmap.keys()))

    print("❌ Error: Controls file must be either a list of IDs, "
          "an object with 'controls': [IDs], or a map of ID->metadata.", file=sys.stderr)
    sys.exit(3)

def load_implemented(impl_json: Any) -> Tuple[Set[str], Dict[str, bool]]:
    """
    Returns:
      implemented_ids: set of implemented control IDs (best-effort)
      implemented_map: explicit map id->bool if available; else inferred True for listed IDs
    Accepts:
      - {"controls": ["A.5.1", ...]}
      - ["A.5.1", ...]
      - {"A.5.1": true, "A.5.2": false, ...}
    """
    # Case 1: {"controls": [ids]}
    if isinstance(impl_json, dict) and "controls" in impl_json:
        ids = _as_string_list(impl_json.get("controls"))
        if ids:
            return (set(ids), {cid: True for cid in ids})

    # Case 2: [ids]
    ids = _as_string_list(impl_json)
    if ids:
        return (set(ids), {cid: True for cid in ids})

    # Case 3: map id->bool
    if isinstance(impl_json, dict):
        # Ensure bool-ish values only
        clean_map: Dict[str, bool] = {}
        for k, v in impl_json.items():
            if isinstance(v, bool):
                clean_map[k] = v
            else:
                print(f"⚠️  Warning: Implementation value for {k} is not boolean; ignoring.", file=sys.stderr)
        if clean_map:
            implemented_ids = {k for k, flag in clean_map.items() if flag}
            return (implemented_ids, clean_map)

    print("❌ Error: Implementation file must be either a list of IDs, "
          "an object with 'controls': [IDs], or a map of ID->bool.", file=sys.stderr)
    sys.exit(3)


# ---------------------------
# Core logic
# ---------------------------

def compute_gaps(
    controls_map: Dict[str, Dict[str, Any]],
    controls_ids: List[str],
    implemented_ids: Set[str],
    implemented_map: Dict[str, bool],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[str]]:
    """
    Returns:
      results: list of {id, title, implemented}
      summary: {total_controls, implemented, gaps}
      gaps: list of missing control IDs
    """
    results: List[Dict[str, Any]] = []
    gaps: List[str] = []

    for cid in sorted(controls_ids):
        meta = controls_map.get(cid, {})
        title = meta.get("title", "")
        implemented = implemented_map.get(cid, (cid in implemented_ids))
        implemented = bool(implemented)

        results.append({
            "id": cid,
            "title": title,
            "implemented": implemented
        })
        if not implemented:
            gaps.append(cid)

    summary = {
        "total_controls": len(controls_ids),
        "implemented": sum(1 for r in results if r["implemented"]),
        "gaps": len(gaps),
    }
    return results, summary, gaps


# ---------------------------
# Renderers
# ---------------------------

def write_json_report(path: str, meta: Dict[str, Any], summary: Dict[str, Any],
                      results: List[Dict[str, Any]], gaps: List[str]) -> None:
    _ensure_parent_dir(path)
    payload = {
        "meta": meta,
        "summary": summary,
        "results": results,
        "gaps": gaps
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

def write_markdown_report(path: str, meta: Dict[str, Any], summary: Dict[str, Any],
                          results: List[Dict[str, Any]], gaps: List[str]) -> None:
    _ensure_parent_dir(path)
    lines: List[str] = []
    lines.append("# ISO 27001 Gap Report")
    lines.append("")
    lines.append(f"- Generated: `{meta['generated_at']}`")
    lines.append(f"- Controls file: `{meta['controls']}`")
    lines.append(f"- Implementation file: `{meta['implementation']}`")
    lines.append("")
    lines.append(f"**Summary**: {summary['implemented']}/{summary['total_controls']} implemented, {summary['gaps']} gaps.")
    lines.append("")
    if gaps:
        lines.append("## Gaps")
        for cid in gaps:
            title = next((r["title"] for r in results if r["id"] == cid), "")
            if title:
                lines.append(f"- **{cid}** — {title}")
            else:
                lines.append(f"- **{cid}**")
        lines.append("")
    lines.append("## Full Results")
    lines.append("")
    lines.append("| Control ID | Title | Implemented |")
    lines.append("|---|---|---|")
    for r in results:
        lines.append(f"| {r['id']} | {r['title']} | {'✅' if r['implemented'] else '❌'} |")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------
# CLI
# ---------------------------

def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="ISO 27001 Gap Analyzer")
    ap.add_argument("--controls",
                    required=False,
                    default="iso_27001_controls.json",
                    help="Path to ISO controls JSON (list, map, or object with 'controls').")
    ap.add_argument("--implementation",
                    required=True,
                    help="Path to implemented controls JSON (list, map id->bool, or object with 'controls').")
    ap.add_argument("--out-json",
                    required=False,
                    default="reports/gap_report.json",
                    help="Path to write machine-readable JSON report.")
    ap.add_argument("--out-md",
                    required=False,
                    default="reports/gap_report.md",
                    help="Path to write Markdown report.")
    return ap


def main() -> None:
    ap = build_argparser()
    args = ap.parse_args()

    # Validate input paths early
    for p in [args.controls, args.implementation]:
        if not os.path.exists(p):
            print(f"❌ Error: {p} not found", file=sys.stderr)
            sys.exit(1)

    # Load JSON
    controls_json = _read_json(args.controls)
    impl_json = _read_json(args.implementation)

    # Normalize schemas
    controls_map, controls_ids = load_controls(controls_json)
    implemented_ids, implemented_map = load_implemented(impl_json)

    # Validate
    if not controls_ids:
        print("❌ Error: No controls found in controls file.", file=sys.stderr)
        sys.exit(3)

    # Warn about unknown IDs in implementation
    unknown_impl = sorted(list((set(implemented_map.keys()) | implemented_ids) - set(controls_ids)))
    if unknown_impl:
        print(f"⚠️  Warning: Implementation contains IDs not present in controls: {unknown_impl}", file=sys.stderr)

    # Compute results
    results, summary, gaps = compute_gaps(controls_map, controls_ids, implemented_ids, implemented_map)

    # Meta + outputs
    meta = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "controls": args.controls,
        "implementation": args.implementation,
        "tool": "iso27001-gap-analyzer",
        "version": "1.1.0"
    }

    write_json_report(args.out_json, meta, summary, results, gaps)
    write_markdown_report(args.out_md, meta, summary, results, gaps)

    # Console summary (nice for CI logs)
    print("\n📊 ISO 27001 Gap Analysis Report")
    print("=" * 40)
    print(f"Total Required Controls: {summary['total_controls']}")
    print(f"Controls Implemented:   {summary['implemented']}")
    print(f"Controls Missing:       {summary['gaps']}")
    if gaps:
        print("-" * 40)
        print("❗ Missing Controls (IDs):")
        for cid in gaps:
            print(f"   - {cid}")
    print("=" * 40)
    print(f"Reports written:\n - {args.out_json}\n - {args.out_md}")

    # Successful termination even when gaps exist (gaps are expected)
    sys.exit(0)


if __name__ == "__main__":
    main()
