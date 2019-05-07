import datetime
import json
import operator

from pint import UnitRegistry
import pytest

from authorityspoke.entities import Entity, Human, Event
from authorityspoke.factors import Predicate, Factor, Fact
from authorityspoke.opinions import Opinion
from authorityspoke.predicates import ureg, Q_


class TestEntities:
    def test_conversion_to_generic(self, make_entity):
        e = make_entity
        assert e["motel_specific"].make_generic() == e["motel"]

    def test_repr_equal_after_make_generic(self, make_entity):
        """
        see the docstring for :meth:`Factor._import_to_mapping`
        for an explanation of what led to __repr__s being
        compared for equality instead of the underlying objects.
        """
        e = make_entity
        motel = e["motel"]
        motel_b = motel.make_generic()
        assert repr(motel) == repr(motel_b)

    def test_context_register(self, make_entity):
        """
        Class "Human" implies "Entity" but not vice versa.
        """
        motel = make_entity["motel"]
        watt = make_entity["watt"]
        empty_update = motel._context_register(watt, operator.ge)
        assert not any(register is not None for register in empty_update)

        update = motel._context_register(watt, operator.le)
        assert any(register == {motel: watt, watt: motel} for register in update)

    def test_new_context(self, make_entity):
        changes = {
            make_entity["motel"]: Entity("Death Star"),
            make_entity["watt"]: Human("Darth Vader"),
        }
        motel = make_entity["motel"]
        assert motel.new_context(changes) == changes[make_entity["motel"]]

    # Same Meaning

    def test_specific_to_generic_different_object(self, make_entity):
        e = make_entity
        motel = e["motel_specific"]
        motel_b = motel.make_generic()
        assert not motel is motel_b
        assert not motel == motel_b

    def test_equality_generic_entities(self, make_entity):
        e = make_entity
        assert e["motel"].means(e["trees"])
        assert not e["motel"] == e["trees"]

    def test_generic_human_and_event_not_equal(self, make_entity):
        """Neither is a subclass of the other."""
        assert not make_entity["tree_search"].means(make_entity["watt"])

    def test_generic_human_and_entity_not_equal(self, make_entity):
        """Human is a subclass of Entity."""
        assert not make_entity["motel"].means(make_entity["watt"])

    # Implication

    def test_implication_generic_entities(self, make_entity):
        assert make_entity["motel_specific"] > make_entity["trees"]
        assert not make_entity["motel_specific"] < make_entity["trees"]

    def test_implication_same_except_generic(self, make_entity):
        assert make_entity["motel_specific"] > make_entity["motel"]
        assert not make_entity["motel_specific"] < make_entity["motel"]

    def test_same_entity_not_ge(self, make_entity):
        assert not make_entity["motel"] > make_entity["motel"]

    def test_implication_subclass(self, make_entity):
        assert make_entity["tree_search_specific"] >= make_entity["motel"]
        assert make_entity["tree_search"] > make_entity["motel"]

    def test_implication_superclass(self, make_entity):
        assert not make_entity["trees"] >= make_entity["tree_search"]

    # Contradiction

    def test_error_contradiction_with_non_factor(self, make_entity, make_predicate):
        with pytest.raises(TypeError):
            assert make_entity["trees"].contradicts(make_predicate["p3"])

    def test_no_contradiction_of_other_factor(self, make_entity, watt_factor):
        assert not make_entity["trees"].contradicts(make_entity["watt"])
        assert not make_entity["trees"].contradicts(watt_factor["f1"])
