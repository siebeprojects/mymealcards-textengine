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

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema


@dataclass
class RawDataType:
    core:  dict
    langs: dict[str, dict] = field(default_factory=dict)  # language_code -> data


@dataclass
class RawData:
    cardgroups:   RawDataType
    cards:        RawDataType
    concepts:     RawDataType
    languages:    RawDataType
    medicaltypes: RawDataType
    products:     RawDataType
    templates:    RawDataType
    ui:           RawDataType


class DataLoader:
    def __init__(self, data_path: Path, schemas_path: Path):
        self._data    = Path(data_path)
        self._schemas = Path(schemas_path)

    def load(self) -> RawData:
        languages_core = self._load_validated("languages.core.json", "languages.core.schema.json")
        language_codes = list(languages_core.keys())

        return RawData(
            cardgroups=  self._load_data_type("cardgroups",   language_codes),
            cards=       self._load_data_type("cards",        language_codes),
            concepts=    self._load_data_type("concepts",     language_codes),
            languages=   self._load_data_type("languages",    language_codes, core=languages_core),
            medicaltypes=self._load_data_type("medicaltypes", language_codes),
            products=    self._load_data_type("products",     language_codes),
            templates=   self._load_data_type("templates",    language_codes),
            ui=          self._load_data_type("ui",           language_codes),
        )

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _load_data_type(self, name: str, language_codes: list[str], core: dict | None = None) -> RawDataType:
        if core is None:
            core = self._load_validated(f"{name}.core.json", f"{name}.core.schema.json")

        langs = {}
        for language_code in language_codes:
            file_path = self._data / name / f"{name}.{language_code}.json"
            if file_path.exists():
                langs[language_code] = self._load_validated(
                    f"{name}/{name}.{language_code}.json",
                    f"{name}.lang.schema.json",
                )

        return RawDataType(core=core, langs=langs)

    def _load_validated(self, data_rel: str, schema_rel: str) -> dict:
        data_path   = self._data    / data_rel
        schema_path = self._schemas / schema_rel
        data   = json.loads(data_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as error:
            raise ValueError(f"Schema validation failed for {data_path.name}: {error.message}") from error
        return data
