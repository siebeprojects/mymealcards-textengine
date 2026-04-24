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

from dataclasses import dataclass


@dataclass
class MedicalType:
    id:       str
    singular: str
    plural:   str

    def __str__(self) -> str:
        return (
            f"MedicalType[{self.id}]\n"
            f"  singular : {self.singular}\n"
            f"  plural   : {self.plural}"
        )


@dataclass
class CardGroup:
    id:          str
    label:       str
    medicaltype: MedicalType

    def __str__(self) -> str:
        return (
            f"CardGroup[{self.id}]\n"
            f"  label      : {self.label}\n"
            f"  medicaltype: {self.medicaltype.id}"
        )


@dataclass
class Card:
    id:             str
    cardid:         str
    cardgroup:      CardGroup
    medicaltype:    MedicalType   # effective — override or inherited from cardgroup
    scope:          str
    header:         str
    description:    str
    subheader:      str
    footer:         str
    examples_left:  list[str]     # resolved display labels
    examples_right: list[str]

    def __str__(self) -> str:
        return (
            f"Card[{self.id}]\n"
            f"  cardid        : {self.cardid}\n"
            f"  cardgroup     : {self.cardgroup.label}\n"
            f"  medicaltype   : {self.medicaltype.singular}\n"
            f"  scope         : {self.scope}\n"
            f"  header        : {self.header}\n"
            f"  description   : {self.description}\n"
            f"  subheader     : {self.subheader}\n"
            f"  footer        : {self.footer}\n"
            f"  examples_left : {self.examples_left}\n"
            f"  examples_right: {self.examples_right}"
        )


@dataclass
class Product:
    id:        str
    card:      Card
    label:     str
    label_pdf: str

    def __str__(self) -> str:
        return (
            f"Product[{self.id}]\n"
            f"  card     : {self.card.id}\n"
            f"  label    : {self.label}\n"
            f"  label_pdf: {self.label_pdf}"
        )


@dataclass
class Language:
    code:      str
    name:      str
    direction: str
    label:     str

    def __str__(self) -> str:
        return (
            f"Language[{self.code}]\n"
            f"  name     : {self.name}\n"
            f"  direction: {self.direction}\n"
            f"  label    : {self.label}"
        )


@dataclass
class UIElement:
    id:        str
    value:     str
    localized: bool

    def __str__(self) -> str:
        return (
            f"UIElement[{self.id}]\n"
            f"  value    : {self.value}\n"
            f"  localized: {self.localized}"
        )


@dataclass
class Tree:
    language:      Language
    medical_types: dict[str, MedicalType]
    card_groups:   dict[str, CardGroup]
    cards:         dict[str, Card]
    products:      dict[str, Product]
    ui:            dict[str, UIElement]

    def __str__(self) -> str:
        def section(title: str, items: dict) -> str:
            lines = [f"\n--- {title} ({len(items)}) ---"]
            lines += [str(obj) for obj in items.values()]
            return "\n".join(lines)

        return "\n".join([
            f"Tree[{self.language.code}]",
            str(self.language),
            section("MedicalTypes", self.medical_types),
            section("CardGroups",   self.card_groups),
            section("Cards",        self.cards),
            section("Products",     self.products),
            section("UI",           self.ui),
        ])
