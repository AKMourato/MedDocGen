import json_generation_measurements
import pytest
from main.utils.helpers import check_and_create_folder
from tests.test_utils import is_same


@pytest.mark.parametrize("hlist", ["[262]"])
def test_jsongen(hlist):
    # delete folder if already there for proper testing
    test_dir_out = "tests/tests_out_measurements/"
    check_and_create_folder(test_dir_out, delete_if_exists=True)

    class Namespace:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    args = Namespace(
        jsondir=test_dir_out,
        datadir="/home/database/v-patients/",
        categories=["General LV", "LV"],
        measurement="LV Volume",
        hlist=hlist,
    )
    json_generation_measurements.measurement_jsongen(args)

    x = is_same(test_dir_out, "tests/test_measurement_jsons/")
    assert x == True
