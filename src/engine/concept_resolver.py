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

import re

from engine.ast_models import AstConcept


_FORM_REFERENCE_PATTERN = re.compile(r'\{(\w+)\}')

_FALLBACK_ENTRY_TO_FIELD: dict[str, str] = {
    "forms.noun_plural":   "noun_plural",
    "forms.noun_singular": "noun_singular",
    "forms.attributive":   "attributive",
}

_DISPLAY_LABEL_FORM_TO_FIELD: dict[str, str] = {
    "noun_plural":   "noun_plural",
    "noun_singular": "noun_singular",
    "attributive":   "attributive",
}


class ConceptResolver:

    def resolve(self, concept: AstConcept, fallback_chain: list[str]) -> str:
        for fallback_entry in fallback_chain:
            resolved_value = self._resolve_entry(concept, fallback_entry)
            if resolved_value is not None:
                return resolved_value
        raise ValueError(
            f"Concept '{concept.id}' has no value for any entry "
            f"in fallback chain: {fallback_chain}"
        )

    def _resolve_entry(self, concept: AstConcept, fallback_entry: str) -> str | None:
        if fallback_entry == "display.label":
            return self._resolve_display_label(concept)
        field_name = _FALLBACK_ENTRY_TO_FIELD.get(fallback_entry)
        if field_name is None:
            raise ValueError(f"Unknown fallback entry: '{fallback_entry}'")
        return getattr(concept, field_name)

    def _resolve_display_label(self, concept: AstConcept) -> str | None:
        display_label = concept.display_label
        if display_label is None:
            return None
        form_names = _FORM_REFERENCE_PATTERN.findall(display_label)
        if not form_names:
            return display_label
        resolved = display_label
        for form_name in form_names:
            field_name = _DISPLAY_LABEL_FORM_TO_FIELD.get(form_name)
            if field_name is None:
                raise ValueError(
                    f"Concept '{concept.id}' display.label references "
                    f"unknown form '{{{form_name}}}'"
                )
            form_value = getattr(concept, field_name)
            if form_value is None:
                return None
            resolved = resolved.replace(f'{{{form_name}}}', form_value)
        return resolved
