# Copyright (c) 2026 Siebe Projects Oy
#
# All rights reserved.
#
# This source code is proprietary and provided for viewing and evaluation
# purposes only. No permission is granted to use, copy, modify, distribute,
# deploy, or otherwise exploit this code without prior written authorization
# from Siebe Projects Oy.
#
# THIS CODE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS
# OR IMPLIED.

import json
import sys
from pathlib import Path


ROOT              = Path(__file__).parent.parent.parent
CARDS_CORE_PATH   = ROOT / "src" / "data" / "cards.core.json"
CONCEPTS_CORE_PATH = ROOT / "src" / "data" / "concepts.core.json"

FILENAME_TO_CARDGROUP: dict[str, str] = {
    "foodallergies": "cardgroup0",
    "intolerances":  "cardgroup1",
}

CARDGROUP_CONFIGS: dict[str, dict[str, object]] = {
    "cardgroup0": {
        "header_template_key":      "header_type0",
        "description_template_key": "statement_type0",
        "subheader_template_key":   "question_type0",
        "footer_template_key":      "footer_type2",
    },
    "cardgroup1": {
        "header_template_key":      "header_type1",
        "description_template_key": "statement_type0",
        "subheader_template_key":   "question_type0",
        "footer_template_key":      "footer_type1",
    },
}


class CardImporter:
    def __init__(self, list_file_path: Path | str) -> None:
        self.list_file_path = Path(list_file_path)
        self.cardgroup      = self._infer_cardgroup()
        self.config         = CARDGROUP_CONFIGS[self.cardgroup]
        self.cards_core     = self._load_json(CARDS_CORE_PATH)
        self.concepts_core  = self._load_json(CONCEPTS_CORE_PATH)

    def _load_json(self, path: Path) -> dict:
        with path.open(encoding="utf-8") as file:
            return json.load(file)

    def _save_json(self, path: Path, data: dict) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
            file.write("\n")

    def _infer_cardgroup(self) -> str:
        prefix = self.list_file_path.stem.split("-")[0]
        if prefix not in FILENAME_TO_CARDGROUP:
            raise ValueError(
                f"Cannot infer cardgroup from filename '{self.list_file_path.name}'. "
                f"Expected prefix: {list(FILENAME_TO_CARDGROUP.keys())}"
            )
        return FILENAME_TO_CARDGROUP[prefix]

    def _build_card(self, card_id: str, concepts: list[str]) -> dict:
        config = self.config

        description = (
            {"mode": "static"}
            if config.get("description_static")
            else {
                "mode": "template",
                "template_key": config["description_template_key"],
                "concepts": concepts,
            }
        )

        subheader = (
            {"mode": "static"}
            if config.get("subheader_static")
            else {
                "mode": "template",
                "template_key": config["subheader_template_key"],
                "concepts": concepts,
            }
        )

        return {
            "cardid": card_id,
            "cardgroup": self.cardgroup,
            "scope": {
                "mode": "template",
                "template_key": "header_list",
                "concepts": concepts,
            },
            "header": {
                "mode": "template",
                "template_key": config["header_template_key"],
                "concepts": concepts,
            },
            "description": description,
            "subheader": subheader,
            "examples": {
                "mode": "template",
                "template_key": "example_item",
                "concepts_left": concepts,
                "concepts_right": [],
            },
            "footer": {
                "mode": "template",
                "template_key": config["footer_template_key"],
            },
        }

    def _ensure_concepts_exist(self, concepts: list[str]) -> list[str]:
        new_concepts = []
        for concept in concepts:
            if concept not in self.concepts_core:
                self.concepts_core[concept] = {}
                new_concepts.append(concept)
        return new_concepts

    def run(self) -> None:
        entries = self._load_json(self.list_file_path)

        added_cards      = []
        skipped_cards    = []
        all_new_concepts = []

        for entry in entries:
            card_key = entry["key"]

            if card_key in self.cards_core:
                skipped_cards.append(card_key)
                continue

            new_concepts = self._ensure_concepts_exist(entry["concepts"])
            all_new_concepts.extend(new_concepts)

            self.cards_core[card_key] = self._build_card(entry["id"], entry["concepts"])
            added_cards.append(card_key)

        self._save_json(CARDS_CORE_PATH, self.cards_core)
        if all_new_concepts:
            self._save_json(CONCEPTS_CORE_PATH, self.concepts_core)

        print(f"Cards added:    {len(added_cards)}")
        print(f"Cards skipped:  {len(skipped_cards)} (already exist)")
        print(f"Concepts added: {len(all_new_concepts)}")

        if added_cards:
            print("\nAdded cards:")
            for card_key in added_cards:
                print(f"  {card_key}")

        if all_new_concepts:
            print("\nNew concepts created:")
            for concept in all_new_concepts:
                print(f"  {concept}")

        if skipped_cards:
            print("\nSkipped (already exist):")
            for card_key in skipped_cards:
                print(f"  {card_key}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_cards.py <list-file-path>")
        sys.exit(1)

    CardImporter(sys.argv[1]).run()
