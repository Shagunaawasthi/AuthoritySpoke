import operator

import pytest

from authorityspoke.comparisons import ContextRegister
from authorityspoke.groups import FactorGroup


class TestContextRegisters:
    def test_possible_context_without_empty_spaces(self, watt_factor, make_entity):
        left = watt_factor["f1"]
        right = watt_factor["f1"]
        contexts = list(left.possible_contexts(right))
        assert len(contexts) == 1
        assert contexts[0][make_entity["motel"]] == make_entity["motel"]

    def test_all_possible_contexts_identical_factor(self, watt_factor, make_entity):
        left = watt_factor["f2"]
        right = watt_factor["f2"]
        contexts = list(left.possible_contexts(right))
        assert len(contexts) == 2
        assert any(
            context[make_entity["watt"]] == make_entity["motel"] for context in contexts
        )

    def test_limited_possible_contexts_identical_factor(self, watt_factor, make_entity):
        left = watt_factor["f2"]
        right = watt_factor["f2"]
        context = {make_entity["motel"]: make_entity["motel"]}
        contexts = list(left.possible_contexts(right, context=context))
        assert len(contexts) == 1
        assert contexts[0][make_entity["watt"]] == make_entity["watt"]

    def test_context_register_empty(self, make_complex_fact, watt_factor):
        """
        Yields no context_register because the Entity in f1 doesn't imply
        the Fact in f_relevant_murder.
        """
        with pytest.raises(StopIteration):
            next(
                watt_factor["f1"]._context_registers(
                    make_complex_fact["f_relevant_murder"], operator.ge
                )
            )

    def test_context_register_valid(self, make_entity, watt_factor):
        assert next(
            watt_factor["f1"]._context_registers(
                watt_factor["f1_entity_order"], operator.le
            )
        ) == {make_entity["motel"]: make_entity["watt"],}

    def test_import_to_context_register(self, make_entity, watt_factor):
        f = watt_factor["f7"]
        left = ContextRegister(
            {
                watt_factor["f7"]: watt_factor["f7_swap_entities"],
                make_entity["motel"]: make_entity["trees"],
            }
        )
        right = ContextRegister({make_entity["trees"]: make_entity["motel"]})
        assert len(left.merged_with(right)) == 3

    def test_import_to_mapping_no_change(self, make_entity):
        old_mapping = ContextRegister({make_entity["motel"]: make_entity["trees"]})
        assert dict(
            old_mapping.merged_with({make_entity["motel"]: make_entity["trees"]})
        ) == {make_entity["motel"]: make_entity["trees"],}

    def test_import_to_mapping_conflict(self, make_entity):
        merged = ContextRegister(
            {make_entity["motel"]: make_entity["trees"]}
        ).merged_with(ContextRegister({make_entity["motel"]: make_entity["motel"]}))
        assert merged is None

    def test_import_to_mapping_reciprocal(self, watt_factor):
        mapping = ContextRegister({watt_factor["f7"]: watt_factor["f7"]}).merged_with(
            {watt_factor["f7_swap_entities"]: watt_factor["f7_swap_entities"]}
        )
        assert mapping[watt_factor["f7"]] == watt_factor["f7"]

    def test_registers_for_interchangeable_context(self, make_entity, watt_factor):
        """
        Test that _registers_for_interchangeable_context swaps the first two
        items in the ContextRegister
        """
        matches = ContextRegister(
            {
                make_entity["motel"]: make_entity["trees"],
                make_entity["trees"]: make_entity["motel"],
                make_entity["watt"]: make_entity["watt"],
            }
        )
        new_matches = [
            match
            for match in watt_factor["f7"]._registers_for_interchangeable_context(
                matches
            )
        ]
        assert (
            ContextRegister(
                {
                    make_entity["trees"]: make_entity["trees"],
                    make_entity["motel"]: make_entity["motel"],
                    make_entity["watt"]: make_entity["watt"],
                }
            )
            in new_matches
        )


class TestLikelyContext:
    def test_likely_context_one_factor(self, make_entity, watt_factor):
        left = watt_factor["f2"]
        right = watt_factor["f2"]
        context = next(left.likely_contexts(right))
        assert context[make_entity["motel"]] == make_entity["motel"]

    def test_likely_context_implication_one_factor(self, make_entity, watt_factor):
        left = watt_factor["f8"]
        right = watt_factor["f8_meters"]
        context = next(left.likely_contexts(right))
        assert context[make_entity["motel"]] == make_entity["motel"]

    def test_likely_context_two_factors(self, make_entity, watt_factor):
        left = FactorGroup((watt_factor["f9_swap_entities"], watt_factor["f2"]))
        right = watt_factor["f2"]
        context = next(left.likely_contexts(right))
        assert context[make_entity["motel"]] == make_entity["motel"]

    def test_likely_context_two_by_two(self, make_entity, watt_factor):
        left = FactorGroup((watt_factor["f9"], watt_factor["f2"]))
        right = FactorGroup(
            (watt_factor["f9_swap_entities"], watt_factor["f9_more_different_entity"])
        )
        context = next(left.likely_contexts(right))
        assert context[make_entity["motel"]] == make_entity["trees"]

    def test_likely_context_different_context_factors(self, make_opinion_with_holding):
        lotus = make_opinion_with_holding["lotus_majority"]
        oracle = make_opinion_with_holding["oracle_majority"]
        left = [lotus.holdings[2].outputs[0], lotus.holdings[2].inputs[0].to_effect]
        left = FactorGroup(left)
        right = FactorGroup(oracle.holdings[2].outputs[0])
        context = next(left.likely_contexts(right))
        lotus_menu = lotus.holdings[2].generic_factors[0]
        java_api = oracle.generic_factors[0]
        assert context[lotus_menu] == java_api

    def test_likely_context_from_factor_meaning(self, make_opinion_with_holding):
        lotus = make_opinion_with_holding["lotus_majority"]
        oracle = make_opinion_with_holding["oracle_majority"]
        left = lotus.holdings[2].outputs[0]
        right = oracle.holdings[2].outputs[0]
        likely = left._likely_context_from_meaning(right, context=ContextRegister())
        lotus_menu = lotus.holdings[2].generic_factors[0]
        java_api = oracle.generic_factors[0]
        assert likely[lotus_menu] == java_api

    def test_union_one_generic_not_matched(self, make_opinion_with_holding):
        """
        Here, both FactorGroups have "fact that <> was a computer program".
        But they each have another generic that can't be matched:
        fact that <the Java API> was a literal element of <the Java language>
        and
        fact that <the Lotus menu command hierarchy> provided the means by
        which users controlled and operated <Lotus 1-2-3>

        Tests that Factors from "left" should be keys and Factors from "right" values.
        """
        lotus = make_opinion_with_holding["lotus_majority"]
        oracle = make_opinion_with_holding["oracle_majority"]
        left = FactorGroup(lotus.holdings[7].inputs[:2])
        right = FactorGroup(
            [oracle.holdings[3].outputs[0], oracle.holdings[3].inputs[0]]
        )
        new = left | right
        text = (
            "that <the Lotus menu command hierarchy> was a "
            "literal element of <Lotus 1-2-3>"
        )
        assert text in new[1].short_string
