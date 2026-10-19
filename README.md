# AST Card Compiler — Proof of Concept

A prototype compiler that transforms structured JSON data definitions into fully rendered, localizable card objects via an Abstract Syntax Tree (AST) pipeline.

All data in example/placeholder data (`concept0`, `medicaltype1`, etc.) is intended to demonstrate the compiler's architecture. No real domain data is included.

---

## What it does

Given a set of JSON data files describing card templates, concepts, and localization strings, the compiler produces a `Tree` — a fully resolved, language-specific object graph of rendered cards, products, and UI elements.

Cards are defined by referencing **concepts** (the vocabulary) and **templates** (the sentence patterns). The compiler resolves grammatical forms, applies fallback chains, and renders each field for the target language.

---

## Pipeline

```
JSON data files
      │
      ▼
  DataLoader          validates against JSON schemas
      │
      ▼
    Parser            transforms raw data → AstTree
      │
      ▼
 AstValidator         checks cross-reference consistency
      │
      ▼
ConceptResolver       resolves grammatical forms with fallback chains
      │
      ▼
LanguageRenderer      renders template strings for the target language
      │
      ▼
 TreeCompiler         compiles AstTree → final Tree
      │
      ▼
     Tree             language: Language
                      medical_types: dict[str, MedicalType]
                      card_groups: dict[str, CardGroup]
                      cards: dict[str, Card]
                      products: dict[str, Product]
                      ui: dict[str, UIElement]
```

---

## Data model

| Entity | Role |
|---|---|
| **MedicalType** | Top-level classification (e.g. `medicaltype0`, `medicaltype1`) |
| **CardGroup** | Groups cards under a medical type |
| **Concept** | A vocabulary item with grammatical forms (`noun_singular`, `noun_plural`, `attributive`) and an optional `display.label` override |
| **Template** | A sentence pattern with typed placeholders (`{concepts:list(and)}`, `{concepts:list(or)}`, `{concepts:list(neg_all)}`, `{concepts:single}`) |
| **Card** | A rendered card with `scope`, `header`, `description`, `subheader`, `examples`, and `footer` fields |
| **Product** | A named reference to a card |

### Template modifiers

| Modifier | Behaviour |
|---|---|
| `{concepts:single}` | Renders the first resolved concept label |
| `{concepts:list(and)}` | Joins resolved labels with "and" |
| `{concepts:list(or)}` | Joins resolved labels with "or" |
| `{concepts:list(neg_all)}` | Joins using the language-specific negation separator |

### Concept fallback chain

When rendering a concept in a template, the compiler walks a `fallback` list defined on the template. For example:

```json
"fallback": ["display.label", "forms.noun_plural", "forms.noun_singular"]
```

The first field that resolves to a non-null value is used.

---

## Example data

The repository ships with three demo cards (`card0`, `card1`, `card2`), two card groups, two medical types, and five concepts (`concept0`–`concept4`) that exercise the different features of the compiler:

- `card0` — single-concept card, simple template rendering
- `card1` — multi-concept card, list modifiers with left/right example columns
- `card2` — card with a `medicaltype` override and a static field overridden in the language file

---

## Getting started

**Requirements:** Python 3.10 or higher.

Clone the repository and install the single dependency:

```bash
git clone https://github.com/your-org/mymealcards-textengine.git
cd mymealcards-textengine
pip install jsonschema
```

Run the compiler from the project root:

```bash
cd src
python main.py
```

This compiles the English example data and prints the resulting `Tree` to stdout.

To use the compiler from your own script, run it from the project root with `src` on the path:

```bash
PYTHONPATH=src python - <<'EOF'
from main import compile_language

tree = compile_language("en")

for card_id, card in tree.cards.items():
    print(f"{card.cardid}  {card.header}")
    print(f"  {card.description}")
    print(f"  {card.footer}")
    print()
EOF
```

Expected output:

```
DEMO001-EN  Concept-zero Type0
  This should not contain the following: concepts zero and concepts one.
  Avoid any cross-contact. Thank you.

DEMO002-EN  Concept-zero and Concept-two Type0
  This should not contain the following: concepts zero and concept two.
  Avoid any cross-contact. Thank you.

DEMO003-EN  Type1 Card (Example Override)
  For secondary reasons, no items containing concepts three.
  This is important. Thank you.
```

---

## Adding a language

1. Add the language code to `src/data/languages.core.json`
2. Create localization files: `src/data/*/[entity].[code].json`
3. Implement a renderer in `src/languages/[code]/language_renderer.py`
4. Register it in `src/main.py`

---

## Project structure

```
src/
├── main.py                      # Entry point
├── engine/
│   ├── data_loader.py           # JSON loading + schema validation
│   ├── parser.py                # Raw data → AstTree
│   ├── ast_models.py            # AST dataclasses
│   ├── ast_validator.py         # AST consistency checks
│   ├── concept_resolver.py      # Grammatical form resolution
│   ├── tree_compiler.py         # AstTree → Tree
│   └── language_renderer.py     # Base renderer interface
├── languages/
│   └── en/
│       ├── grammar.py           # English grammar constants
│       └── language_renderer.py # English renderer implementation
├── data/                        # JSON data files
│   ├── *.core.json              # Language-agnostic definitions
│   └── [entity]/[entity].en.json  # English localizations
└── schemas/                     # JSON Schema validation files
```

---

This is a prototype. The compiler pipeline is complete and functional; the data files serve as illustrative examples only.
