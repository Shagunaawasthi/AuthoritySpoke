import logging

import pytest

from authorityspoke.enactments import Enactment
from authorityspoke.entities import Entity
from authorityspoke.factors import ContextRegister
from authorityspoke.facts import Fact
from authorityspoke.holdings import Holding
from authorityspoke.predicates import Predicate, Q_
from authorityspoke.procedures import Procedure
from authorityspoke.rules import Rule

from authorityspoke.io import loaders, readers


class TestRules:
    def test_enactment_type_in_str(self, make_holding):
        assert "constitution" in str(make_holding["h1"]).lower()

    def test_no_blank_line_in_str(self, make_holding):
        assert "\n\n" not in str(make_holding["h2"])

    def test_enactment_text_in_str(self, make_holding):
        assert "secure in their persons" in str(make_holding["h1"])

    def test_None_not_in_str(self, make_holding):
        assert "None" not in str(make_holding["h2"])

    def test_str_without_legislation(self, make_holding):
        assert "legislation" not in str(make_holding["h_output_distance_less"])

    def test_new_concrete_context(self, make_holding):
        different = make_holding["h1"].new_context(
            [Entity("Castle Grayskull"), Entity("He-Man")]
        )
        assert "<He-Man> operated" in str(different)

    def test_new_context_non_generic(self, make_holding, watt_factor):
        different = make_holding["h1"].new_context(
            {watt_factor["f1"]: watt_factor["f7"]}
        )
        assert "the distance between <Hideaway Lodge> and" in str(different)

    def test_new_context_non_generic_from_list_error(self, make_holding, watt_factor):
        with pytest.raises(ValueError):
            make_holding["h1"].new_context(
                [watt_factor["f1"], watt_factor["f7"], watt_factor["f2"]]
            )

    def test_new_context_dict_must_contain_only_factors(
        self, make_holding, make_predicate
    ):
        with pytest.raises(TypeError):
            make_holding["h1"].new_context({make_predicate["p1"]: make_predicate["p7"]})

    def test_new_context_dict_must_be_dict(self, make_holding, make_predicate):
        with pytest.raises(TypeError):
            make_holding["h1"].new_context([make_predicate["p1"], make_predicate["p2"]])

    def test_new_context_choose_factor_to_replace_by_name(self, make_beard_rule):
        transfer_rule = make_beard_rule[11]
        barber_rule = make_beard_rule[-1]
        defendant = transfer_rule.generic_factors[0]
        counterparty = transfer_rule.generic_factors[2]
        defendant_rule = barber_rule.new_context(
            {"the barber": defendant, "the customer": counterparty}
        )
        assert defendant_rule.generic_factors[1].name == "the defendant"

    def test_generic_factors(self, make_entity, make_holding):
        generics = make_holding["h3"].generic_factors
        assert make_entity["motel"] in generics
        assert make_entity["tree_search"] in generics

    def test_despite_only_in_str_when_relevant(self, make_holding):
        assert "despite the legislation" not in str(make_holding["h1"].rule)

    def test_generic_factors_order(self, make_entity, make_holding):
        """The motel is mentioned in the first input in the JSON,
        so it should be first."""
        generics = make_holding["h1"].generic_factors
        assert list(generics) == [make_entity["motel"], make_entity["watt"]]

    def test_string_with_line_breaks(self, make_opinion_with_holding):
        cardenas = make_opinion_with_holding["cardenas_majority"]
        assert "was addicted to heroin,\n" in str(cardenas.holdings[0])

    def test_string_mentions_absence(self, make_opinion_with_holding):
        cardenas = make_opinion_with_holding["cardenas_majority"]
        assert "absence of the Evidence" in str(cardenas.holdings[1])

    def test_factor_properties_for_rule(self, make_opinion_with_holding):
        cardenas = make_opinion_with_holding["cardenas_majority"]
        assert len(cardenas.holdings[1].inputs) == 1
        assert len(cardenas.holdings[1].outputs) == 1
        assert len(cardenas.holdings[1].despite) == 1

    def test_single_enactment_converted_to_tuple(self, make_holding):
        assert isinstance(make_holding["h2"].enactments, tuple)

    def test_holding_len(self, make_holding):
        assert len(make_holding["h1"]) == 2
        assert len(make_holding["h3"]) == 5

    def test_wrong_role_for_added_enactment(self, make_enactment, make_holding):
        with pytest.raises(ValueError):
            make_holding["h1"].rule.add_enactment(
                incoming=make_enactment["due_process_14"], role="inputs"
            )


