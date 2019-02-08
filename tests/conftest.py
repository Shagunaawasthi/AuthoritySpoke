import json
from typing import Dict

from pint import UnitRegistry
import pytest

from enactments import Code, Enactment
from spoke import Entity, Event, Human
from spoke import Predicate, Factor, Fact, Evidence
from spoke import Procedure, Rule, ProceduralRule
from spoke import Opinion, opinion_from_file
from spoke import ureg, Q_


@pytest.fixture(scope="class")
def make_entity() -> Dict[str, Entity]:
    return {
        "e_motel": Entity("Hideaway Lodge"),
        "e_motel_specific": Entity("Hideaway Lodge", generic=False),
        "e_watt": Human("Wattenburg"),
        "e_trees": Entity("the stockpile of trees"),
        "e_trees_specific": Entity("the stockpile of trees", generic=False),
        "e_tree_search": Event(
            "officers' search of the stockpile of trees"
            ),
    }


@pytest.fixture(scope="class")
def make_predicate() -> Dict[str, Predicate]:

    return {
        "p1": Predicate("{} was a motel"),
        "p1_again": Predicate("{} was a motel"),
        "p2": Predicate("{} operated and lived at {}"),
        "p2_reciprocal": Predicate("{} operated and lived at {}", reciprocal=True),
        "p2_no_truth": Predicate("{} operated and lived at {}", truth=None),
        "p2_false": Predicate("{} operated and lived at {}", truth=False),
        "p3": Predicate("{} was {}’s abode"),
        "p3_false": Predicate("{} was {}’s abode", truth=False),
        "p4": Predicate("{} was on the premises of {}"),
        "p5": Predicate("{} was a stockpile of Christmas trees"),
        "p6": Predicate("{} was among some standing trees"),
        "p7": Predicate(
            "The distance between {} and {} was {}",
            truth=False,
            reciprocal=True,
            comparison=">",
            quantity=Q_("35 feet"),
        ),
        "p7_obverse": Predicate(
            "The distance between {} and {} was {}",
            truth=True,
            reciprocal=True,
            comparison="<=",
            quantity=Q_("35 feet"),
        ),
        "p7_opposite": Predicate(
            "The distance between {} and {} was {}",
            truth=True,
            reciprocal=True,
            comparison=">",
            quantity=Q_("35 feet"),
        ),
        "p7_true": Predicate(
            "The distance between {} and {} was {}",
            truth=True,
            reciprocal=True,
            comparison="<",
            quantity=Q_("35 feet"),
        ),
        "p8": Predicate(
            "The distance between {} and {} was {}",
            reciprocal=True,
            comparison=">=",
            quantity=Q_("20 feet"),
        ),
        "p8_exact": Predicate(
            "The distance between {} and {} was {}",
            reciprocal=True,
            comparison="=",
            quantity=Q_("25 feet"),
        ),
        "p8_less": Predicate(
            "The distance between {} and {} was {}",
            reciprocal=True,
            comparison="<=",
            quantity=Q_("20 feet"),
        ),
        "p8_meters": Predicate(
            "The distance between {} and {} was {}",
            reciprocal=True,
            comparison=">=",
            quantity=Q_("10 meters"),
        ),
        "p8_int": Predicate(
            "The distance between {} and {} was {}",
            reciprocal=True,
            comparison=">=",
            quantity=20,
        ),
        "p8_float": Predicate(
            "The distance between {} and {} was {}",
            reciprocal=True,
            comparison=">=",
            quantity=20.0,
        ),
        "p8_higher_int": Predicate(
            "The distance between {} and {} was {}",
            reciprocal=True,
            comparison=">=",
            quantity=30,
        ),
        "p9": Predicate(
            "The distance between {} and a parking area used by personnel and patrons of {} was {}",
            comparison="<=",
            quantity=Q_("5 feet"),
        ),
        "p9_miles": Predicate(
            "The distance between {} and a parking area used by personnel and patrons of {} was {}",
            comparison="<=",
            quantity=Q_("5 miles"),
        ),
        "p9_acres": Predicate(
            "The distance between {} and a parking area used by personnel and patrons of {} was {}",
            comparison="<=",
            quantity=Q_("5 acres"),
        ),
        "p10": Predicate("{} was within the curtilage of {}"),
        "p10_false": Predicate("{} was within the curtilage of {}", truth=False),
        "p11": Predicate("{} was a warrantless search and seizure"),
        "p12": Predicate("{} was performed by federal law enforcement officers"),
        "p13": Predicate("{} constituted an intrusion upon {}"),
        "p14": Predicate("{} sought to preserve {} as private"),
        "p15": Predicate("{} was in an area adjacent to {}"),
        "p16": Predicate("{} was in an area accessible to the public"),
        "p17": Predicate(
            "In {}, several law enforcement officials meticulously went through {}"
        ),
        "p18": Predicate(
            "{} continued for {}", comparison=">=", quantity=Q_("385 minutes")
        ),
        "p19": Predicate("{} continued after night fell"),
        # Use the irrelevant predicates/factors to make sure they don't affect an outcome.
        "p_irrelevant_0": Predicate("{} was a clown"),
        "p_irrelevant_1": Predicate("{} was a bear"),
        "p_irrelevant_2": Predicate("{} was a circus"),
        "p_irrelevant_3": Predicate("{} performed at {}"),
        "p_crime": Predicate("{} commited a crime"),
        "p_shooting": Predicate("{} shot {}"),
        "p_no_shooting": Predicate("{} shot {}", truth=False),
        "p_no_crime": Predicate("{} commited a crime", truth=False),
        "p_three_entities": Predicate("{} threw {} to {}"),
    }


