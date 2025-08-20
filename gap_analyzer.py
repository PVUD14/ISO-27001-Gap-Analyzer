 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/gap_analyzer.py b/gap_analyzer.py
index 7ca3291acb81fd1169332f4ef95fdedff77e8a09..43b56fc57d4fc8c13a2db0e12a20412271c4d2d0 100644
--- a/gap_analyzer.py
+++ b/gap_analyzer.py
@@ -1 +1,80 @@
-# ISO 27001 Gap Analyzer Placeholder
+"""Simple ISO 27001 gap analysis tool.
+
+This script loads a list of ISO 27001 controls and compares it against
+an organization's implementation data supplied in JSON format. Any
+controls that are missing or not implemented are printed as output.
+
+Usage:
+    python gap_analyzer.py path/to/implementation.json
+
+The implementation JSON file should map control IDs to a boolean value
+indicating whether the control is implemented. Example:
+{
+    "A.5.1.1": true,
+    "A.5.1.2": false
+}
+"""
+from __future__ import annotations
+
+import argparse
+import json
+from typing import Dict, List, Tuple
+
+
+def load_controls(path: str) -> Dict[str, str]:
+    """Load ISO 27001 controls from a JSON file.
+
+    The file is expected to contain a list of objects with ``id`` and
+    ``description`` fields.
+    """
+    with open(path, "r", encoding="utf-8") as handle:
+        data = json.load(handle)
+    return {item["id"]: item["description"] for item in data}
+
+
+def load_implementation(path: str) -> Dict[str, bool]:
+    """Load organization's control implementation data from JSON."""
+    with open(path, "r", encoding="utf-8") as handle:
+        return json.load(handle)
+
+
+def analyze_gap(
+    controls: Dict[str, str], implementation: Dict[str, bool]
+) -> List[Tuple[str, str]]:
+    """Return controls that are missing or not implemented."""
+    missing: List[Tuple[str, str]] = []
+    for control_id, description in controls.items():
+        status = implementation.get(control_id)
+        if not status:
+            missing.append((control_id, description))
+    return missing
+
+
+def main() -> None:
+    parser = argparse.ArgumentParser(description="ISO 27001 Gap Analyzer")
+    parser.add_argument(
+        "implementation",
+        help="JSON file mapping control IDs to implemented status",
+    )
+    parser.add_argument(
+        "-c",
+        "--controls",
+        default="iso_27001_controls.json",
+        help="JSON file containing ISO 27001 controls",
+    )
+    args = parser.parse_args()
+
+    controls = load_controls(args.controls)
+    implementation = load_implementation(args.implementation)
+    missing = analyze_gap(controls, implementation)
+
+    if missing:
+        print("Controls missing or not met:")
+        for control_id, description in missing:
+            print(f"- {control_id}: {description}")
+    else:
+        print("All ISO 27001 controls are implemented.")
+
+
+if __name__ == "__main__":
+    main()
 
EOF
)
