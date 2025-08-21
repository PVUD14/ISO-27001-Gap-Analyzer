# Samples

This folder contains example input files for the ISO 27001 Gap Analyzer.

- `iso_27001_controls.json` → Example set of ISO controls with titles.
- `implemented_controls.json` → Example implementation map (true/false).

These are used in:
- Local testing (`python gap_analyzer.py --implementation samples/implemented_controls.json --controls samples/iso_27001_controls.json`)
- GitHub Actions demo runs, so the CI pipeline always generates a baseline report.
