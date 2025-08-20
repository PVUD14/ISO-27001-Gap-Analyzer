import json
import sys
import os

def load_json_file(file_path):
    """Load a JSON file and return its data."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"❌ Error: File not found - {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Failed to parse JSON file {file_path}. Details: {e}")
        sys.exit(1)


def analyze_gaps(required_controls, implemented_controls):
    """Compare implemented controls with required ISO 27001 controls."""
    required_set = set(required_controls)
    implemented_set = set(implemented_controls)

    missing = required_set - implemented_set
    covered = required_set & implemented_set

    return missing, covered


def print_summary(missing, covered, total):
    """Prints the summary of gap analysis results."""
    print("\n📊 ISO 27001 Gap Analysis Report")
    print("=" * 40)
    print(f"Total Required Controls: {total}")
    print(f"Controls Implemented: {len(covered)}")
    print(f"Controls Missing: {len(missing)}")
    print("-" * 40)

    if missing:
        print("❗ Missing Controls:")
        for control in sorted(missing):
            print(f"   - {control}")
    else:
        print("✅ All required controls are implemented.")

    print("=" * 40)


def main():
    if len(sys.argv) != 3:
        print("Usage: python iso_gap_analyzer.py <iso_27001_controls.json> <implemented_controls.json>")
        sys.exit(1)

    iso_file = sys.argv[1]
    implemented_file = sys.argv

    if not os.path.exists(iso_file):
        print(f"❌ Error: {iso_file} not found")
        sys.exit(1)

    if not os.path.exists(implemented_file):
        print(f"❌ Error: {implemented_file} not found")
        sys.exit(1)

    # Load data
    iso_data = load_json_file(iso_file)
    implemented_data = load_json_file(implemented_file)

    # Extract lists
    required_controls = iso_data.get("controls", [])
    implemented_controls = implemented_data.get("controls", [])

    if not isinstance(required_controls, list) or not isinstance(implemented_controls, list):
        print("❌ Error: 'controls' key must contain a list in both JSON files.")
        sys.exit(1)

    # Perform gap analysis
    missing, covered = analyze_gaps(required_controls, implemented_controls)

    # Print summary
    print_summary(missing, covered, len(required_controls))


if __name__ == "__main__":
    main()