@pytest.fixture(scope="class")
def make_factor(make_predicate) -> Dict[str, Factor]:
    p = make_predicate

    return {
        "f1": Fact(p["p1"]),
        "f1_entity_order": Fact(p["p1"], (1,)),
        "f1b": Fact(p["p1"]),
        "f1c": Fact(p["p1_again"]),
        "f2": Fact(p["p2"], (1, 0)),
        "f2_preponderance_of_evidence": Fact(
            p["p2"], (1, 0), standard_of_proof="preponderance of evidence"
        ),
        "f2_clear_and_convincing": Fact(
            p["p2"], (1, 0), standard_of_proof="clear and convincing"
        ),
        "f2_beyond_reasonable_doubt": Fact(
            p["p2"], (1, 0), standard_of_proof="beyond reasonable doubt"
        ),
        "f2_entity_order": Fact(p["p2"]),
        "f2_no_truth": Fact(p["p2_no_truth"]),
        "f2_false": Fact(p["p2_false"]),
        "f2_reciprocal": Fact(p["p2_reciprocal"]),
        "f3": Fact(p["p3"]),
        "f3_entity_order": Fact(p["p3"], (1, 0)),
        "f3_absent": Fact(p["p3"], absent=True),
        "f4": Fact(p["p4"]),
        "f4_h4": Fact(p["p4"], (3, 0)),
        "f4_swap_entities": Fact(p["p4"], (1, 0)),
        "f4_swap_entities_4": Fact(p["p4"], (1, 4)),
        "f5": Fact(p["p5"]),
        "f5_h4": Fact(p["p5"], (3,)),
        "f5_swap_entities": Fact(p["p5"], (1,)),
        "f6": Fact(p["p6"]),
        "f6_swap_entities": Fact(p["p6"], (1,)),
        "f7": Fact(p["p7"]),
        "f7_swap_entities": Fact(p["p7"], (1, 0)),
        "f7_swap_entities_4": Fact(p["p7"], (1, 4)),
        "f7_true": Fact(p["p7_true"]),
        "f8": Fact(p["p8"]),
        "f8_absent": Fact(p["p8"], absent=True),
        "f8_exact": Fact(p["p8_exact"]),
        "f8_exact_swap_entities": Fact(p["p8_exact"], (1, 0)),
        "f8_float": Fact(p["p8_float"]),
        "f8_higher_int": Fact(p["p8_higher_int"]),
        "f8_int": Fact(p["p8_int"]),
        "f8_less": Fact(p["p8_less"]),
        "f8_meters": Fact(p["p8_meters"]),
        "f9": Fact(p["p9"]),
        "f9_absent": Fact(p["p9"], absent=True),
        "f9_absent_miles": Fact(p["p9_miles"], absent=True),
        "f9_swap_entities": Fact(p["p9"], (1, 0)),
        "f9_swap_entities_4": Fact(p["p9"], (1, 4)),
        "f10": Fact(p["p10"]),
        "f10_absent": Fact(p["p10"], absent=True),
        "f10_false": Fact(p["p10_false"]),
        "f10_absent_false": Fact(p["p10_false"], absent=True),
        "f10_swap_entities": Fact(p["p10"], (1, 0)),
        "f10_swap_entities_4": Fact(p["p10"], (1, 4)),
        "f11": Fact(p["p11"], 2),
        "f12": Fact(p["p12"], 2),
        "f13": Fact(p["p13"], (2, 3)),
        "f14": Fact(p["p14"], (1, 3)),
        "f15": Fact(p["p15"], (3, 0)),
        "f16": Fact(p["p16"], 3),
        "f17": Fact(p["p17"], (2, 3)),
        "f18": Fact(p["p18"], 2),
        "f19": Fact(p["p19"], 2),
        "f_irrelevant_0": Fact(p["p_irrelevant_0"], (2,)),
        "f_irrelevant_1": Fact(p["p_irrelevant_1"], (3,)),
        "f_irrelevant_2": Fact(p["p_irrelevant_2"], (4,)),
        "f_irrelevant_3": Fact(p["p_irrelevant_3"], (2, 4)),
        "f_irrelevant_3_new_context": Fact(p["p_irrelevant_3"], (3, 4)),
        "f_irrelevant_3_context_0": Fact(p["p_irrelevant_3"], (3, 0)),
        "f_crime": Fact(p["p_crime"]),
        "f_no_crime": Fact(p["p_no_crime"]),
        "f_no_crime_entity_order": Fact(p["p_no_crime"], (1,)),
        "f_shooting": Fact(p["p_shooting"]),
        "f_no_shooting": Fact(p["p_no_shooting"]),
        "f_no_shooting_entity_order": Fact(p["p_no_shooting"], (1, 0)),
        "f_three_entities": Fact(p["p_three_entities"], (0, 1, 2)),
        "f_repeating_entity": Fact(p["p_three_entities"], (0, 1, 0)),
    }


