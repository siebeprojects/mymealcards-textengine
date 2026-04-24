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

from engine.ast_models import AstCard, AstConcept, AstFieldDefinition, AstTemplate, AstTree
from engine.concept_resolver import ConceptResolver


_FORM_REFERENCE_PATTERN = re.compile(r'\{(\w+)\}')

_DISPLAY_LABEL_FORM_TO_FIELD: dict[str, str] = {
    "noun_plural":   "noun_plural",
    "noun_singular": "noun_singular",
    "attributive":   "attributive",
}


class AstValidator:

    def __init__(self, ast_tree: AstTree, concept_resolver: ConceptResolver):
        self._ast_tree         = ast_tree
        self._concept_resolver = concept_resolver
        self._errors: list[str] = []

    def validate(self) -> None:
        self._errors = []
        self._validate_concept_display_labels()
        self._validate_cards()
        self._validate_ui()
        if self._errors:
            error_lines = "\n".join(f"  - {error}" for error in self._errors)
            raise ValueError(
                f"AST validation failed with {len(self._errors)} error(s):\n{error_lines}"
            )

    # ------------------------------------------------------------------
    # Concept-level checks
    # ------------------------------------------------------------------

    def _validate_concept_display_labels(self) -> None:
        for concept in self._ast_tree.concepts.values():
            if concept.display_label is None:
                continue
            for form_name in _FORM_REFERENCE_PATTERN.findall(concept.display_label):
                field_name = _DISPLAY_LABEL_FORM_TO_FIELD.get(form_name)
                if field_name is None:
                    self._errors.append(
                        f"Concept '{concept.id}' display.label references "
                        f"unknown form '{{{form_name}}}'"
                    )
                    continue
                if getattr(concept, field_name) is None:
                    self._errors.append(
                        f"Concept '{concept.id}' display.label references "
                        f"'{{{form_name}}}' but that form is not set"
                    )

    # ------------------------------------------------------------------
    # Card-level checks
    # ------------------------------------------------------------------

    def _validate_cards(self) -> None:
        for card_id, ast_card in self._ast_tree.cards.items():
            for field_name, field_definition in [
                ("scope",       ast_card.scope),
                ("header",      ast_card.header),
                ("description", ast_card.description),
                ("subheader",   ast_card.subheader),
                ("footer",      ast_card.footer),
            ]:
                self._validate_field(card_id, field_name, field_definition)
            self._validate_examples(card_id, ast_card)

    def _validate_field(
        self,
        card_id:          str,
        field_name:       str,
        field_definition: AstFieldDefinition,
    ) -> None:
        if field_definition.mode != "template":
            return
        if field_definition.template is None:
            self._errors.append(
                f"Card '{card_id}' field '{field_name}' has mode 'template' but no template assigned"
            )
            return
        template    = field_definition.template
        concepts    = field_definition.concepts
        field_label = f"Card '{card_id}' field '{field_name}'"

        for token in template.tokens:
            self._validate_modifier_concept_count(field_label, token.modifier, len(concepts))

        for concept in concepts:
            self._validate_concept_resolution(field_label, concept, template)

    def _validate_modifier_concept_count(
        self,
        field_label:   str,
        modifier:      str,
        concept_count: int,
    ) -> None:
        if modifier == "single" and concept_count != 1:
            self._errors.append(
                f"{field_label}: modifier 'single' requires exactly 1 concept, "
                f"got {concept_count}"
            )
        elif modifier in ("list(and)", "list(or)", "list(neg_all)") and concept_count == 0:
            self._errors.append(
                f"{field_label}: modifier '{modifier}' requires at least 1 concept, got 0"
            )

    def _validate_concept_resolution(
        self,
        field_label: str,
        concept:     AstConcept,
        template:    AstTemplate,
    ) -> None:
        try:
            self._concept_resolver.resolve(concept, template.fallback)
        except ValueError as resolution_error:
            self._errors.append(f"{field_label}: {resolution_error}")

    # ------------------------------------------------------------------
    # UI-level checks
    # ------------------------------------------------------------------

    def _validate_ui(self) -> None:
        language_code = self._ast_tree.language.code
        for element_id, ast_element in self._ast_tree.ui.items():
            if ast_element.localized and not ast_element.value:
                self._errors.append(
                    f"UI element '{element_id}' is marked as localized "
                    f"but has no translation for language '{language_code}'"
                )

    # ------------------------------------------------------------------
    # Example-level checks
    # ------------------------------------------------------------------

    def _validate_examples(self, card_id: str, ast_card: AstCard) -> None:
        example_template = ast_card.examples.template
        for side, concepts in [
            ("left",  ast_card.examples.concepts_left),
            ("right", ast_card.examples.concepts_right),
        ]:
            for concept in concepts:
                self._validate_concept_resolution(
                    f"Card '{card_id}' examples.{side}",
                    concept,
                    example_template,
                )