class TestSameMeaning:
    def test_holdings_equivalent_entity_orders_equal(self, make_rule):
        """
        Test that holdings are considered equal if they have the same factors
        and the numbers they use to refer to entities are different but in an
        equivalent order.
        e.g. {"F1": "1,2,1", "F2": "2,0,0"} and {"F2": "1,2,2", "F1": "0,1,0"}
        """
        assert make_rule["h1"].means(make_rule["h1_entity_order"])

    def test_added_enactment_changes_meaning(self, make_complex_rule, make_enactment):
        due_process_rule = (
            make_complex_rule["accept_murder_fact_from_relevance"]
            + make_enactment["due_process_5"]
        )

        assert not due_process_rule.means(
            make_complex_rule["accept_murder_fact_from_relevance"]
        )
        assert not make_complex_rule["accept_murder_fact_from_relevance"].means(
            due_process_rule
        )

    def test_holdings_different_entities_unequal(self, make_rule):
        assert not make_rule["h1"].means(make_rule["h1_easy"])

    def test_holdings_differing_in_entity_order_equal(self, make_rule):
        assert make_rule["h1"].means(make_rule["h1_entity_order"])

    def test_holdings_citing_different_enactment_text_unequal(self, make_rule):
        assert not make_rule["h2"].means(make_rule["h2_fourth_a_cite"])

    def test_explain_rule_differing_in_entity_order(self, make_complex_rule):
        left = make_complex_rule["accept_murder_fact_from_relevance_and_shooting"]
        right = make_complex_rule[
            "accept_murder_fact_from_relevance_and_shooting_craig"
        ]
        explanation = left.explain_same_meaning(right)
        assert "<Craig> is like <Alice>" in explanation.prose or "<Alice> is like <Craig>" in explanation.prose
        assert "<Dan> is like <Bob>" in explanation.prose or "<Bob> is like <Dan>" in explanation.prose


