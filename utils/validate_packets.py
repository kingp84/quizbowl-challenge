import os
import json

def check_clue_order(tossup):
    """Ensure hard → medium → easy clue order is present and not missing."""
    errors = []
    diff = tossup.get("difficulty", {})
    if not diff.get("hard") or diff["hard"] == "MISSING":
        errors.append("Missing hard clue")
    if not diff.get("medium") or diff["medium"] == "MISSING":
        errors.append("Missing medium clue")
    if not diff.get("easy") or diff["easy"] == "MISSING":
        errors.append("Missing easy clue")
    return errors

def validate_naqt(packet_path):
    with open(packet_path, encoding="utf-8") as f:
        data = json.load(f)
    tossups = [q for q in data["questions"] if q["type"] == "tossup"]
    bonuses = [q for q in data["questions"] if q["type"] == "bonus"]

    errors = []
    if len(tossups) != 20:
        errors.append(f"Expected 20 tossups, found {len(tossups)}")
    if len(bonuses) != 3:
        errors.append(f"Expected 3 bonuses, found {len(bonuses)}")

    for i, t in enumerate(tossups, start=1):
        clue_errors = check_clue_order(t)
        if clue_errors:
            errors.append(f"Tossup {i}: {clue_errors}")

    return errors

def validate_ossaa(packet_path, quarter):
    with open(packet_path, encoding="utf-8") as f:
        data = json.load(f)
    tossups = [q for q in data["questions"] if q["type"] == "tossup"]
    sixty = [q for q in data["questions"] if data["type"] == "sixty_second"]

    errors = []
    if quarter in [1, 3]:  # 20 tossups
        if len(tossups) != 20:
            errors.append(f"Quarter {quarter}: Expected 20 tossups, found {len(tossups)}")
        for i, t in enumerate(tossups, start=1):
            clue_errors = check_clue_order(t)
            if clue_errors:
                errors.append(f"Quarter {quarter} Tossup {i}: {clue_errors}")
    elif quarter in [2, 4]:  # 3 sets of 10 sixty-second
        if len(sixty) != 30:
            errors.append(f"Quarter {quarter}: Expected 30 sixty-second questions, found {len(sixty)}")

    return errors

def validate_froshmore(packet_path):
    with open(packet_path, encoding="utf-8") as f:
        data = json.load(f)
    tossups = [q for q in data["questions"] if q["type"] == "tossup"]
    bonuses = [q for q in data["questions"] if q["type"] == "bonus"]

    errors = []
    if len(tossups) != 24:
        errors.append(f"Expected 24 tossups, found {len(tossups)}")
    if len(bonuses) != 24:
        errors.append(f"Expected 24 bonuses, found {len(bonuses)}")

    # Check 1-to-1 mapping
    if len(tossups) != len(bonuses):
        errors.append("Mismatch: tossups and bonuses should be paired 1-to-1")

    for i, t in enumerate(tossups, start=1):
        clue_errors = check_clue_order(t)
        if clue_errors:
            errors.append(f"Tossup {i}: {clue_errors}")

    return errors

def run_validation():
    base = "packets"

    print("Validating NAQT...")
    for filename in os.listdir(os.path.join(base, "NAQT")):
        if filename.endswith(".json"):
            errors = validate_naqt(os.path.join(base, "NAQT", filename))
            if errors:
                print(f"{filename}: FAIL → {errors}")
            else:
                print(f"{filename}: PASS")

    print("\nValidating OSSAA...")
    for filename in os.listdir(os.path.join(base, "OSSAA")):
        if filename.endswith(".json"):
            # Infer quarter from filename
            if "Q1" in filename or "Quarter1" in filename:
                quarter = 1
            elif "Q2" in filename or "Quarter2" in filename:
                quarter = 2
            elif "Q3" in filename or "Quarter3" in filename:
                quarter = 3
            elif "Q4" in filename or "Quarter4" in filename:
                quarter = 4
            else:
                quarter = None

            if quarter:
                errors = validate_ossaa(os.path.join(base, "OSSAA", filename), quarter)
                if errors:
                    print(f"{filename}: FAIL → {errors}")
                else:
                    print(f"{filename}: PASS")
            else:
                print(f"{filename}: Skipped (quarter not detected)")

    print("\nValidating Froshmore...")
    for filename in os.listdir(os.path.join(base, "Froshmore")):
        if filename.endswith(".json"):
            errors = validate_froshmore(os.path.join(base, "Froshmore", filename))
            if errors:
                print(f"{filename}: FAIL → {errors}")
            else:
                print(f"{filename}: PASS")

if __name__ == "__main__":
    run_validation()