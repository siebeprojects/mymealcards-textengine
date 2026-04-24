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

from engine.ast_models import AstConcept, AstTemplate
from engine.language_renderer import LanguageRenderer
from languages.en.grammar import LIST_CONNECTORS, NEG_ALL_SEPARATOR


class EnglishLanguageRenderer(LanguageRenderer):

    def render(self, template: AstTemplate, concepts: list[AstConcept]) -> str:
        result = template.template_string
        for token in template.tokens:
            values = [
                self._concept_resolver.resolve(concept, template.fallback)
                for concept in concepts
            ]
            resolved = self._apply_modifier(values, token.modifier, self._join)
            result = result.replace(token.placeholder, resolved, 1)
        if template.type == "header":
            return self._title_case(result)
        return result[0].upper() + result[1:] if result else result

    def capitalize_label(self, text: str) -> str:
        return self._title_case(text)

    def _title_case(self, text: str) -> str:
        lowercase_words = {"and", "or"}
        words = text.split(" ")
        return " ".join(
            word if (index > 0 and word.lower() in lowercase_words)
            else word[0].upper() + word[1:] if word else word
            for index, word in enumerate(words)
        )

    def _join(self, values: list[str], list_type: str) -> str:
        if not values:
            return ""

        if list_type == "neg_all":
            if len(values) == 1:
                return values[0]
            return values[0] + "".join(f"{NEG_ALL_SEPARATOR}{value}" for value in values[1:])

        connector = LIST_CONNECTORS[list_type]
        if len(values) == 1:
            return values[0]
        if len(values) == 2:
            return f"{values[0]} {connector} {values[1]}"
        return ", ".join(values[:-1]) + f", {connector} {values[-1]}"