class TestImplication:
    def test_holdings_more_inputs_implies_fewer(self, make_rule):
        assert make_rule["h1"] > make_rule["h1_easy"]
        assert make_rule["h2_irrelevant_inputs"] > make_rule["h2"]

    def test_holding_narrower_despite_implies_broader(self, make_rule):
        assert make_rule["h2_exact_in_despite"] > make_rule["h2"]
        assert not make_rule["h2"] > make_rule["h2_exact_in_despite"]

    def test_explain_implication_same_entities(self, make_rule):
        """
        Checks that because the generic entities on both sides of the implication
        relation are the same, the "Hideaway Lodge" Entity corresponds to an equal object.
        """
        explanation = make_rule["h2_exact_in_despite"].explain_implication(
            make_rule["h2"]
        )
        hideaway = Entity("Hideaway Lodge")
        assert explanation[hideaway] == hideaway

    def test_explain_all_to_all_implies_reciprocal(self, make_rule):
        """
        There's only one explanation for how the factors can match between these two Rules.
        The explanation simply matches each context factor to the same factor.
        """
        fewer_inputs = make_rule["h3_fewer_inputs_ALL"]
        explanation = fewer_inputs.explain_implication(make_rule["h3_ALL"])
        assert explanation[Entity("Hideaway Lodge")] == Entity("Hideaway Lodge")

    def test_holdings_more_specific_quantity_implies_less_specific(self, make_rule):
        assert make_rule["h2_exact_quantity"] > make_rule["h2"]

    def test_holdings_less_specific_with_all_implies_more_specific(self, make_rule):
        assert make_rule["h2_ALL"] > make_rule["h2_exact_quantity_ALL"]
        assert not make_rule["h2_exact_quantity_ALL"] > make_rule["h2_ALL"]

    def test_specific_holding_with_all_implies_more_general_with_some(self, make_rule):
        assert make_rule["h2_exact_quantity_ALL"] > make_rule["h2"]

    def test_mandatory_implies_permissive(self, make_rule):
        assert make_rule["h2_MUST"] > make_rule["h2"]
        assert not make_rule["h2"] > make_rule["h2_MUST"]

    def test_all_to_all(self, make_rule):
        """This is supposed to test reciprocal predicates in despite factors."""
        assert make_rule["h2_exact_in_despite_ALL"] > make_rule["h2_ALL"]

    def test_all_to_all_reciprocal(self, make_rule, caplog):
        """
        The entity order shouldn't matter, compared to test_all_to_all,
        because it's the mirror image of the normal entity order.
        """
        caplog.set_level(logging.DEBUG)
        assert make_rule["h2_exact_in_despite_ALL_entity_order"] > make_rule["h2_ALL"]

    def test_some_holding_does_not_imply_version_with_more_supporting_factors(
        self, make_rule
    ):
        """A version of h2 with some supporting factors removed does not imply
        h2.

        A SOME holding means that a court has actually applied the procedure in
        some case. If it also implied variations of itself with other supporting
        inputs added, that would mean that every SOME holding would imply every
        possible variation of itself that could be constructed by substituting
        any different set of supporting inputs."""

        assert not make_rule["h_near_means_curtilage_even_if"] >= make_rule["h2"]
        assert make_rule["h_near_means_curtilage_even_if"] <= make_rule["h2"]

    def test_implication_with_evidence(self, make_rule):
        assert make_rule["h3"] > make_rule["h3_fewer_inputs"]

    def test_holding_based_on_less_text_implies_more(self, make_rule):
        """The implied holding is based on enactment text that is a superset
        of the implying holding's enactment text."""
        assert make_rule["h2"] > make_rule["h2_fourth_a_cite"]

    def test_holding_with_enactment_cite_does_not_imply_without(self, make_rule):
        """Just because an outcome is required by enactment text doesn't mean
        the court would require it pursuant to its common law power to make laws."""
        assert not make_rule["h2"] >= make_rule["h2_without_cite"]

    def test_implication_common_law_and_constitutional(self, make_rule):
        """When a court asserts a holding as valid without legislative support,
        the court is actually making a broader statement than it would be making
        if it cited legislative support. The holding without legislative support
        doesn't depend for its validity on the enactment remaining in effect without
        being repealed.

        The relative priority of the holdings is a different
        matter. Statutory holdings trump common law holdings, and constitutional
        trumps statutory."""
        assert make_rule["h2"] <= make_rule["h2_without_cite"]

    def test_no_implication_of_holding_with_added_despite_enactment(self, make_rule):
        assert not make_rule["h2"] >= make_rule["h2_despite_due_process"]

    def test_implication_of_holding_with_removed_despite_enactment(self, make_rule):
        assert make_rule["h2_despite_due_process"] >= make_rule["h2"]

    def test_implication_more_specific_input(self, make_complex_rule):
        """
        A universal Rule is contravariant with its inputs.
        When an input becomes more specific, the Rule becomes less specific.
        """
        small_reliable = make_complex_rule["accept_small_weight_reliable"]
        small_more_reliable = make_complex_rule[
            "accept_small_weight_reliable_more_evidence"
        ]
        assert small_reliable >= small_more_reliable
        assert not small_more_reliable >= small_reliable

    def test_implication_more_specific_output(self, make_complex_rule):
        """
        A Rule is covariant with its outputs.
        When an output becomes more specific, the Rule becomes more specific.
        """
        small_reliable = make_complex_rule["accept_small_weight_reliable"]
        large_reliable = make_complex_rule["accept_large_weight_reliable"]
        assert not small_reliable >= large_reliable
        assert large_reliable >= small_reliable

    def test_implies_holding(self, make_complex_rule):
        """
        The Rule class doesn't know anything about the Holding class, but it
        should check whether Holding has an is_implied_by method and call it.
        """
        small_reliable = make_complex_rule["accept_small_weight_reliable"]
        small_more_reliable_holding = Holding(
            make_complex_rule["accept_small_weight_reliable_more_evidence"]
        )
        assert small_reliable >= small_more_reliable_holding


