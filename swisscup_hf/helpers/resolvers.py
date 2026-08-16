class CLIConflictResolver:
    """Handles all command-line user prompts for data cleaning and conflicts."""

    def resolve_name_discrepancy(self, civl_id: str, name: str, key: str, json_val: str, excel_val: str) -> str:
        print(f"\n⚠️ Discrepancy found for civl_id {civl_id} ({name}) in {key.replace('_', ' ').title()}:")
        print(f"  [1] JSON value:  {json_val}")
        print(f"  [2] Excel value: {excel_val}")

        while True:
            choice = input(f"Which value should be kept? (1/2): ").strip()
            if choice == '1': return json_val
            if choice == '2': return excel_val
            print("Invalid input. Please enter 1 or 2.")

    def resolve_glider(self, name: str, old_glider: str, new_glider: str) -> str:
        print(f"\n🪂 Discrepancy in glider found for {name}:")
        print(f"  [1] Old glider (JSON):  {old_glider}")
        print(f"  [2] New glider (Excel): {new_glider}")
        print(f"  [3] Type a custom glider name")

        while True:
            choice = input("Which glider should be used? (1/2/3): ").strip()
            if choice == '1': return old_glider
            if choice == '2': return new_glider
            if choice == '3': return input("Enter custom glider name: ").strip()
            print("Invalid input.")

    def resolve_invalid_gender(self, invalid_gender: str) -> str:
        print(f"\n⚠️ Invalid Gender found: '{invalid_gender}'")
        return input("Please enter a valid gender ('M' or 'F'): ").strip().upper()

    def resolve_invalid_nationality(self, invalid_nat: str, info: str) -> str:
        print(f"\n⚠️ Invalid Nationality length: '{invalid_nat}' for {info}")
        return input("Please enter a valid 3-letter IOC country code (e.g., SUI): ").strip().upper()

    def resolve_duplicate_merge(self, name_title: str, unique_ids: list) -> tuple[bool, str]:
        print(f"\n👯 Possible duplicate: {name_title}")
        print(f"CIVL IDs found: {', '.join(unique_ids)}")

        action = input("Do you want to merge these records? (y/n): ").strip().lower()
        if action == 'y':
            print("Available IDs:", unique_ids)
            target_id = input("Type the exact CIVL ID to KEEP (or press Enter to cancel): ").strip()
            return True, target_id
        return False, ""