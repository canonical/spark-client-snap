import logging
import os
import time
import unittest
import uuid

import helpers.utils
from tests import UnittestWithTmpFolder


class TestLoggingConfig(UnittestWithTmpFolder):
    def test_dummy(self):
        pass


class TestPropertiesFiles(UnittestWithTmpFolder):
    def test_read_property_file_invalid_file(self):
        test_id = str(uuid.uuid4())
        conf = helpers.utils.read_property_file(f"dummy_file_{test_id}")
        assert len(conf.keys()) == 0

    def test_get_scala_shell_history_file_snap_env(self):
        test_id = str(uuid.uuid4())
        os.environ["SNAP_USER_DATA"] = test_id
        assert (
            f"{test_id}/.scala_history" == helpers.utils.get_scala_shell_history_file()
        )

    def test_get_scala_shell_history_file_home(self):
        expected_username = os.environ.get("USER")
        env_snap_user_data = os.environ.get("SNAP_USER_DATA")
        if env_snap_user_data:
            del os.environ["SNAP_USER_DATA"]
        scala_history_file = helpers.utils.get_scala_shell_history_file()
        if env_snap_user_data:
            os.environ["SNAP_USER_DATA"] = env_snap_user_data
        assert f"/home/{expected_username}/.scala_history" == scala_history_file

    def test_read_property_file_extra_java_options(self):
        test_id = str(uuid.uuid4())
        test_config_w = dict()
        contents_java_options = f"-Dscala.shell.histfile={test_id} -Da=A -Db=B -Dc=C"
        test_config_w["spark.driver.extraJavaOptions"] = contents_java_options
        with helpers.utils.UmaskNamedTemporaryFile(
            mode="w", prefix="spark-client-snap-unittest-", suffix=".test"
        ) as t:
            helpers.utils.write_property_file(t.file, test_config_w)
            t.flush()
            test_config_r = helpers.utils.read_property_file(t.name)
            assert (
                test_config_r.get("spark.driver.extraJavaOptions").strip()
                == contents_java_options.strip()
            )


if __name__ == "__main__":

    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level="DEBUG")
    unittest.main()