class TestContradiction:
    def test_some_holding_consistent_with_absent_output(self, make_rule):
        assert not make_rule["h2"].contradicts(make_rule["h2_output_absent"])
        assert not make_rule["h2_output_absent"].contradicts(make_rule["h2"])

    def test_some_holding_consistent_with_false_output(self, make_rule):
        assert not make_rule["h2"].contradicts(make_rule["h2_output_false"])
        assert not make_rule["h2_output_false"].contradicts(make_rule["h2"])

    def test_some_holding_consistent_with_absent_false_output(self, make_rule):
        assert not make_rule["h2"].contradicts(make_rule["h2_output_absent_false"])
        assert not make_rule["h2_output_absent_false"].contradicts(make_rule["h2"])

    def test_contradicts_if_valid_some_vs_all(self, make_rule):

        """
        This test and the one below show that you can change whether two
        holdings contradict one another by exchanging the SOME/MAY from one
        with the ALL/MUST from the other.

        The assertion here is:
        In SOME cases where the distance between A and B is less than 20 feet
        the court MUST find that
        A is in the curtilage of B

        contradicts

        In ALL cases where the distance between A and B is less than 35 feet
        the court MAY find that
        A is not in the curtilage of B
        """

        assert make_rule["h_nearer_means_curtilage_MUST"].contradicts(
            make_rule["h_near_means_no_curtilage_ALL"]
        )
        assert make_rule["h_near_means_no_curtilage_ALL"].contradicts(
            make_rule["h_nearer_means_curtilage_MUST"]
        )

    def test_contradicts_if_valid_some_vs_all_no_contradiction(self, make_rule):

        """
        This test and the one above show that you can change whether two
        holdings contradict one another by exchanging the SOME/MAY from one
        with the ALL/MUST from the other.

        The assertion here is:
        In SOME cases where the distance between A and B is less than 35 feet
        the court MAY find that
        A is not in the curtilage of B

        does not contradict

        In ALL cases where the distance between A and B is less than 20 feet
        the court MUST find that
        A is in the curtilage of B
        """

        assert not make_rule["h_near_means_no_curtilage"].contradicts(
            make_rule["h_nearer_means_curtilage_ALL"]
        )
        assert not make_rule["h_nearer_means_curtilage_ALL"].contradicts(
            make_rule["h_near_means_no_curtilage"]
        )

    def test_contradicts_if_valid_all_vs_some(self, make_rule):

        """
        The assertion here is:
        In ALL cases where the distance between A and B is less than 35 feet
        the court MUST find that
        A is not in the curtilage of B

        contradicts

        In SOME cases where the distance between A and B is less than 20 feet
        the court MAY find that
        A is in the curtilage of B
        """

        assert make_rule["h_near_means_no_curtilage_ALL_MUST"].contradicts(
            make_rule["h_nearer_means_curtilage"]
        )
        assert make_rule["h_nearer_means_curtilage"].contradicts(
            make_rule["h_near_means_no_curtilage_ALL_MUST"]
        )

    def test_no_contradiction_quantity_outputs(self, make_rule):
        """
        Added to try to break Procedure.contradiction_between_outputs.

        "the distance between {the stockpile of trees} and a parking area
        used by personnel and patrons of {Hideaway Lodge} was <= 5 feet"
        does not contradict
        "the distance between {circus} and a parking area used by personnel
        and patrons of {Hideaway Lodge} was > 5 feet"

        Given that the context parameter indicates the "circus" is not the
        same place as "the stockpile of trees", there's no contradiction.
        """
        stockpile_means_stockpile = ContextRegister(
            {Entity("the stockpile of trees"): Entity("the stockpile of trees")}
        )
        assert not make_rule["h_output_distance_less"].contradicts(
            make_rule["h_output_farther_different_entity"], context=stockpile_means_stockpile
        )
        assert not make_rule["h_output_farther_different_entity"].contradicts(
            make_rule["h_output_distance_less"], context=stockpile_means_stockpile
        )

    def test_contradicts_if_valid_all_vs_all(self, make_rule):

        """
        The assertion here is:
        In ALL cases where the distance between A and B is less than 35 feet
        the court MUST find that
        A is in the curtilage of B

        contradicts

        In ALL cases where the distance between A and B is more than 20 feet
        the court MAY find that
        A is not in the curtilage of B
        """

        assert make_rule["h_near_means_curtilage_ALL_MUST"].contradicts(
            make_rule["h_far_means_no_curtilage"]
        )
        assert make_rule["h_far_means_no_curtilage"].contradicts(
            make_rule["h_near_means_curtilage_ALL_MUST"]
        )

    def test_always_may_contradicts_sometimes_must_not(self, make_rule):
        assert make_rule["h2_ALL"].contradicts(make_rule["h2_SOME_MUST_output_false"])
        assert make_rule["h2_SOME_MUST_output_false"].contradicts(make_rule["h2_ALL"])

    def test_always_may_contradicts_sometimes_must_omit_output(self, make_rule):
        assert make_rule["h2_ALL"].contradicts(make_rule["h2_SOME_MUST_output_absent"])
        assert make_rule["h2_SOME_MUST_output_absent"].contradicts(make_rule["h2_ALL"])

    def test_sometimes_must_contradicts_always_may_not(self, make_rule):
        assert make_rule["h2_MUST"].contradicts(make_rule["h2_ALL_MAY_output_false"])
        assert make_rule["h2_ALL_MAY_output_false"].contradicts(make_rule["h2_MUST"])

    def test_sometimes_must_contradicts_always_must_not(self, make_rule):
        assert make_rule["h2_MUST"].contradicts(make_rule["h2_ALL_MUST_output_false"])
        assert make_rule["h2_ALL_MUST_output_false"].contradicts(make_rule["h2_MUST"])

    def test_some_must_no_contradict_some_may(self, make_rule):
        assert not make_rule["h2_MUST"].contradicts(make_rule["h2"])
        assert not make_rule["h2"].contradicts(make_rule["h2_MUST"])

    # Contradiction of other types

    def test_sometimes_must_contradicts_holding_always_must_not(
        self, make_rule, make_holding
    ):
        assert make_rule["h2_MUST"].contradicts(
            make_holding["h2_ALL_MUST_output_false"]
        )

    def test_no_contradiction_of_fact(self, make_rule, watt_factor):
        assert not make_rule["h2_MUST"].contradicts(watt_factor["f2"])

    def test_error_for_contradiction_of_predicate(self, make_rule, watt_factor):
        with pytest.raises(TypeError):
            make_rule["h2_MUST"].contradicts(watt_factor["f2"].predicate)


