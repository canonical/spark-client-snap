import logging
import os
import unittest
import uuid

import helpers.utils  # type: ignore
from tests import UnittestWithTmpFolder


class TestLoggingConfig(UnittestWithTmpFolder):
    def test_dummy(self):
        pass


class TestProperties(UnittestWithTmpFolder):
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
        contents_java_options = (
            f'-Dscala.shell.histfile = "{test_id} -Da=A -Db=B -Dc=C"'
        )
        test_config_w["spark.driver.extraJavaOptions"] = contents_java_options
        with helpers.utils.UmaskNamedTemporaryFile(
            mode="w", prefix="spark-client-snap-unittest-", suffix=".test"
        ) as t:
            helpers.utils.write_property_file(t.file, test_config_w)
            t.flush()
            test_config_r = helpers.utils.read_property_file(t.name)
            assert (
                test_config_r.get("spark.driver.extraJavaOptions")
                == contents_java_options
            )

    def test_parse_options(self):
        test_id = str(uuid.uuid4())
        props_with_option = f'"-Dscala.shell.histfile={test_id} -Da=A -Db=B -Dc=C"'
        options = helpers.utils.parse_options(props_with_option)
        assert options["scala.shell.histfile"] == f"{test_id}"
        assert options["a"] == "A"
        assert options["b"] == "B"
        assert options["c"] == "C"

    def test_merge_options(self):
        test_id = str(uuid.uuid4())
        options1 = dict()
        options1[
            "spark.driver.extraJavaOptions"
        ] = '"-Dscala.shell.histfile=file1 -Da=A"'
        options2 = dict()
        options2[
            "spark.driver.extraJavaOptions"
        ] = '"-Dscala.shell.histfile=file2 -Db=B"'
        options3 = dict()
        options3[
            "spark.driver.extraJavaOptions"
        ] = f'"-Dscala.shell.histfile={test_id} -Dc=C"'

        expected_merged_options = f"-Dscala.shell.histfile={test_id} -Da=A -Db=B -Dc=C"

        options = helpers.utils.merge_options([options1, options2, options3])
        assert (
            options.get("spark.driver.extraJavaOptions").strip()
            == expected_merged_options.strip()
        )

    def test_merge_configurations(self):
        test_id = str(uuid.uuid4())
        conf1 = dict()
        conf1["spark.app.name"] = "spark1-app"
        conf1["spark.executor.instances"] = "3"
        conf1[
            "spark.kubernetes.container.image"
        ] = "docker.io/averma32/sparkrock:latest"
        conf1["spark.kubernetes.container.image.pullPolicy"] = "IfNotPresent"
        conf1["spark.kubernetes.namespace"] = "default"
        conf1["spark.kubernetes.authenticate.driver.serviceAccountName"] = "spark"
        conf1[
            "spark.driver.extraJavaOptions"
        ] = "-Dscala.shell.histfile=file1 -DpropA=A1 -DpropB=B"

        conf2 = dict()
        conf2["spark.app.name"] = "spark2-app"
        conf2["spark.hadoop.fs.s3a.endpoint"] = "http://192.168.1.39:9000"
        conf2["spark.hadoop.fs.s3a.access.key"] = "PJRzbIei0ZOJQOun"
        conf2["spark.hadoop.fs.s3a.secret.key"] = "BHERvH7cap87UFe3PEqTb3sksSmjCbK7"
        conf2[
            "spark.hadoop.fs.s3a.aws.credentials.provider"
        ] = "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider"
        conf2[
            "spark.driver.extraJavaOptions"
        ] = "-DpropA=A2 -Dscala.shell.histfile=file2 -DpropC=C"

        conf3 = dict()
        conf3["spark.app.name"] = "spark3-app"
        conf3["spark.hadoop.fs.s3a.connection.ssl.enabled"] = "false"
        conf3["spark.hadoop.fs.s3a.path.style.access"] = "true"
        conf3["spark.eventLog.enabled"] = "true"
        conf3["spark.eventLog.dir"] = "s3a://spark-history-server-dir/spark-events"
        conf3[
            "spark.history.fs.logDirectory"
        ] = "s3a://spark-history-server-dir/spark-events"
        conf3[
            "spark.driver.extraJavaOptions"
        ] = f"-DpropA=A3 -DpropD=D -Dscala.shell.histfile={test_id}"

        expected_merged_options = (
            f"-Dscala.shell.histfile={test_id} -DpropA=A3 -DpropB=B -DpropC=C -DpropD=D"
        )

        conf = helpers.utils.merge_configurations([conf1, conf2, conf3])

        assert conf["spark.app.name"] == "spark3-app"
        assert conf["spark.executor.instances"] == "3"
        assert (
            conf["spark.kubernetes.container.image"]
            == "docker.io/averma32/sparkrock:latest"
        )
        assert conf["spark.kubernetes.container.image.pullPolicy"] == "IfNotPresent"
        assert conf["spark.kubernetes.namespace"] == "default"
        assert (
            conf["spark.kubernetes.authenticate.driver.serviceAccountName"] == "spark"
        )
        assert conf["spark.hadoop.fs.s3a.endpoint"] == "http://192.168.1.39:9000"
        assert conf["spark.hadoop.fs.s3a.access.key"] == "PJRzbIei0ZOJQOun"
        assert (
            conf["spark.hadoop.fs.s3a.secret.key"] == "BHERvH7cap87UFe3PEqTb3sksSmjCbK7"
        )
        assert (
            conf["spark.hadoop.fs.s3a.aws.credentials.provider"]
            == "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider"
        )
        assert conf["spark.hadoop.fs.s3a.connection.ssl.enabled"] == "false"
        assert conf["spark.hadoop.fs.s3a.path.style.access"] == "true"
        assert conf["spark.eventLog.enabled"] == "true"
        assert (
            conf["spark.eventLog.dir"] == "s3a://spark-history-server-dir/spark-events"
        )
        assert (
            conf["spark.history.fs.logDirectory"]
            == "s3a://spark-history-server-dir/spark-events"
        )
        assert (
            conf["spark.driver.extraJavaOptions"].strip()
            == expected_merged_options.strip()
        )


if __name__ == "__main__":

    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level="DEBUG")
    unittest.main()
