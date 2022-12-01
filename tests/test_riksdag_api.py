import os
from sync_asr.riksdag.riksdag_api import RiksdagAPI


TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def test_riksdag_api():
    file = f"{TEST_DIR}/H001CU21"
    rdapi = RiksdagAPI(filename=file)
    assert "streamurls" in rdapi.__dict__