class TestAddition:
    def test_add_factor_to_rule(self, make_complex_rule, make_factor):
        """
        Test that you can make a new version of a :class:`.Rule`,
        with one more input :class:`.Factor`, by using the addition operator with
        the :class:`.Rule` and input :class:`.Factor`.
        """
        c = make_complex_rule
        assert not c["accept_murder_fact_from_relevance"].means(
            c["accept_murder_fact_from_relevance_and_shooting"]
        )
        two_input_rule = (
            c["accept_murder_fact_from_relevance"] + make_factor["f_shooting"]
        )
        assert two_input_rule.means(c["accept_murder_fact_from_relevance_and_shooting"])

    def test_add_factor_to_rule_reverse(self, make_complex_rule, make_factor):
        c = make_complex_rule
        two_input_rule = (
            make_factor["f_shooting"] + c["accept_murder_fact_from_relevance"]
        )
        assert two_input_rule.means(c["accept_murder_fact_from_relevance_and_shooting"])

    def test_add_enactment_to_rule_reverse(self, make_complex_rule, make_enactment):
        """
        Test that you can make a new version of a :class:`.Rule`,
        with one more input :class:`.Factor`, by using the addition operator with
        the :class:`.Rule` and input :class:`.Factor`.
        """
        murder_rule = make_complex_rule["accept_murder_fact_from_relevance"]
        assert make_enactment["due_process_5"] not in murder_rule.enactments
        due_process_murder_rule = make_enactment["due_process_5"] + murder_rule
        assert make_enactment["due_process_5"] in due_process_murder_rule.enactments

    def test_add_enactment_to_rule(self, make_complex_rule, make_enactment):
        """
        Test that you can make a new version of a :class:`.Rule`,
        with one more input :class:`.Factor`, by using the addition operator with
        the :class:`.Rule` and input :class:`.Factor`.
        """
        murder_rule = make_complex_rule["accept_murder_fact_from_relevance"]
        assert make_enactment["due_process_5"] not in murder_rule.enactments
        due_process_murder_rule = murder_rule + make_enactment["due_process_5"]
        assert make_enactment["due_process_5"] in due_process_murder_rule.enactments

    def test_add_simple_rules(self):
        """
        A simple form of two Rules from Feist, with no Enactments.

        Even though the rules have different generic Factors (i.e. Entities),
        the __add__ function will make one Rule using the generic Factors from
        the operand on the left, but will give it the output from the operand
        on the right.
        """
        context = Entity("the Pythagorean theorem")
        three = Entity("the number three")

        fact_not_original = Rule(
            Procedure(
                inputs=Fact(Predicate("{} was a fact"), context_factors=context),
                outputs=Fact(
                    Predicate("{} was an original work", truth=False),
                    context_factors=context,
                ),
            ),
            universal=True,
        )
        unoriginal_not_copyrightable = Rule(
            Procedure(
                inputs=Fact(
                    Predicate("{} was an original work", truth=False),
                    context_factors=three,
                ),
                outputs=Fact(
                    Predicate("{} was copyrightable", truth=False),
                    context_factors=three,
                ),
            ),
            universal=True,
        )

        facts_not_copyrightable = fact_not_original + unoriginal_not_copyrightable
        assert len(facts_not_copyrightable.inputs) == 1
        assert str(facts_not_copyrightable.inputs[0]).endswith(
            "act that <the Pythagorean theorem> was a fact"
        )
        assert len(facts_not_copyrightable.outputs) == 2
        assert str(facts_not_copyrightable.outputs[1]).endswith(
            "false that <the Pythagorean theorem> was copyrightable"
        )

    def test_add_rules_with_duplicate_enactment_text(
        self, make_enactment, make_opinion_with_holding
    ):
        """
        test implication between
        telephone listings -> not original (feist.holdings[11])
        +
        not original -> not copyrightable (feist.holdings[3])
        =
        telephone listings -> not copyrightable

        listings_not_original now has all the Enactments it needs
        on its own. The addition expression should not result in
        duplicated text.
        """
        feist = make_opinion_with_holding["feist_majority"]
        listings_not_original = feist.holdings[10].rule
        inferred_holding = feist.holdings[3].inferred_from_exclusive[0]
        unoriginal_not_copyrightable = inferred_holding.rule
        listings_not_copyrightable = (
            listings_not_original
            + make_enactment["copyright_requires_originality"]
            + unoriginal_not_copyrightable
        )
        assert len(listings_not_copyrightable.inputs) == 1
        assert any(
            out.short_string
            == (
                "absence of the fact that <Rural's telephone listings> were copyrightable"
            )
            for out in listings_not_copyrightable.outputs
        )
        assert (
            listings_not_copyrightable.short_string.count(
                "in accordance with this title"
            )
            == 1
        )

    def test_add_some_plus_some_makes_none(self, make_complex_rule):
        """The rules can't be added because they both have universal==False"""
        new_rule = (
            make_complex_rule["accept_relevance_testimony"]
            + make_complex_rule["accept_murder_fact_from_relevance"]
        )
        assert new_rule is None

    def test_add_complex_rule(self, make_complex_rule):
        """
        The resulting rule will have universal==False because one of the
        two input rules has universal==False.
        """
        new_rule = (
            make_complex_rule["accept_relevance_testimony_ALL"]
            + make_complex_rule["accept_murder_fact_from_relevance"]
        )
        assert new_rule.universal is False
        assert (
            new_rule.inputs
            == make_complex_rule["accept_relevance_testimony_ALL"].inputs
        )
        assert (
            make_complex_rule["accept_murder_fact_from_relevance"].outputs[0]
            in new_rule.outputs
        )

    def test_add_disconnected_rules_returns_none(self, make_rule):
        assert make_rule["h1"] + make_rule["h2_ALL"] is None

    def test_rule_requiring_more_enactments_wont_add(
        self, make_enactment, make_complex_rule
    ):
        """
        This requirement might be changed, so that if the second
        Rule requires more Enactments the method will just assume they're
        available.
        """
        due_process_rule = (
            make_complex_rule["accept_murder_fact_from_relevance"]
            + make_enactment["due_process_5"]
        )
        assert (
            make_complex_rule["accept_relevance_testimony_ALL"] + due_process_rule
            is None
        )


