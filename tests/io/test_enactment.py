import json
import os
import pathlib

import pint
import pytest

from authorityspoke.enactments import Code, Enactment
from authorityspoke.entities import Entity
from authorityspoke.facts import Fact
from authorityspoke.holdings import Holding
from authorityspoke.opinions import Opinion
from authorityspoke.predicates import Predicate
from authorityspoke.procedures import Procedure
from authorityspoke.io import readers, schemas
from authorityspoke.io.loaders import load_holdings
from authorityspoke.io import filepaths
from authorityspoke.rules import Rule
from authorityspoke.selectors import TextQuoteSelector

ureg = pint.UnitRegistry()


class TestEnactmentImport:
    def test_enactment_from_dict(self, make_regime):
        record = {"source": "/us-ca/evid/s351"}
        schema = schemas.EnactmentSchema()
        schema.context["regime"] = make_regime
        enactment = schema.load(record)
        assert "all relevant evidence is admissible" in enactment.text

    def test_enactment_import_from_holding(self, make_regime):
        holdings = load_holdings("holding_cardenas.json", regime=make_regime)
        enactment_list = holdings[0].enactments
        assert "all relevant evidence is admissible" in enactment_list[0].text