@pytest.fixture(scope="class")
def make_evidence(make_predicate, make_factor) -> Dict[str, Evidence]:
    p = make_predicate
    f = make_factor
    return {
        "e_shooting": Evidence(
            form="testimony",
            to_effect=f["f_crime"],
            statement=f["f_shooting"],
            stated_by=0,
        ),
        "e_no_shooting": Evidence(
            form="testimony",
            to_effect=f["f_no_crime"],
            statement=f["f_no_shooting"],
            stated_by=0,
        ),
        "e_no_shooting_absent": Evidence(
            form="testimony",
            to_effect=f["f_no_crime"],
            statement=f["f_no_shooting"],
            stated_by=0,
            absent=True,
        ),
        "e_no_shooting_entity_order": Evidence(
            form="testimony",
            to_effect=f["f_no_crime_entity_order"],
            statement=f["f_no_shooting_entity_order"],
            stated_by=1,
        ),
        "e_no_shooting_witness_unknown": Evidence(
            form="testimony", to_effect=f["f_no_crime"], statement=f["f_no_shooting"]
        ),
        "e_no_shooting_witness_unknown_absent": Evidence(
            form="testimony",
            to_effect=f["f_no_crime"],
            statement=f["f_no_shooting"],
            absent=True,
        ),
        "e_no_shooting_no_effect_entity_order": Evidence(
            form="testimony", statement=f["f_no_shooting_entity_order"], stated_by=1
        ),
        "e_no_shooting_derived_from_entity_order": Evidence(
            form="testimony", statement=f["f_no_shooting_entity_order"], derived_from=1
        ),
        "e_no_shooting_different_witness": Evidence(
            form="testimony",
            to_effect=f["f_no_crime"],
            statement=f["f_no_shooting"],
            stated_by=1,
        ),
        "e_reciprocal": Evidence(
            form="testimony", to_effect=f["f_no_crime"], statement=f["f7"], stated_by=2
        ),
        "e_crime": Evidence(to_effect=f["f_crime"], derived_from=2),
        "e_crime_absent": Evidence(to_effect=f["f_crime"], derived_from=2, absent=True),
    }


