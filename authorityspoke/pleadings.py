from dataclasses import dataclass

from typing import ClassVar, Optional

from authorityspoke.entities import Entity
from authorityspoke.factors import Factor
from authorityspoke.facts import Fact
from authorityspoke.formatting import indented


@dataclass(frozen=True)
class Pleading(Factor):
    r"""
    A document filed by a party to make :class:`Allegation`\s.

    :param filer:
        the :class:`.Entity` that the pleading references as having filed it,
        regardless of any questions about the identification of the filer.

    :param name:

    :param absent:

    :param generic:
    """

    filer: Optional[Entity] = None
    name: Optional[str] = None
    absent: bool = False
    generic: bool = False
    context_factor_names: ClassVar = ("filer",)

    def __str__(self):
        string = f'{("filed by " + str(self.filer) if self.filer else "")}'
        return super().__str__().format(string).replace("Pleading", "pleading")

    @property
    def short_string(self):
        return str(self)


@dataclass(frozen=True)
class Allegation(Factor):
    """
    A formal assertion of a :class:`Fact`.

    May be included by a party in a :class:`Pleading`
    to establish a cause of action.

    :param statement:
        a :class:`Fact` being alleged

    :param pleading:
        the :class:`Pleading` in where the allegation appears

    :param name:

    :param absent:

    :param generic:
    """

    statement: Optional[Fact] = None
    pleading: Optional[Pleading] = None
    name: Optional[str] = None
    absent: bool = False
    generic: bool = False
    context_factor_names: ClassVar = ("statement", "pleading")

    def __str__(self):
        text = ""
        if self.statement:
            text += f"\n" + indented("OF:")
            factor_text = indented(str(self.statement), tabs=2)
            text += f"\n{str(factor_text)}"
        if self.pleading:
            text += f"\n" + indented("FOUND IN:")
            factor_text = indented(str(self.pleading), tabs=2)
            text += f"\n{str(factor_text)}"
        return super().__str__().format(text).strip()

    @property
    def short_string(self):
        string = (
            f'{("in " + self.pleading.short_string + ",") if self.pleading else ""}'
            + f'{("claiming " + self.statement.short_string + ",") if self.statement else ""}'
        )
        string = string.strip(",")
        return super().__str__().format(string).replace("Allegation", "allegation")
