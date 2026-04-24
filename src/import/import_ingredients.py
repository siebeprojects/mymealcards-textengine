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
from pathlib import Path


ROOT           = Path(__file__).parent.parent.parent
LOCALE_EN      = ROOT / "locales" / "en.json"
CONCEPTS_CORE  = ROOT / "src" / "data" / "concepts.core.json"
CONCEPTS_EN    = ROOT / "src" / "data" / "concepts" / "concepts.en.json"


class IngredientImporter:
    def __init__(self) -> None:
        self.locale_data:   dict = self._load_json(LOCALE_EN)
        self.concepts_core: dict = self._load_json(CONCEPTS_CORE)
        self.concepts_en:   dict = self._load_json(CONCEPTS_EN)

    def _load_json(self, path: Path) -> dict:
        with path.open(encoding="utf-8") as file:
            return json.load(file)

    def _save_json(self, path: Path, data: dict) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
            file.write("\n")

    def _extract_ingredients(self) -> dict[str, str]:
        prefix = "ingredient."
        return {
            key[len(prefix):]: value
            for key, value in self.locale_data.items()
            if key.startswith(prefix)
        }

    def run(self) -> None:
        ingredients = self._extract_ingredients()

        added_to_core = []
        updated_in_en = []
        added_to_en   = []

        for ingredient_id, noun_singular in ingredients.items():
            if ingredient_id not in self.concepts_core:
                self.concepts_core[ingredient_id] = {}
                added_to_core.append(ingredient_id)

            if ingredient_id in self.concepts_en:
                existing_noun_singular = (
                    self.concepts_en[ingredient_id]
                    .get("forms", {})
                    .get("noun_singular")
                )
                if existing_noun_singular != noun_singular:
                    self.concepts_en[ingredient_id].setdefault("forms", {})
                    self.concepts_en[ingredient_id]["forms"]["noun_singular"] = noun_singular
                    updated_in_en.append(ingredient_id)
            else:
                self.concepts_en[ingredient_id] = {
                    "forms": {
                        "noun_singular": noun_singular
                    }
                }
                added_to_en.append(ingredient_id)

        self._save_json(CONCEPTS_CORE, self.concepts_core)
        self._save_json(CONCEPTS_EN, self.concepts_en)

        print(f"Added to concepts.core.json:  {len(added_to_core)}")
        print(f"Added to concepts.en.json:    {len(added_to_en)}")
        print(f"Updated in concepts.en.json:  {len(updated_in_en)}")

        if added_to_core:
            print("\nNew core concepts:")
            for concept_id in added_to_core:
                print(f"  {concept_id}")

        if updated_in_en:
            print("\nUpdated noun_singular in en:")
            for concept_id in updated_in_en:
                print(f"  {concept_id}")


if __name__ == "__main__":
    IngredientImporter().run()