class TestUnion:
    def test_union_contradictory_outputs(self, make_opinion_with_holding):
        """
        Test that even when two Rules don't contradict each other,
        their union will be None if any of their outputs contradict.
        """
        feist = make_opinion_with_holding["feist_majority"]
        assert not feist.holdings[1].contradicts(feist.holdings[2])
        assert feist.holdings[1].outputs[0].contradicts(feist.holdings[2].outputs[0])
        assert feist.holdings[1] | feist.holdings[2] is None

    def test_union_basic(self, make_opinion_with_holding):
        feist = make_opinion_with_holding["feist_majority"]
        new_rule = feist.holdings[0].rule | feist.holdings[2].rule
        assert len(new_rule.inputs) == 2
        assert len(new_rule.outputs) == 1
        assert len(new_rule.enactments) == 4

    def test_union_of_rule_and_holding(self, make_opinion_with_holding):
        feist = make_opinion_with_holding["feist_majority"]
        new_holding = feist.holdings[0].rule | feist.holdings[2]
        assert isinstance(new_holding, Holding)
        assert len(new_holding.inputs) == 2
        assert len(new_holding.outputs) == 1
        assert len(new_holding.enactments) == 4

    def test_union_longer(self, make_opinion_with_holding):
        feist = make_opinion_with_holding["feist_majority"]
        new_rule = feist.holdings[4].rule | feist.holdings[6].rule
        assert len(new_rule.inputs) == 6
        assert len(new_rule.outputs) == 1
        assert len(new_rule.despite) == 1
        assert new_rule.universal is False
        assert new_rule.mandatory is False

    def test_union_same_output(self, make_opinion_with_holding):
        """
        The two Rules being combined both same the same output
        Factor (and they both have only one output Factor).
        The combined Rule should also have just that one
        output Factor.
        """

        lotus = make_opinion_with_holding["lotus_majority"]
        lotus_not_copyrightable = lotus.holdings[6].rule
        feist = make_opinion_with_holding["feist_majority"]
        feist_not_copyrightable = feist.holdings[0].rule
        new_rule = lotus_not_copyrightable | feist_not_copyrightable
        assert len(new_rule.outputs) == 1

    def test_union_implied_but_not_universal_easy(self, make_rule):
        """
        Tests that when you take the union of Rule A with another Rule
        that only differs in that its input Factors are a subset of Rule A's,
        the answer is Rule A.
        """
        assert (make_rule["h1"] | make_rule["h1_easy"]).means(make_rule["h1"])

    def test_union_implied_but_not_universal(self, make_rule):
        """
        This is similar to the test above, except that the first Rule
        also has some generic context Factors that the second
        Rule doesn't.
        """
        a = make_rule["h2_irrelevant_inputs"]
        b = make_rule["h2"]
        assert (a | b).means(a)

    def test_union_implied_change_context(self, make_rule):
        """
        The correct Entities need to be assigned to the context factors
        in a new Procedure created with the __or__ method.
        """
        original_on_left = make_rule["h1_easy"] | make_rule["h1_entity_order"]
        assert "act that <Hideaway Lodge> was <Wattenburg>’s abode" in str(
            original_on_left
        )

    def test_union_implied_change_context_reverse(self, make_rule):
        original_on_right = make_rule["h1_entity_order"] | make_rule["h1_easy"]
        assert "that <Wattenburg> was <Hideaway Lodge>’s abode" in str(
            original_on_right
        )

    def test_union_change_context(self, make_opinion_with_holding):
        """
        When the union operation is applied to the Rules, a fact that
        related to <the Java API> in the original is mentioned relating
        to <the Lotus menu command hierarchy> instead.
        """

        lotus = make_opinion_with_holding["lotus_majority"]
        oracle = make_opinion_with_holding["oracle_majority"]
        # changing one of the Rules to universal because otherwise
        # nothing can be inferred by their union.
        lotus_4 = lotus.holdings[2].rule.evolve("universal")
        new = lotus_4 | oracle.holdings[2].rule
        assert new.mandatory is False
        assert (
            "<the Lotus menu command hierarchy> was the expression of an idea"
            in new.short_string
        )

    def test_union_one_generic_not_matched(self, make_opinion_with_holding):
        """
        Here, both Rules have the input "fact that <> was a computer program".
        But they each have another generic that can't be matched:
        fact that <the Java API> was a literal element of <the Java language>
        and
        fact that <the Lotus menu command hierarchy> provided the means by
        which users controlled and operated <Lotus 1-2-3>
        """
        lotus = make_opinion_with_holding["lotus_majority"]
        oracle = make_opinion_with_holding["oracle_majority"]
        new = lotus.holdings[7].rule | oracle.holdings[3].rule
        text = (
            "that <the Lotus menu command hierarchy> was a "
            "literal element of <Lotus 1-2-3>"
        )
        assert text in new.short_string

    def test_union_returns_universal(self, make_rule):
        """
        an ALL rule should be
        returned even though ``implied`` is SOME, because
        ``implied`` contributes no information that wasn't
        already in ``greater``.
        """
        new_rule = make_rule["h2_ALL_due_process"] | make_rule["h2"]
        assert len(new_rule.enactments) == 2
        assert new_rule.universal

    def test_union_inconsistent_outputs(self, make_opinion_with_holding):
        """
        The union operator should return a rule with all the inputs of both Rules
        (including input Enactments) and all the outputs of both Rules.

        This returns None because the outputs are inconsistent
        (True and False versions of the same Rule)
        """
        feist = make_opinion_with_holding["feist_majority"]
        feist_copyrightable = feist.holdings[3].rule
        oracle = make_opinion_with_holding["oracle_majority"]
        oracle_copyrightable = oracle.holdings[0].rule
        assert feist_copyrightable | oracle_copyrightable is None


