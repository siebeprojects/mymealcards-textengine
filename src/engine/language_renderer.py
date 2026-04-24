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

import re
from abc import ABC, abstractmethod
from collections.abc import Callable

from engine.ast_models import AstConcept, AstTemplate, AstTemplateToken
from engine.concept_resolver import ConceptResolver


_TOKEN_PATTERN = re.compile(r'\{([^}]+)\}')


def parse_template_tokens(template_string: str) -> list[AstTemplateToken]:
    tokens = []
    for match in _TOKEN_PATTERN.finditer(template_string):
        tokens.append(_parse_token(match.group(0), match.group(1)))
    return tokens


def _parse_token(placeholder: str, content: str) -> AstTemplateToken:
    parts = content.split(":")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid DSL token '{placeholder}': expected {{concepts:modifier}}"
        )
    subject, modifier = parts
    if subject != "concepts":
        raise ValueError(
            f"Invalid DSL token '{placeholder}': subject must be 'concepts', got '{subject}'"
        )
    return AstTemplateToken(
        modifier=modifier,
        placeholder=placeholder,
    )


class LanguageRenderer(ABC):

    def __init__(self, concept_resolver: ConceptResolver):
        self._concept_resolver = concept_resolver

    @abstractmethod
    def render(self, template: AstTemplate, concepts: list[AstConcept]) -> str:
        """Render an AstTemplate with the given AstConcepts into a final string."""

    def capitalize_label(self, text: str) -> str:
        """Capitalize a label string. Override in language renderers for language-specific rules."""
        return text[0].upper() + text[1:] if text else text

    def _apply_modifier(self, values: list[str], modifier: str, join_fn: Callable[[list[str], str], str]) -> str:
        if modifier == "single":
            if len(values) != 1:
                raise ValueError(
                    f"Modifier 'single' requires exactly 1 concept, got {len(values)}"
                )
            return values[0]
        if modifier in ("list(and)", "list(or)", "list(neg_all)"):
            if not values:
                raise ValueError(
                    f"Modifier '{modifier}' requires at least 1 concept, got 0"
                )
            if modifier == "list(and)":
                return join_fn(values, "and")
            if modifier == "list(or)":
                return join_fn(values, "or")
            return join_fn(values, "neg_all")
        raise ValueError(f"Unknown modifier: {modifier}")
