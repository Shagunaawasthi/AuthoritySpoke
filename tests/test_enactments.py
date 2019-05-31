import datetime
import json
import operator

from pint import UnitRegistry
import pytest

from authorityspoke.entities import Human, Event
from authorityspoke.enactments import Code, Enactment
from authorityspoke.opinions import Opinion
from authorityspoke.predicates import ureg, Q_
from authorityspoke.selectors import TextQuoteSelector


class TestCodes:
    def test_making_code(self, make_code):
        const = make_code["const"]
        assert str(const) == "Constitution of the United States"

    def test_make_cfr(self, make_code):
        cfr = make_code["cfr37"]
        assert str(cfr) == "Code of Federal Regulations Title 37"

    def test_cfr_repr(self, make_code):
        cfr = make_code["cfr37"]
        assert repr(cfr) == 'Code("cfr37.xml")'

    @pytest.mark.parametrize(
        "code, url",
        [
            ("usc17", "/us/usc/t17"),
            ("const", "/us/const"),
            ("cfr37", "/us/cfr/t37"),
            ("ca_evid", "/us-ca/evid"),
            ("ca_pen", "/us-ca/pen"),
        ],
    )
    def test_code_urls(self, make_code, code, url):
        assert make_code[code].url == url

    @pytest.mark.parametrize(
        "code, expected",
        [
            ("usc17", "USC Title 17"),
            ("const", "Constitution of the United States"),
            ("cfr37", "Code of Federal Regulations Title 37"),
            ("ca_evid", "California Evidence Code"),
            ("ca_pen", "California Penal Code"),
        ],
    )
    def test_code_title(self, make_code, code, expected):
        assert make_code[code].title == expected

    def test_get_bill_of_rights_effective_date(self, make_code):
        const = make_code["const"]
        bill_of_rights_date = datetime.date(1791, 12, 15)
        assert const.provision_effective_date("amendment-V") == bill_of_rights_date

    def test_get_14th_A_effective_date(self, make_code):
        const = make_code["const"]
        equal_protection_date = datetime.date(1868, 7, 28)
        assert const.provision_effective_date("amendment-XIV") == equal_protection_date

    def test_format_uri_for_const(self, make_code):
        """
        This should test the example in the docstring
        for the Code.format_uri_for_const method.
        """

        const = make_code["const"]
        out = const.format_uri_for_const("/us/const/amendment/XIV/1")
        assert out == "amendment-XIV-1"


class TestEnactments:
    def test_make_enactment(self, make_enactment):
        search_clause = make_enactment["search_clause"]
        assert search_clause.text.endswith("shall not be violated")

    def test_passage_from_uslm_code(self, make_code):
        usc17 = make_code["usc17"]
        copyright_exceptions = Enactment(
            usc17, section="102", subsection="b", end="extend to any"
        )
        assert copyright_exceptions.text == (
            "In no case does copyright protection "
            + "for an original work of authorship extend to any"
        )

    def test_passage_from_imported_statute(self, make_code):
        opinion = Opinion.from_file(f"oracle_h.json")
        oracle_majority = opinion.exposit(f"holding_oracle.json")
        despite_text = str(oracle_majority.holdings[5])
        assert 'DESPITE: "In no case does copyright protection ' in despite_text

    def test_short_passage_from_uslm_code(self, make_code):
        usc17 = make_code["usc17"]
        method = Enactment(
            usc17,
            section="102",
            subsection="b",
            start="method of operation",
            end="method of operation",
        )
        assert method.text == "method of operation"

    def test_passage_from_cfr_code(self, make_code):
        cfr = make_code["cfr37"]
        selector = TextQuoteSelector(path="/us/cfr/t37/s202.1")
        slogans = Enactment(cfr, selector=selector)
        assert "Words and short phrases such as names" in slogans.text

    def test_code_title_in_str(self, make_enactment):
        assert "secure in their persons" in str(make_enactment["search_clause"])

    def test_equal_enactment_text(self, make_enactment):
        assert make_enactment["due_process_5"].means(make_enactment["due_process_14"])

    def test_enactment_subset_or_equal(self, make_enactment):
        dp5 = make_enactment["due_process_5"]
        dp14 = make_enactment["due_process_14"]
        assert dp5 >= dp14

    def test_unequal_enactment_text(self, make_enactment):
        assert make_enactment["search_clause"] != make_enactment["fourth_a"]

    def test_enactment_subset(self, make_enactment):
        assert make_enactment["search_clause"] < make_enactment["fourth_a"]

    def test_comparison_to_factor_false(self, make_enactment, watt_factor):
        dp5 = make_enactment["due_process_5"]
        f1 = watt_factor["f1"]
        assert not dp5 == f1

    def test_implication_of_factor_fails(self, make_enactment, watt_factor):
        dp5 = make_enactment["due_process_5"]
        f1 = watt_factor["f1"]
        with pytest.raises(TypeError):
            assert not dp5 > f1

    def test_implication_by_factor_fails(self, make_enactment, watt_factor):
        dp5 = make_enactment["due_process_5"]
        f1 = watt_factor["f1"]
        with pytest.raises(TypeError):
            assert not dp5 < f1

    def test_bill_of_rights_effective_date(self, make_enactment):
        # December 15, 1791
        assert make_enactment["search_clause"].effective_date == datetime.date(
            1791, 12, 15
        )

    def test_14th_A_effective_date(self, make_enactment):
        # July 28, 1868
        assert make_enactment["due_process_14"].effective_date == datetime.date(
            1868, 7, 28
        )

    def test_compare_effective_dates(self, make_enactment):
        dp5 = make_enactment["due_process_5"]
        dp14 = make_enactment["due_process_14"]
        assert dp14.effective_date > dp5.effective_date
