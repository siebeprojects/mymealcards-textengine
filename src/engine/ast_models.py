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

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class AstMedicalType:
    id:       str
    singular: str
    plural:   str

    def __str__(self) -> str:
        return (
            f"AstMedicalType[{self.id}]\n"
            f"  singular : {self.singular}\n"
            f"  plural   : {self.plural}"
        )


@dataclass
class AstCardGroup:
    id:          str
    medicaltype: AstMedicalType

    def __str__(self) -> str:
        return (
            f"AstCardGroup[{self.id}]\n"
            f"  medicaltype: {self.medicaltype.id}"
        )


@dataclass
class AstConcept:
    id:            str
    noun_singular: str | None
    noun_plural:   str | None
    attributive:   str | None
    display_label: str | None
    gender:        str | None = None

    def __str__(self) -> str:
        return (
            f"AstConcept[{self.id}]\n"
            f"  noun_singular: {self.noun_singular}\n"
            f"  noun_plural  : {self.noun_plural}\n"
            f"  attributive  : {self.attributive}\n"
            f"  display_label: {self.display_label}\n"
            f"  gender       : {self.gender}"
        )


@dataclass
class AstTemplateToken:
    modifier:    str   # list(and) | list(or) | list(neg_all) | single
    placeholder: str   # original {concepts:modifier} string

    def __str__(self) -> str:
        return (
            f"AstTemplateToken\n"
            f"  modifier   : {self.modifier}\n"
            f"  placeholder: {self.placeholder}"
        )


@dataclass
class AstTemplate:
    id:              str
    type:            str
    args:            list[str]
    fallback:        list[str]
    template_string: str
    tokens:          list[AstTemplateToken] = field(default_factory=list)

    def __str__(self) -> str:
        token_lines = "\n".join(f"    {token.placeholder}" for token in self.tokens)
        return (
            f"AstTemplate[{self.id}]\n"
            f"  type    : {self.type}\n"
            f"  args    : {self.args}\n"
            f"  fallback: {self.fallback}\n"
            f"  template: {self.template_string}\n"
            f"  tokens  :\n{token_lines if token_lines else '    (none)'}"
        )


@dataclass
class AstFieldDefinition:
    mode:         Literal["static", "template"]
    template:     AstTemplate | None
    concepts:     list[AstConcept]
    static_value: str | None = None

    def __str__(self) -> str:
        if self.mode == "static":
            return f"AstFieldDefinition[static] value={self.static_value}"
        if self.template is None:
            return "AstFieldDefinition[template] template=<missing>"
        concept_ids = [concept.id for concept in self.concepts]
        return f"AstFieldDefinition[template] template={self.template.id} concepts={concept_ids}"


@dataclass
class AstExamples:
    template:       AstTemplate
    concepts_left:  list[AstConcept]
    concepts_right: list[AstConcept]

    def __str__(self) -> str:
        left_ids  = [concept.id for concept in self.concepts_left]
        right_ids = [concept.id for concept in self.concepts_right]
        return (
            f"AstExamples\n"
            f"  template: {self.template.id}\n"
            f"  left    : {left_ids}\n"
            f"  right   : {right_ids}"
        )


@dataclass
class AstCard:
    id:                   str
    cardid:               str
    cardgroup:            AstCardGroup
    medicaltype_override: AstMedicalType | None
    scope:                AstFieldDefinition
    header:               AstFieldDefinition
    description:          AstFieldDefinition
    subheader:            AstFieldDefinition
    examples:             AstExamples
    footer:               AstFieldDefinition

    def effective_medicaltype(self) -> AstMedicalType:
        return self.medicaltype_override or self.cardgroup.medicaltype

    def __str__(self) -> str:
        medical_type    = self.effective_medicaltype()
        override_marker = " (override)" if self.medicaltype_override else ""
        return (
            f"AstCard[{self.id}]\n"
            f"  cardid     : {self.cardid}\n"
            f"  cardgroup  : {self.cardgroup.id}\n"
            f"  medicaltype: {medical_type.id}{override_marker}\n"
            f"  scope      : {self.scope}\n"
            f"  header     : {self.header}\n"
            f"  description: {self.description}\n"
            f"  subheader  : {self.subheader}\n"
            f"  footer     : {self.footer}\n"
            f"  examples   :\n"
            f"    template: {self.examples.template.id}\n"
            f"    left    : {[c.id for c in self.examples.concepts_left]}\n"
            f"    right   : {[c.id for c in self.examples.concepts_right]}"
        )


@dataclass
class AstProduct:
    id:        str
    card:      AstCard
    label:     str
    label_pdf: str

    def __str__(self) -> str:
        return (
            f"AstProduct[{self.id}]\n"
            f"  card     : {self.card.id}\n"
            f"  label    : {self.label}\n"
            f"  label_pdf: {self.label_pdf}"
        )


@dataclass
class AstLanguage:
    code:      str
    name:      str
    direction: str
    label:     str

    def __str__(self) -> str:
        return (
            f"AstLanguage[{self.code}]\n"
            f"  name     : {self.name}\n"
            f"  direction: {self.direction}\n"
            f"  label    : {self.label}"
        )


@dataclass
class AstUIElement:
    id:        str
    value:     str
    localized: bool

    def __str__(self) -> str:
        return (
            f"AstUIElement[{self.id}]\n"
            f"  value    : {self.value}\n"
            f"  localized: {self.localized}"
        )


@dataclass
class AstTree:
    language:      AstLanguage
    medical_types: dict[str, AstMedicalType]
    card_groups:   dict[str, AstCardGroup]
    concepts:      dict[str, AstConcept]
    templates:     dict[str, AstTemplate]
    cards:         dict[str, AstCard]
    products:      dict[str, AstProduct]
    ui:            dict[str, AstUIElement]

    def __str__(self) -> str:
        def section(title: str, items: dict) -> str:
            lines = [f"\n--- {title} ({len(items)}) ---"]
            lines += [str(obj) for obj in items.values()]
            return "\n".join(lines)

        return "\n".join([
            f"AstTree[{self.language.code}]",
            str(self.language),
            section("AstMedicalTypes", self.medical_types),
            section("AstCardGroups",   self.card_groups),
            section("AstConcepts",     self.concepts),
            section("AstTemplates",    self.templates),
            section("AstCards",        self.cards),
            section("AstProducts",     self.products),
            section("AstUI",           self.ui),
        ])
