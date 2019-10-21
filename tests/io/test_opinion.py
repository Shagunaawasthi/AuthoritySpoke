from typing import Dict, List

from authorityspoke.io import loaders, readers, schemas


class TestLoadOpinion:
    def test_load_opinion_in_CAP_format(self):
        watt_dict = loaders.load_opinion("watt_h.json")
        assert watt_dict["name_abbreviation"] == "Wattenburg v. United States"

    def test_load_opinion(self):
        schema = schemas.OpinionSchema(many=False)
        brad_dict = loaders.load_opinion("brad_h.json")
        dissent = brad_dict["casebody"]["data"]["opinions"][1]
        opinion = schema.load(dissent)
        assert opinion.position == "concurring-in-part-and-dissenting-in-part"
