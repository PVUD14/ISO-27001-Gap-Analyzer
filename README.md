diff --git a/README.md b/README.md
index 16e3ad51bb7b933b302eeb737cc95af9ee4911ba..433b106b7662790ef0b41f1f57e46bb1ab70a2ee 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,15 @@
 # ISO-27001-Gap-Analyzer
 A simple ISO 27001 Gap Analyzer tool that automatically checks provided input against ISO 27001 requirements. This project is automated using GitHub Actions to generate compliance gap reports based on the given scope
+
+## Usage
+
+1. Prepare a JSON file that maps ISO 27001 control IDs to a boolean value indicating whether each control is implemented.
+2. Run the analyzer, optionally specifying a custom controls file:
+
+```bash
+python gap_analyzer.py path/to/implementation.json
+```
+
+The script compares the supplied implementation data against the controls
+listed in `iso_27001_controls.json` and prints any controls that are
+missing or not met.
