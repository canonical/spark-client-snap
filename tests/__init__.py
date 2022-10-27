import os
import random
from unittest import TestCase

from helpers.utils import create_dir_if_not_exists  # type: ignore

test_path = os.path.dirname(os.path.abspath(__file__))

DATA_FOLDER = os.path.join(test_path, "resources", "data")


class UnittestWithTmpFolder(TestCase):
    TMP_FOLDER = os.path.join("/tmp", "%032x" % random.getrandbits(128))

    @classmethod
    def setUpClass(cls) -> None:
        create_dir_if_not_exists(cls.TMP_FOLDER)

    @classmethod
    def tearDownClass(cls) -> None:
        os.system(f"rm -rf {cls.TMP_FOLDER}/*")