@pytest.fixture(scope="module")
def make_code() -> Dict[str, Code]:
    return {"const": Code("constitution.xml")}


@pytest.fixture(scope="module")
def make_enactment(make_code) -> Dict[str, Enactment]:
    const = make_code["const"]

    return {
        "search_clause": Enactment(const, "amendment-IV", end="violated"),
        "fourth_a": Enactment(const, "amendment-IV"),
        "due_process_5": Enactment(
            const,
            "amendment-V",
            start="life, liberty, or property",
            end="due process of law",
        ),
        "due_process_14": Enactment(
            const,
            "amendment-XIV-1",
            start="life, liberty, or property",
            end="due process of law",
        ),
    }


@pytest.fixture(scope="class")
def make_procedure(make_evidence, make_factor) -> Dict[str, Procedure]:
    e = make_evidence
    f = make_factor

    return {
        "c1": Procedure(outputs=(f["f3"],), inputs=(f["f1"], f["f2"])),
        "c2": Procedure(
            outputs=(f["f10"],),
            inputs=(f["f4"], f["f5"], f["f6"], f["f7"], f["f9"]),
            despite=(f["f8"],),
        ),
        "c3": Procedure(
            outputs=e["e_crime_absent"],
            inputs=(f["f3"], f["f11"], f["f12"], f["f13"], f["f14"], f["f15"]),
            despite=(f["f16"]),
        ),
        "c4": Procedure(
            outputs=f["f13"],
            inputs=(f["f1"], f["f2"], f["f4_h4"], f["f5_h4"], f["f11"], f["f12"], f["f17"], f["f18"], f["f19"]),
        ),
        "c1_again": Procedure(outputs=(f["f3"],), inputs=(f["f1"], f["f2"])),
        "c1_entity_order": Procedure(
            outputs=(f["f3_entity_order"],),
            inputs=(f["f2_entity_order"], f["f1_entity_order"]),
        ),
        "c1_easy": Procedure(outputs=(f["f3"],), inputs=(f["f2"])),
        "c2_absent_despite": Procedure(
            outputs=(f["f10"],),
            inputs=(f["f4"], f["f5"], f["f6"], f["f7"]),
            despite=(f["f8_exact"], f["f9_absent"]),
        ),
        "c2_exact_quantity": Procedure(
            outputs=(f["f10"],),
            inputs=(f["f4"], f["f5"], f["f6"], f["f8_exact"], f["f9"]),
        ),
        "c2_higher_quantity": Procedure(
            outputs=(f["f10"],),
            inputs=(f["f4"], f["f5"], f["f6"], f["f7"], f["f8_higher_int"], f["f9"]),
        ),
        "c2_exact_in_despite": Procedure(
            outputs=(f["f10"],),
            inputs=(f["f4"], f["f5"], f["f6"], f["f7"], f["f9"]),
            despite=(f["f8_exact"],),
        ),
        "c2_exact_in_despite_entity_order": Procedure(
            outputs=(f["f10_swap_entities"],),
            inputs=(
                f["f4_swap_entities"],
                f["f5_swap_entities"],
                f["f6_swap_entities"],
                f["f7_swap_entities"],
                f["f9_swap_entities"],
            ),
            despite=(f["f8_exact_swap_entities"],),
        ),
        "c2_irrelevant_inputs": Procedure(
            outputs=(f["f10"],),
            inputs=(
                f["f4"],
                f["f5"],
                f["f6"],
                f["f7"],
                f["f9"],
                f["f_irrelevant_0"],
                f["f_irrelevant_1"],
                f["f_irrelevant_2"],
                f["f_irrelevant_3"],
                f["f_irrelevant_3_new_context"],
            ),
            despite=(f["f8"],),
        ),
        "c2_irrelevant_outputs": Procedure(
            outputs=(
                f["f10_swap_entities_4"],
                f["f_irrelevant_0"],
                f["f_irrelevant_1"],
                f["f_irrelevant_2"],
                f["f_irrelevant_3"],
                f["f_irrelevant_3_context_0"],
            ),
            inputs=(
                f["f4_swap_entities_4"],
                f["f5_swap_entities"],
                f["f6_swap_entities"],
                f["f7_swap_entities_4"],
                f["f9_swap_entities_4"],
            ),
        ),
        "c2_irrelevant_despite": Procedure(
            outputs=(f["f10"],),
            inputs=(f["f4"], f["f5"], f["f6"], f["f7"], f["f9"]),
            despite=(
                f["f8"],
                f["f_irrelevant_0"],
                f["f_irrelevant_1"],
                f["f_irrelevant_2"],
                f["f_irrelevant_3"],
                f["f_irrelevant_3_new_context"],
            ),
        ),
        "c2_reciprocal_swap": Procedure(
            outputs=(f["f10"],),
            inputs=(f["f4"], f["f5"], f["f6"], f["f7_swap_entities"], f["f9"]),
            despite=(f["f8"],),
        ),
        "c2_nonreciprocal_swap": Procedure(
            outputs=(f["f10"],),
            inputs=(f["f4_swap_entities"], f["f5"], f["f6"], f["f7"], f["f9"]),
            despite=(f["f8"],),
        ),
        "c2_broad_output": Procedure(
            outputs=(f["f8_int"],), inputs=(f["f4"], f["f5"], f["f6"], f["f7"], f["f9"])
        ),
        "c2_narrow_output": Procedure(
            outputs=(f["f8_higher_int"],),
            inputs=(f["f4"], f["f5"], f["f6"], f["f7"], f["f9"]),
        ),
        "c2_output_absent": Procedure(
            outputs=(f["f10_absent"],),
            inputs=(f["f4"], f["f5"], f["f6"], f["f7"], f["f9"]),
            despite=(f["f8"],),
        ),
        "c2_output_false": Procedure(
            outputs=(f["f10_false"],),
            inputs=(f["f4"], f["f5"], f["f6"], f["f7"], f["f9"]),
            despite=(f["f8"],),
        ),
        "c2_output_absent_false": Procedure(
            outputs=(f["f10_absent_false"],),
            inputs=(f["f4"], f["f5"], f["f6"], f["f7"], f["f9"]),
            despite=(f["f8"],),
        ),
        "c_near_means_no_curtilage": Procedure(
            outputs=(f["f10_false"],), inputs=(f["f7_true"])
        ),
        "c_nearer_means_curtilage": Procedure(
            outputs=(f["f10"],), inputs=(f["f8_less"])
        ),
        "c_near_means_curtilage": Procedure(outputs=(f["f10"],), inputs=(f["f7"])),
        "c_near_means_curtilage_even_if": Procedure(
            outputs=(f["f10"],), inputs=(f["f7"]), despite=(f["f8"])
        ),
        "c_far_means_no_curtilage": Procedure(
            outputs=(f["f10_false"],), inputs=(f["f8"])
        ),
        "c3_fewer_inputs": Procedure(
            outputs=e["e_crime_absent"],
            inputs=(f["f3"], f["f11"], f["f12"], f["f15"]),
            despite=(f["f16"]),
        ),
    }


