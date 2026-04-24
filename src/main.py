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

from pathlib import Path

from engine.ast_validator import AstValidator
from engine.concept_resolver import ConceptResolver
from engine.data_loader import DataLoader
from engine.parser import Parser
from engine.language_renderer import LanguageRenderer
from engine.models import Tree
from engine.tree_compiler import TreeCompiler
from languages.en.language_renderer import EnglishLanguageRenderer


DATA_PATH    = Path(__file__).parent / "data"
SCHEMAS_PATH = Path(__file__).parent / "schemas"

_RENDERER_REGISTRY: dict[str, type[LanguageRenderer]] = {
    "en": EnglishLanguageRenderer,
}


def compile_language(language_code: str) -> Tree:
    renderer_class = _RENDERER_REGISTRY.get(language_code)
    if renderer_class is None:
        raise ValueError(f"No template renderer registered for language: {language_code}")

    concept_resolver = ConceptResolver()
    raw_data         = DataLoader(DATA_PATH, SCHEMAS_PATH).load()
    ast_tree         = Parser(raw_data, language_code).build()
    AstValidator(ast_tree, concept_resolver).validate()
    renderer         = renderer_class(concept_resolver)
    tree             = TreeCompiler(ast_tree, renderer).compile()
    return tree


if __name__ == "__main__":
    tree = compile_language("en")
    for card_id, card in tree.cards.items():
        print(f"{card.cardid}  {card.header}")
        print(f"  {card.description}")
        print(f"  {card.footer}")
        print()