class TestStatuteRules:
    """
    Tests from the statute_rules Jupyter Notebook.
    """

    def test_greater_than_implies_equal(self, make_code, make_beard_rule):
        beard_act = make_code["beard_act"]
        beard_dictionary = loaders.load_holdings("beard_rules.json")
        beard_dictionary[0]["inputs"][1][
            "content"
        ] = "the length of the suspected beard was = 8 millimetres"
        longer_hair_rule = readers.read_rule(beard_dictionary[0], beard_act)
        assert make_beard_rule[0].implies(longer_hair_rule)

    def test_greater_than_contradicts_not_greater(self, make_code, make_beard_rule):
        beard_act = make_code["beard_act"]
        beard_dictionary = loaders.load_holdings("beard_rules.json")
        beard_dictionary[1]["inputs"][1][
            "content"
        ] = "the length of the suspected beard was >= 12 inches"
        beard_dictionary[1]["outputs"][0]["truth"] = False
        beard_dictionary[1]["mandatory"] = True
        long_hair_is_not_a_beard = readers.read_rule(beard_dictionary[1], beard_act)
        assert make_beard_rule[1].contradicts(long_hair_is_not_a_beard)

    def test_contradictory_fact_about_beard_length(self, make_code, make_beard_rule):
        beard_act = make_code["beard_act"]
        beard_dictionary = loaders.load_holdings("beard_rules.json")
        beard_dictionary[1]["despite"] = beard_dictionary[1]["inputs"][0]
        beard_dictionary[1]["inputs"] = {
            "type": "fact",
            "content": "the length of the suspected beard was >= 12 inches",
        }
        beard_dictionary[1]["outputs"][0]["truth"] = False
        beard_dictionary[1]["mandatory"] = True
        long_thing_is_not_a_beard = readers.read_rule(beard_dictionary[1], beard_act)
        assert make_beard_rule[1].contradicts(long_thing_is_not_a_beard)

    def test_contradictory_fact_about_beard_length_reverse(
        self, make_code, make_beard_rule
    ):
        beard_act = make_code["beard_act"]
        beard_dictionary = loaders.load_holdings("beard_rules.json")
        beard_dictionary[1]["despite"] = beard_dictionary[1]["inputs"][0]
        beard_dictionary[1]["inputs"] = {
            "type": "fact",
            "content": "the length of the suspected beard was >= 12 inches",
        }
        beard_dictionary[1]["outputs"][0]["truth"] = False
        beard_dictionary[1]["mandatory"] = True
        long_thing_is_not_a_beard = readers.read_rule(beard_dictionary[1], beard_act)
        assert long_thing_is_not_a_beard.contradicts(make_beard_rule[1])

    @pytest.mark.parametrize(
        (
            "facial_hair_over_5mm, facial_hair_on_or_below_chin, "
            "facial_hair_uninterrupted, outcome"
        ),
        (
            [False, False, True, False],
            [False, False, False, False],
            [False, True, False, False],
            [False, True, True, False],
            [True, False, True, True],
            [True, False, False, False],
            [True, True, True, True],
            [True, True, None, True],
            [True, None, True, True],
        ),
    )
    def test_is_beard_implied(
        self,
        facial_hair_over_5mm,
        facial_hair_on_or_below_chin,
        facial_hair_uninterrupted,
        outcome,
        make_beard_rule,
        make_code,
    ):
        beard = Entity("a facial feature")

        hypothetical = Rule(
            procedure=Procedure(
                inputs=[
                    Fact(Predicate("{} was facial hair"), context_factors=beard),
                    Fact(
                        Predicate(
                            "the length of {} was {}",
                            comparison=">=",
                            quantity=Q_("5 millimeters"),
                            truth=facial_hair_over_5mm,
                        ),
                        context_factors=beard,
                    ),
                    Fact(
                        Predicate(
                            "{} occurred on or below the chin",
                            truth=facial_hair_on_or_below_chin,
                        ),
                        context_factors=beard,
                    ),
                    Fact(
                        Predicate(
                            "{} existed in an uninterrupted line from the front "
                            "of one ear to the front of the other ear below the nose",
                            truth=facial_hair_uninterrupted,
                        ),
                        context_factors=beard,
                    ),
                ],
                outputs=Fact(Predicate("{} was a beard"), context_factors=beard),
            ),
            enactments=Enactment(
                source="/au/act/1934/47/1/4/", code=make_code["beard_act"]
            ),
        )
        meets_chin_test = make_beard_rule[0].implies(hypothetical)
        meets_ear_test = make_beard_rule[1].implies(hypothetical)
        assert outcome == meets_chin_test or meets_ear_test

    def test_adding_definition_of_transfer(self, make_beard_rule):
        loan_is_transfer = make_beard_rule[7]
        elements_of_offense = make_beard_rule[11]
        loan_without_exceptions = (
            loan_is_transfer
            + elements_of_offense.inputs[1]
            + elements_of_offense.inputs[2]
            + elements_of_offense.enactments[1]
        )
        combined = loan_without_exceptions + elements_of_offense
        assert combined
