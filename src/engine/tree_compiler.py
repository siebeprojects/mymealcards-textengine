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

from engine.ast_models import AstFieldDefinition, AstTree
from engine.models import Card, CardGroup, Language, MedicalType, Product, Tree, UIElement
from engine.language_renderer import LanguageRenderer


class TreeCompiler:

    def __init__(self, ast_tree: AstTree, renderer: LanguageRenderer):
        self._ast_tree = ast_tree
        self._renderer = renderer

    def compile(self) -> Tree:
        language      = self._compile_language()
        medical_types = self._compile_medical_types()
        card_groups   = self._compile_card_groups(medical_types)
        cards         = self._compile_cards(card_groups, medical_types)
        products      = self._compile_products(cards)
        ui            = self._compile_ui()

        return Tree(
            language=language,
            medical_types=medical_types,
            card_groups=card_groups,
            cards=cards,
            products=products,
            ui=ui,
        )

    # ------------------------------------------------------------------
    # Private compilers
    # ------------------------------------------------------------------

    def _compile_language(self) -> Language:
        ast_language = self._ast_tree.language
        return Language(
            code=ast_language.code,
            name=ast_language.name,
            direction=ast_language.direction,
            label=ast_language.label,
        )

    def _compile_medical_types(self) -> dict[str, MedicalType]:
        medical_types = {}
        for medicaltype_id, ast_medical_type in self._ast_tree.medical_types.items():
            medical_types[medicaltype_id] = MedicalType(
                id=medicaltype_id,
                singular=self._renderer.capitalize_label(ast_medical_type.singular),
                plural=self._renderer.capitalize_label(ast_medical_type.plural),
            )
        return medical_types

    def _compile_card_groups(self, medical_types: dict[str, MedicalType]) -> dict[str, CardGroup]:
        card_groups = {}
        for cardgroup_id, ast_card_group in self._ast_tree.card_groups.items():
            medicaltype = medical_types[ast_card_group.medicaltype.id]
            card_groups[cardgroup_id] = CardGroup(
                id=cardgroup_id,
                label=self._renderer.capitalize_label(medicaltype.singular),
                medicaltype=medicaltype,
            )
        return card_groups

    def _render_field(self, field_definition: AstFieldDefinition) -> str:
        if field_definition.mode == "static":
            return field_definition.static_value or ""
        return self._renderer.render(field_definition.template, field_definition.concepts)

    def _compile_cards(
        self,
        card_groups:   dict[str, CardGroup],
        medical_types: dict[str, MedicalType],
    ) -> dict[str, Card]:
        cards = {}
        for card_id, ast_card in self._ast_tree.cards.items():
            effective_medicaltype = medical_types[ast_card.effective_medicaltype().id]
            card_group            = card_groups[ast_card.cardgroup.id]

            language_code = self._ast_tree.language.code.upper()
            cards[card_id] = Card(
                id=card_id,
                cardid=f"{ast_card.cardid}-{language_code}",
                cardgroup=card_group,
                medicaltype=effective_medicaltype,
                scope=self._render_field(ast_card.scope),
                header=self._render_field(ast_card.header),
                description=self._render_field(ast_card.description),
                subheader=self._render_field(ast_card.subheader),
                footer=self._render_field(ast_card.footer),
                examples_left=[
                    self._renderer.render(ast_card.examples.template, [concept])
                    for concept in ast_card.examples.concepts_left
                ],
                examples_right=[
                    self._renderer.render(ast_card.examples.template, [concept])
                    for concept in ast_card.examples.concepts_right
                ],
            )
        return cards

    def _compile_products(self, cards: dict[str, Card]) -> dict[str, Product]:
        products = {}
        for product_id, ast_product in self._ast_tree.products.items():
            products[product_id] = Product(
                id=product_id,
                card=cards[ast_product.card.id],
                label=ast_product.label,
                label_pdf=ast_product.label_pdf,
            )
        return products

    def _compile_ui(self) -> dict[str, UIElement]:
        ui = {}
        for element_id, ast_element in self._ast_tree.ui.items():
            ui[element_id] = UIElement(
                id=element_id,
                value=ast_element.value,
                localized=ast_element.localized,
            )
        return ui
