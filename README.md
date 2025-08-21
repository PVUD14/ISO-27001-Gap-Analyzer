# ISO-27001 Gap Analyzer

A simple ISO 27001 Gap Analyzer that checks an organization’s implemented controls against the ISO 27001 control set.  
The tool supports multiple JSON input formats, runs locally or via GitHub Actions, and generates both human-readable (Markdown) and machine-readable (JSON) reports.

---

## Features
- Accepts flexible JSON schemas for both required controls and implementation status.
- Produces:
  - 📄 **Markdown report** (`reports/gap_report.md`)  
  - 🗄️ **JSON report** (`reports/gap_report.json`)
- Clean CLI with explicit input/output flags.
- CI-friendly: warnings for unknown IDs, non-zero exit only on errors (not on gaps).
- Automated with GitHub Actions to generate reports on push or manual trigger.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/PVUD14/ISO-27001-Gap-Analyzer.git
cd ISO-27001-Gap-Analyzer
