import json
from pathlib import Path

def validate_full_summary(file_path: Path) -> bool:
    required_keys = [
        "module", "description", "frontend", "backend",
        "dependencies", "events", "test"
    ]
    try:
        with open(file_path) as f:
            data = json.load(f)

        for key in required_keys:
            if key not in data:
                print(f"❌ Missing required field: {key}")
                return False

        # Check frontend/backend structure
        for section in ["frontend", "backend"]:
            if not isinstance(data.get(section), dict):
                print(f"❌ {section} should be a dict")
                return False

        print("✅ Validation passed.")
        return True
    except Exception as e:
        print(f"❌ Error validating {file_path.name}: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python validate_full_summary.py path/to/full_summary.json")
    else:
        validate_full_summary(Path(sys.argv[1]))