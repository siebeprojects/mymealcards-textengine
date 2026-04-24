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

from engine.ast_models import (
    AstCard, AstCardGroup, AstConcept, AstExamples, AstFieldDefinition,
    AstLanguage, AstMedicalType, AstProduct, AstTemplate, AstTree, AstUIElement,
)
from engine.data_loader import RawData
from engine.language_renderer import parse_template_tokens


class Parser:

    def __init__(self, raw_data: RawData, language_code: str):
        self._raw           = raw_data
        self._language_code = language_code

    def build(self) -> AstTree:
        language      = self._build_language()
        medical_types = self._build_medical_types()
        card_groups   = self._build_card_groups(medical_types)
        concepts      = self._build_concepts()
        templates     = self._build_templates()
        cards         = self._build_cards(card_groups, medical_types, concepts, templates)
        products      = self._build_products(cards)
        ui            = self._build_ui()

        return AstTree(
            language=language,
            medical_types=medical_types,
            card_groups=card_groups,
            concepts=concepts,
            templates=templates,
            cards=cards,
            products=products,
            ui=ui,
        )

    # ------------------------------------------------------------------
    # Private builders
    # ------------------------------------------------------------------

    def _build_language(self) -> AstLanguage:
        core_entry = self._raw.languages.core[self._language_code]
        lang_data  = self._raw.languages.langs.get(self._language_code, {})
        lang_entry = lang_data.get(self._language_code, {})
        return AstLanguage(
            code=self._language_code,
            name=core_entry["name"],
            direction=core_entry["direction"],
            label=lang_entry.get("label", self._language_code),
        )

    def _build_medical_types(self) -> dict[str, AstMedicalType]:
        lang_data     = self._raw.medicaltypes.langs.get(self._language_code, {})
        medical_types = {}
        for medicaltype_id in self._raw.medicaltypes.core:
            lang_entry = lang_data.get(medicaltype_id, {})
            forms      = lang_entry.get("forms", {})
            medical_types[medicaltype_id] = AstMedicalType(
                id=medicaltype_id,
                singular=forms.get("singular", medicaltype_id),
                plural=forms.get("plural", medicaltype_id),
            )
        return medical_types

    def _build_card_groups(self, medical_types: dict[str, AstMedicalType]) -> dict[str, AstCardGroup]:
        card_groups = {}
        for cardgroup_id, cardgroup_data in self._raw.cardgroups.core.items():
            medicaltype_id = cardgroup_data["medicaltype"]
            card_groups[cardgroup_id] = AstCardGroup(
                id=cardgroup_id,
                medicaltype=medical_types[medicaltype_id],
            )
        return card_groups

    def _build_concepts(self) -> dict[str, AstConcept]:
        lang_data       = self._raw.concepts.langs.get(self._language_code, {})
        all_concept_ids = sorted(set(self._raw.concepts.core.keys()) | set(lang_data.keys()))
        concepts        = {}
        for concept_id in all_concept_ids:
            lang_entry = lang_data.get(concept_id, {})
            forms      = lang_entry.get("forms", {})
            display    = lang_entry.get("display", {})
            concepts[concept_id] = AstConcept(
                id=concept_id,
                noun_singular=forms.get("noun_singular"),
                noun_plural=forms.get("noun_plural"),
                attributive=forms.get("attributive"),
                display_label=display.get("label"),
                gender=lang_entry.get("gender"),
            )
        return concepts

    def _build_templates(self) -> dict[str, AstTemplate]:
        lang_data        = self._raw.templates.langs.get(self._language_code, {})
        all_template_ids = sorted(set(self._raw.templates.core.keys()) | set(lang_data.keys()))
        templates        = {}
        for template_id in all_template_ids:
            core_entry      = self._raw.templates.core.get(template_id, {})
            lang_entry      = lang_data.get(template_id, {})
            template_string = lang_entry.get("template", "")
            templates[template_id] = AstTemplate(
                id=template_id,
                type=core_entry.get("type", ""),
                args=core_entry.get("args", []),
                fallback=core_entry.get("fallback", []),
                template_string=template_string,
                tokens=parse_template_tokens(template_string),
            )
        return templates

    def _build_field_definition(
        self,
        card_id:        str,
        field_name:     str,
        field_data:     dict,
        lang_card_data: dict,
        concepts:       dict[str, AstConcept],
        templates:      dict[str, AstTemplate],
    ) -> AstFieldDefinition:
        mode = field_data["mode"]

        if mode == "static":
            static_value = lang_card_data.get(field_name) if lang_card_data else None
            return AstFieldDefinition(mode="static", template=None, concepts=[], static_value=static_value)

        if mode == "template":
            template_key   = field_data["template_key"]
            concept_ids    = field_data.get("concepts", [])
            template       = templates[template_key]
            field_concepts = [concepts[concept_id] for concept_id in concept_ids]
            return AstFieldDefinition(mode="template", template=template, concepts=field_concepts)

        raise ValueError(f"Unknown field mode '{mode}' in card '{card_id}' field '{field_name}'")

    def _validate_concept_references(
        self,
        concepts: dict[str, AstConcept],
    ) -> None:
        errors = []
        field_names = ("scope", "header", "description", "subheader", "footer")
        for card_id, card_data in self._raw.cards.core.items():
            for field_name in field_names:
                field_data = card_data.get(field_name, {})
                if field_data.get("mode") == "template":
                    for concept_id in field_data.get("concepts", []):
                        if concept_id not in concepts:
                            errors.append(
                                f"Card '{card_id}' field '{field_name}': "
                                f"concept '{concept_id}' not found"
                            )
            examples_data = card_data.get("examples", {})
            for side in ("concepts_left", "concepts_right"):
                for concept_id in examples_data.get(side, []):
                    if concept_id not in concepts:
                        errors.append(
                            f"Card '{card_id}' examples.{side.replace('concepts_', '')}: "
                            f"concept '{concept_id}' not found"
                        )
        if errors:
            error_lines = "\n".join(f"  - {error}" for error in errors)
            raise ValueError(
                f"Cards reference {len(errors)} unknown concept(s):\n{error_lines}"
            )

    def _validate_template_references(
        self,
        templates: dict[str, AstTemplate],
    ) -> None:
        errors = []
        field_names = ("scope", "header", "description", "subheader", "footer")
        for card_id, card_data in self._raw.cards.core.items():
            for field_name in field_names:
                field_data = card_data.get(field_name, {})
                if field_data.get("mode") == "template":
                    template_key = field_data.get("template_key")
                    if template_key not in templates:
                        errors.append(
                            f"Card '{card_id}' field '{field_name}': "
                            f"template '{template_key}' not found"
                        )
            examples_data = card_data.get("examples", {})
            template_key  = examples_data.get("template_key")
            if template_key and template_key not in templates:
                errors.append(
                    f"Card '{card_id}' examples: template '{template_key}' not found"
                )
        if errors:
            error_lines = "\n".join(f"  - {error}" for error in errors)
            raise ValueError(
                f"Cards reference {len(errors)} unknown template(s):\n{error_lines}"
            )

    def _build_cards(
        self,
        card_groups:   dict[str, AstCardGroup],
        medical_types: dict[str, AstMedicalType],
        concepts:      dict[str, AstConcept],
        templates:     dict[str, AstTemplate],
    ) -> dict[str, AstCard]:
        self._validate_template_references(templates)
        self._validate_concept_references(concepts)
        lang_data = self._raw.cards.langs.get(self._language_code, {})
        cards     = {}

        for card_id, card_data in self._raw.cards.core.items():
            lang_card_data       = lang_data.get(card_id, {})
            card_group           = card_groups[card_data["cardgroup"]]
            medicaltype_override = (
                medical_types[card_data["medicaltype"]]
                if "medicaltype" in card_data
                else None
            )
            examples_data     = card_data["examples"]
            examples_template = templates[examples_data["template_key"]]
            concepts_left     = [concepts[cid] for cid in examples_data.get("concepts_left", [])]
            concepts_right    = [concepts[cid] for cid in examples_data.get("concepts_right", [])]

            cards[card_id] = AstCard(
                id=card_id,
                cardid=card_data["cardid"],
                cardgroup=card_group,
                medicaltype_override=medicaltype_override,
                scope=self._build_field_definition(
                    card_id, "scope", card_data["scope"], lang_card_data, concepts, templates
                ),
                header=self._build_field_definition(
                    card_id, "header", card_data["header"], lang_card_data, concepts, templates
                ),
                description=self._build_field_definition(
                    card_id, "description", card_data["description"], lang_card_data, concepts, templates
                ),
                subheader=self._build_field_definition(
                    card_id, "subheader", card_data["subheader"], lang_card_data, concepts, templates
                ),
                examples=AstExamples(
                    template=examples_template,
                    concepts_left=concepts_left,
                    concepts_right=concepts_right,
                ),
                footer=self._build_field_definition(
                    card_id, "footer", card_data["footer"], lang_card_data, concepts, templates
                ),
            )

        return cards

    def _build_products(self, cards: dict[str, AstCard]) -> dict[str, AstProduct]:
        lang_data = self._raw.products.langs.get(self._language_code, {})
        products  = {}
        for product_id, product_data in self._raw.products.core.items():
            card_id    = product_data["card"]
            lang_entry = lang_data.get(product_id, {})
            products[product_id] = AstProduct(
                id=product_id,
                card=cards[card_id],
                label=lang_entry.get("label", ""),
                label_pdf=lang_entry.get("label-pdf", ""),
            )
        return products

    def _build_ui(self) -> dict[str, AstUIElement]:
        lang_data = self._raw.ui.langs.get(self._language_code, {})
        ui        = {}
        for element_id, element_data in self._raw.ui.core.items():
            is_localized = element_data.get("localized", False)
            if is_localized:
                lang_entry = lang_data.get(element_id, {})
                value      = lang_entry.get("label", "")
            else:
                value = element_data.get("value", "")
            ui[element_id] = AstUIElement(
                id=element_id,
                value=value,
                localized=is_localized,
            )
        return ui
