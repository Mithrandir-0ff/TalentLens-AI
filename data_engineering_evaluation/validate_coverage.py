import json

def validate_coverage(dataset_path="data_engineering_evaluation/dataset.json"):
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    examples = data["examples"]

    print(f"Total examples: {len(examples)}\n")
    
    scenarios = set(e["scenario"] for e in examples)
    print("Scenarios covered:")
    for s in scenarios:
        print(f"  {s}")
    print()


    positions = set(e["position"] for e in examples)
    print("Positions covered:")
    for p in positions:
        print(f"  {p}")
    print()


    leagues = set(e["league"] for e in examples)
    print("Leagues covered:")
    for l in leagues:
        print(f"  {l}")
    print()


    complexities = set(e["complexity"] for e in examples)
    print("Complexity levels covered:")
    for c in complexities:
        print(f"  {c}")
    print()

    age_groups = set(e["age_group"] for e in examples)
    print("Age groups covered:")
    for a in age_groups:
        print(f"  {a}")
    print()


if __name__ == "__main__":
    validate_coverage()