import json

from authorityspoke.opinions import Opinion


class TestDownload:
    def test_download_opinion_by_id(self, tmp_path):
        to_file = "oracle_h.json"
        Opinion.cap_download(
            cap_id=4066790, filename=to_file, directory=tmp_path, to_dict=True
        )
        new_file = tmp_path / to_file
        with open(new_file, "r") as read_file:
            case = json.load(read_file)
        assert case["name_abbreviation"] == "Oracle America, Inc. v. Google Inc."

    def test_download_opinion_by_cite(self, tmp_path):
        to_file = "lotus_h.json"
        Opinion.cap_download(
            cite="49 F.3d 807", filename=to_file, directory=tmp_path, to_dict=True
        )
        new_file = tmp_path / to_file
        with open(new_file, "r") as read_file:
            case = json.load(read_file)
        assert case["decision_date"] == "1995-03-09"

    def test_download_and_make_opinion_object(self):
        lotus = Opinion.cap_download(cite="49 F.3d 807", save_to_file=False)
        assert lotus.__class__.__name__ == "Opinion"