@pytest.fixture(scope="class")
def real_holding(make_procedure, make_enactment) -> Dict[str, ProceduralRule]:
    """These holdings can be changed in case they don't accurately reflect
    what's in real cases, or in case there are API improvements that
    allow them to become more accurate. I'll try not to write any tests
    that depend on them remaining the same."""

    c = make_procedure
    e = make_enactment

    return {
        "h1": ProceduralRule(c["c1"], enactments=e["search_clause"], mandatory=True),
        "h2": ProceduralRule(c["c2"], enactments=e["search_clause"], mandatory=True),
        "h3": ProceduralRule(c["c3"], enactments=e["search_clause"], mandatory=True),
        "h4": ProceduralRule(c["c4"], enactments=e["search_clause"], mandatory=True),
    }


@pytest.fixture(scope="class")
def make_holding(make_procedure, make_enactment) -> Dict[str, ProceduralRule]:
    c = make_procedure
    e = make_enactment

    return {
        "h1": ProceduralRule(c["c1"], enactments=e["search_clause"]),
        "h2": ProceduralRule(c["c2"], enactments=e["search_clause"]),
        "h3": ProceduralRule(c["c3"], enactments=e["search_clause"]),
        "h1_again": ProceduralRule(c["c1"], enactments=e["search_clause"]),
        "h1_entity_order": ProceduralRule(
            c["c1_entity_order"], enactments=e["search_clause"]
        ),
        "h1_easy": ProceduralRule(c["c1_easy"], enactments=e["search_clause"]),
        "h1_opposite": ProceduralRule(
            c["c1"], enactments=e["search_clause"], rule_valid=False
        ),
        "h2_without_cite": ProceduralRule(c["c2"]),
        "h2_fourth_a_cite": ProceduralRule(c["c2"], enactments=e["fourth_a"]),
        "h2_despite_due_process": ProceduralRule(
            c["c2"],
            enactments=e["search_clause"],
            enactments_despite=e["due_process_5"],
        ),
        "h2_ALL_due_process": ProceduralRule(
            c["c2"],
            enactments=(e["search_clause"], e["due_process_5"]),
            mandatory=False,
            universal=True,
            rule_valid=True,
        ),
        "h2_ALL_due_process_invalid": ProceduralRule(
            c["c2"],
            enactments=(e["search_clause"], e["due_process_5"]),
            mandatory=False,
            universal=True,
            rule_valid=False,
        ),
        "h2_ALL": ProceduralRule(
            c["c2"], enactments=e["search_clause"], mandatory=False, universal=True
        ),
        "h2_ALL_invalid": ProceduralRule(
            c["c2"],
            enactments=e["search_clause"],
            mandatory=False,
            universal=True,
            rule_valid=False,
        ),
        "h2_ALL_MAY_output_false": ProceduralRule(
            c["c2_output_false"],
            enactments=e["search_clause"],
            mandatory=False,
            universal=True,
        ),
        "h2_ALL_MUST": ProceduralRule(
            c["c2"], enactments=e["search_clause"], mandatory=True, universal=True
        ),
        "h2_ALL_MUST_output_false": ProceduralRule(
            c["c2_output_false"],
            enactments=e["search_clause"],
            mandatory=True,
            universal=True,
        ),
        "h2_exact_quantity": ProceduralRule(
            c["c2_exact_quantity"], enactments=e["search_clause"]
        ),
        "h2_invalid": ProceduralRule(
            c["c2"], enactments=e["search_clause"], rule_valid=False
        ),
        "h2_irrelevant_inputs": ProceduralRule(
            c["c2_irrelevant_inputs"], enactments=e["search_clause"]
        ),
        "h2_irrelevant_inputs_invalid": ProceduralRule(
            c["c2_irrelevant_inputs"], enactments=e["search_clause"], rule_valid=False
        ),
        "h2_irrelevant_inputs_ALL_MUST": ProceduralRule(
            c["c2_irrelevant_inputs"],
            enactments=e["search_clause"],
            mandatory=True,
            universal=True,
        ),
        "h2_irrelevant_inputs_ALL_MUST_invalid": ProceduralRule(
            c["c2_irrelevant_inputs"],
            enactments=e["search_clause"],
            mandatory=True,
            universal=True,
            rule_valid=False,
        ),
        "h2_irrelevant_inputs_ALL_invalid": ProceduralRule(
            c["c2_irrelevant_inputs"],
            enactments=e["search_clause"],
            universal=True,
            rule_valid=False,
        ),
        "h2_irrelevant_inputs_MUST": ProceduralRule(
            c["c2_irrelevant_inputs"], enactments=e["search_clause"], mandatory=True
        ),
        "h2_irrelevant_inputs_MUST_invalid": ProceduralRule(
            c["c2_irrelevant_inputs"],
            enactments=e["search_clause"],
            mandatory=True,
            rule_valid=False,
        ),
        "h2_reciprocal_swap": ProceduralRule(
            c["c2_reciprocal_swap"], enactments=e["search_clause"]
        ),
        "h2_exact_in_despite": ProceduralRule(
            c["c2_exact_in_despite"], enactments=e["search_clause"]
        ),
        "h2_exact_in_despite_ALL": ProceduralRule(
            c["c2_exact_in_despite"],
            enactments=e["search_clause"],
            mandatory=False,
            universal=True,
        ),
        "h2_exact_in_despite_ALL_entity_order": ProceduralRule(
            c["c2_exact_in_despite_entity_order"],
            enactments=e["search_clause"],
            mandatory=False,
            universal=True,
        ),
        "h2_exact_quantity_ALL": ProceduralRule(
            c["c2_exact_quantity"],
            enactments=e["search_clause"],
            mandatory=False,
            universal=True,
        ),
        "h2_invalid_undecided": ProceduralRule(
            c["c2"], enactments=e["search_clause"], rule_valid=False, decided=False
        ),
        "h2_MUST": ProceduralRule(
            c["c2"], enactments=e["search_clause"], mandatory=True, universal=False
        ),
        "h2_MUST_invalid": ProceduralRule(
            c["c2"], enactments=e["search_clause"], mandatory=True, rule_valid=False
        ),
        "h2_output_absent": ProceduralRule(
            c["c2_output_absent"], enactments=e["search_clause"]
        ),
        "h2_output_false": ProceduralRule(
            c["c2_output_false"], enactments=e["search_clause"]
        ),
        "h2_output_false_ALL": ProceduralRule(
            c["c2_output_false"], enactments=e["search_clause"], universal=True
        ),
        "h2_output_absent_false": ProceduralRule(
            c["c2_output_absent_false"], enactments=e["search_clause"]
        ),
        "h2_SOME_MUST_output_false": ProceduralRule(
            c["c2_output_false"],
            enactments=e["search_clause"],
            mandatory=True,
            universal=False,
        ),
        "h2_SOME_MUST_output_absent": ProceduralRule(
            c["c2_output_absent"],
            enactments=e["search_clause"],
            mandatory=True,
            universal=False,
        ),
        "h2_undecided": ProceduralRule(
            c["c2"], enactments=e["search_clause"], decided=False
        ),
        "h2_irrelevant_inputs_undecided": ProceduralRule(
            c["c2_irrelevant_inputs"], enactments=e["search_clause"], decided=False
        ),
        "h2_MUST_undecided": ProceduralRule(
            c["c2"], enactments=e["search_clause"], mandatory=True, decided=False
        ),
        "h3_ALL": ProceduralRule(
            c["c3"], enactments=e["search_clause"], universal=True
        ),
        "h3_fewer_inputs": ProceduralRule(
            c["c3_fewer_inputs"], enactments=e["search_clause"]
        ),
        "h3_undecided": ProceduralRule(
            c["c3"], enactments=e["search_clause"], decided=False
        ),
        "h3_ALL_undecided": ProceduralRule(
            c["c3"], enactments=e["search_clause"], decided=False, universal=True
        ),
        "h3_fewer_inputs_ALL": ProceduralRule(
            c["c3_fewer_inputs"], enactments=e["search_clause"], universal=True
        ),
        "h3_fewer_inputs_undecided": ProceduralRule(
            c["c3_fewer_inputs"], enactments=e["search_clause"], decided=False
        ),
        "h3_fewer_inputs_ALL_undecided": ProceduralRule(
            c["c3_fewer_inputs"],
            enactments=e["search_clause"],
            universal=True,
            decided=False,
        ),
        "h_near_means_curtilage": ProceduralRule(
            c["c_near_means_curtilage"], enactments=e["search_clause"]
        ),
        "h_near_means_curtilage_even_if": ProceduralRule(
            c["c_near_means_curtilage_even_if"], enactments=e["search_clause"]
        ),
        "h_near_means_curtilage_ALL_MUST": ProceduralRule(
            c["c_near_means_curtilage"],
            enactments=e["search_clause"],
            mandatory=True,
            universal=True,
        ),
        "h_near_means_curtilage_ALL_undecided": ProceduralRule(
            c["c_near_means_curtilage"],
            enactments=e["search_clause"],
            universal=True,
            decided=False,
        ),
        "h_near_means_no_curtilage": ProceduralRule(
            c["c_near_means_no_curtilage"], enactments=e["search_clause"]
        ),
        "h_near_means_no_curtilage_ALL": ProceduralRule(
            c["c_near_means_no_curtilage"],
            enactments=e["search_clause"],
            universal=True,
        ),
        "h_near_means_no_curtilage_ALL_MUST": ProceduralRule(
            c["c_near_means_no_curtilage"],
            enactments=e["search_clause"],
            mandatory=True,
            universal=True,
        ),
        "h_nearer_means_curtilage": ProceduralRule(
            c["c_nearer_means_curtilage"], enactments=e["search_clause"]
        ),
        "h_nearer_means_curtilage_ALL": ProceduralRule(
            c["c_nearer_means_curtilage"], enactments=e["search_clause"], universal=True
        ),
        "h_nearer_means_curtilage_MUST": ProceduralRule(
            c["c_nearer_means_curtilage"], enactments=e["search_clause"], mandatory=True
        ),
        "h_far_means_no_curtilage": ProceduralRule(c["c_far_means_no_curtilage"]),
        "h_far_means_no_curtilage_ALL": ProceduralRule(
            c["c_far_means_no_curtilage"], enactments=e["search_clause"], universal=True
        ),
    }


@pytest.fixture(scope="class")
def make_opinion(make_entity, real_holding) -> Dict[str, Opinion]:
    h = real_holding
    e = make_entity

    test_cases = ("brad", "cardenas", "watt")
    opinions = {}
    for case in test_cases:
        for opinion in opinion_from_file(f"json/{case}_h.json"):
            opinions[f"{case}_{opinion.position}"] = opinion
    opinions["watt_majority"].posits(h["h1"], (e["e_motel"], e["e_watt"]))
    opinions["watt_majority"].posits(h["h2"], (e["e_trees"], e["e_motel"]))
    opinions["watt_majority"].posits(h["h3"], (e["e_motel"], e["e_watt"],
            e["e_tree_search"], e["e_trees"],))
    opinions["watt_majority"].posits(h["h4"], (e["e_motel"], e["e_watt"],
            e["e_tree_search"], e["e_trees"],))
    return opinions