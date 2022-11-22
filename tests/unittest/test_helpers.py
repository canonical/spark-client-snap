import base64
import logging
import os
import unittest
import uuid
from unittest.mock import patch

import helpers.constants  # type: ignore
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

    def test_parse_conf_overrides(self):
        test_id = str(uuid.uuid4())

        username = str(uuid.uuid4())
        namespace = str(uuid.uuid4())
        kubeconfig = str(uuid.uuid4())
        context = str(uuid.uuid4())

        os.environ["CONF_OVERRIDE_CONTEXT"] = context

        conf_list = [
            f"spark.kubernetes.namespace={namespace}",
            f"spark.kubernetes.authenticate.driver.serviceAccountName={username}",
            f"{helpers.constants.OPTION_SPARK_DRIVER_EXTRA_JAVA_OPTIONS}=-Dscala.shell.histfile={test_id} -Dkubeconfig={kubeconfig} -Dcontext=$CONF_OVERRIDE_CONTEXT",
        ]

        overrides = helpers.utils.parse_conf_overrides(conf_list)

        assert overrides.get("spark.kubernetes.namespace") == namespace
        assert (
            overrides.get("spark.kubernetes.authenticate.driver.serviceAccountName")
            == username
        )
        assert (
            overrides.get(helpers.constants.OPTION_SPARK_DRIVER_EXTRA_JAVA_OPTIONS)
            == f"-Dscala.shell.histfile={test_id} -Dkubeconfig={kubeconfig} -Dcontext={context}"
        )

    @patch("helpers.utils.subprocess.check_output")
    def test_autodetect_kubernetes_master(self, mock_subprocess):
        # mock logic
        def side_effect(*args, **kwargs):
            return values[args[0]]

        mock_subprocess.side_effect = side_effect

        test_id = str(uuid.uuid4())
        username = str(uuid.uuid4())
        namespace = str(uuid.uuid4())
        kubeconfig = helpers.utils.get_kube_config()
        context = str(uuid.uuid4())
        control_plane_uri = f"http://{str(uuid.uuid4())}:{str(uuid.uuid4())}"

        label = helpers.utils.get_primary_label()

        cmd_get_service_account = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context}  get serviceaccount -l {label} -A -o yaml"
        output_get_service_account_yaml_str = f'apiVersion: v1\nitems:\n- apiVersion: v1\n  kind: ServiceAccount\n  metadata:\n    creationTimestamp: "2022-11-21T14:32:06Z"\n    labels:\n      app.kubernetes.io/managed-by: spark-client\n      app.kubernetes.io/spark-client-primary: "1"\n    name: {username}\n    namespace: {namespace}\n    resourceVersion: "321848"\n    uid: 87ef7231-8106-4a36-b545-d8cf167788a6\nkind: List\nmetadata:\n  resourceVersion: ""'
        output_get_service_account = output_get_service_account_yaml_str.encode("utf-8")

        cmd_get_master = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} config view --minify -o jsonpath=\"{{.clusters[0]['cluster.server']}}\""
        output_get_master = control_plane_uri.encode("utf-8")

        values = {
            cmd_get_service_account: output_get_service_account,
            cmd_get_master: output_get_master,
        }

        # test logic
        env_snap = os.environ.get("SNAP")
        os.environ["SNAP"] = test_id

        conf = dict()
        conf["spark.kubernetes.namespace"] = namespace
        conf["spark.kubernetes.context"] = context
        master = helpers.utils.autodetect_kubernetes_master(conf)

        if env_snap:
            os.environ["SNAP"] = env_snap

        expected_master = f"k8s://{control_plane_uri}"

        mock_subprocess.assert_any_call(cmd_get_service_account, shell=True)
        mock_subprocess.assert_called_with(cmd_get_master, shell=True)

        assert master == expected_master

    @patch("helpers.utils.NamedTemporaryFile")
    @patch("helpers.utils.io.TextIOWrapper")
    @patch("helpers.utils.os")
    @patch("helpers.utils.subprocess.check_output")
    def test_setup_kubernetes_secret(
        self, mock_subprocess, mock_os, mock_fp, mock_tempfile
    ):
        # mock logic
        def side_effect(*args, **kwargs):
            return values[args[0]]

        mock_subprocess.side_effect = side_effect

        test_id = str(uuid.uuid4())
        username = str(uuid.uuid4())
        namespace = str(uuid.uuid4())
        kubeconfig = str(uuid.uuid4())
        context = str(uuid.uuid4())
        properties_file = str(uuid.uuid4())

        mock_os.umask.return_value = 0
        mock_os.chmod.return_value = 0
        mock_os.environ.__getitem__.return_value = test_id
        mock_fp.write.return_value = 0
        mock_tempfile.file.return_value = mock_fp
        mock_tempfile.flush.return_value = 0
        mock_tempfile.return_value.__enter__.return_value.name = properties_file

        cmd_create_secret = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} create secret generic spark-client-sa-conf-{username} --from-env-file={properties_file}"
        output_create_secret_str = ""
        output_create_secret = output_create_secret_str.encode("utf-8")

        values = {cmd_create_secret: output_create_secret}

        # test logic
        env_snap = os.environ.get("SNAP")
        os.environ["SNAP"] = test_id

        conf = [
            f"spark.kubernetes.namespace={namespace}",
            f"spark.kubernetes.context={context}",
        ]

        helpers.utils.setup_kubernetes_secret(
            username, namespace, kubeconfig, context, None, conf
        )

        if env_snap:
            os.environ["SNAP"] = env_snap

        mock_subprocess.assert_called_with(cmd_create_secret, shell=True)

    @patch("helpers.utils.os")
    @patch("helpers.utils.subprocess.check_output")
    def test_retrieve_kubernetes_secret(self, mock_subprocess, mock_os):
        # mock logic
        def side_effect(*args, **kwargs):
            return values[args[0]]

        mock_subprocess.side_effect = side_effect

        test_id = str(uuid.uuid4())
        username = str(uuid.uuid4())
        namespace = str(uuid.uuid4())
        kubeconfig = str(uuid.uuid4())
        context = str(uuid.uuid4())
        conf_key = str(uuid.uuid4())
        conf_value = str(uuid.uuid4())
        conf_value_base64_encoded = base64.b64encode(conf_value.encode("ascii"))

        mock_os.environ.__getitem__.return_value = test_id

        cmd_retrieve_secret_yaml = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} get secret spark-client-sa-conf-{username} -o yaml"
        output_retrieve_secret_yaml_str = f'apiVersion: v1\ndata:\n  {conf_key}: {conf_value_base64_encoded}\nkind: Secret\nmetadata:\n  creationTimestamp: "2022-11-21T07:54:51Z"\n  name: spark-client-sa-conf-{username}\n  namespace: {namespace}\n  resourceVersion: "292967"\n  uid: 943b82c3-2891-4332-886c-621ef4f4633f\ntype: Opaque'
        output_retrieve_secret_yaml = output_retrieve_secret_yaml_str.encode("utf-8")

        cmd_retrieve_secret = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} get secret spark-client-sa-conf-{username} -o jsonpath='{{.data.{conf_key}}}' | base64 --decode"
        output_retrieve_secret_str = conf_value
        output_retrieve_secret = output_retrieve_secret_str.encode("utf-8")

        values = {
            cmd_retrieve_secret_yaml: output_retrieve_secret_yaml,
            cmd_retrieve_secret: output_retrieve_secret,
        }

        # test logic
        env_snap = os.environ.get("SNAP")
        os.environ["SNAP"] = test_id

        helpers.utils.retrieve_kubernetes_secret(
            username, namespace, kubeconfig, context, None
        )

        if env_snap:
            os.environ["SNAP"] = env_snap

        mock_subprocess.assert_any_call(cmd_retrieve_secret_yaml, shell=True)
        mock_subprocess.assert_called_with(cmd_retrieve_secret, shell=True)

    @patch("helpers.utils.os.system")
    @patch("helpers.utils.subprocess.check_output")
    def test_set_up_user_primary_defined_primary_reassigned(
        self, mock_subprocess, mock_os_system
    ):
        # mock logic
        def side_effect_subprocess(*args, **kwargs):
            return values_subprocess[args[0]]

        def side_effect_os(*args, **kwargs):
            return values_os[args[0]]

        mock_os_system.side_effect = side_effect_os
        mock_os_system.return_value = 0

        mock_subprocess.side_effect = side_effect_subprocess

        test_id = str(uuid.uuid4())
        username = str(uuid.uuid4())
        namespace = str(uuid.uuid4())
        kubeconfig = str(uuid.uuid4())
        context = str(uuid.uuid4())
        conf_key = str(uuid.uuid4())
        conf_value = str(uuid.uuid4())

        cmd_create_service_account = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} create serviceaccount {username}"
        output_create_service_account = ""
        cmd_create_role_binding = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} create rolebinding {username}-role --role=view --serviceaccount={namespace}:{username}"
        output_create_role_binding = ""

        cmd_retrieve_primary_sa_yaml = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context}  get serviceaccount -l app.kubernetes.io/spark-client-primary=1 -A -o yaml"
        output_retrieve_primary_sa_yaml_str = f'apiVersion: v1\nitems:\n- apiVersion: v1\n  kind: ServiceAccount\n  metadata:\n    creationTimestamp: "2022-11-21T14:32:06Z"\n    labels:\n      app.kubernetes.io/managed-by: spark-client\n      app.kubernetes.io/spark-client-primary: "1"\n    name: {username}\n    namespace: {namespace}\n    resourceVersion: "321848"\n    uid: 87ef7231-8106-4a36-b545-d8cf167788a6\nkind: List\nmetadata:\n  resourceVersion: ""'
        output_retrieve_primary_sa_yaml = output_retrieve_primary_sa_yaml_str.encode(
            "utf-8"
        )

        cmd_unlabel_service_account = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} label serviceaccount --namespace={namespace} {username} app.kubernetes.io/spark-client-primary-"
        output_unlabel_service_account = ""
        cmd_unlabel_rolebinding = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} label rolebinding --namespace={namespace} {username}-role app.kubernetes.io/spark-client-primary-"
        output_unlabel_rolebinding = ""
        cmd_label_new_service_account = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} label serviceaccount {username} app.kubernetes.io/managed-by=spark-client app.kubernetes.io/spark-client-primary=1"
        output_label_service_account = ""
        cmd_label_new_rolebinding = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} label rolebinding {username}-role app.kubernetes.io/managed-by=spark-client app.kubernetes.io/spark-client-primary=1"
        output_label_new_rolebinding = ""

        values_subprocess = {
            cmd_retrieve_primary_sa_yaml: output_retrieve_primary_sa_yaml
        }

        values_os = {
            cmd_create_service_account: output_create_service_account,
            cmd_create_role_binding: output_create_role_binding,
            cmd_unlabel_service_account: output_unlabel_service_account,
            cmd_unlabel_rolebinding: output_unlabel_rolebinding,
            cmd_label_new_service_account: output_label_service_account,
            cmd_label_new_rolebinding: output_label_new_rolebinding,
        }

        # test logic
        env_snap = os.environ.get("SNAP")
        os.environ["SNAP"] = test_id

        defaults = dict()
        defaults[conf_key] = conf_value
        helpers.utils.set_up_user(
            username, namespace, kubeconfig, context, defaults, mark_primary=True
        )

        if env_snap:
            os.environ["SNAP"] = env_snap

        mock_os_system.assert_any_call(cmd_create_service_account)
        mock_os_system.assert_any_call(cmd_create_role_binding)

        mock_subprocess.assert_any_call(cmd_retrieve_primary_sa_yaml, shell=True)

        mock_os_system.assert_any_call(cmd_unlabel_service_account)
        mock_os_system.assert_any_call(cmd_unlabel_rolebinding)
        mock_os_system.assert_any_call(cmd_label_new_service_account)
        mock_os_system.assert_any_call(cmd_label_new_rolebinding)

    @patch("helpers.utils.os.system")
    @patch("helpers.utils.subprocess.check_output")
    def test_set_up_user_primary_defined_primary_not_reassigned(
        self, mock_subprocess, mock_os_system
    ):
        # mock logic
        def side_effect_subprocess(*args, **kwargs):
            return values_subprocess[args[0]]

        def side_effect_os(*args, **kwargs):
            return values_os[args[0]]

        mock_os_system.side_effect = side_effect_os
        mock_os_system.return_value = 0

        mock_subprocess.side_effect = side_effect_subprocess

        test_id = str(uuid.uuid4())
        username = str(uuid.uuid4())
        namespace = str(uuid.uuid4())
        kubeconfig = str(uuid.uuid4())
        context = str(uuid.uuid4())
        conf_key = str(uuid.uuid4())
        conf_value = str(uuid.uuid4())

        cmd_create_service_account = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} create serviceaccount {username}"
        output_create_service_account = ""
        cmd_create_role_binding = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} create rolebinding {username}-role --role=view --serviceaccount={namespace}:{username}"
        output_create_role_binding = ""

        cmd_retrieve_primary_sa_yaml = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context}  get serviceaccount -l app.kubernetes.io/spark-client-primary=1 -A -o yaml"
        output_retrieve_primary_sa_yaml_str = f'apiVersion: v1\nitems:\n- apiVersion: v1\n  kind: ServiceAccount\n  metadata:\n    creationTimestamp: "2022-11-21T14:32:06Z"\n    labels:\n      app.kubernetes.io/managed-by: spark-client\n      app.kubernetes.io/spark-client-primary: "1"\n    name: {username}\n    namespace: {namespace}\n    resourceVersion: "321848"\n    uid: 87ef7231-8106-4a36-b545-d8cf167788a6\nkind: List\nmetadata:\n  resourceVersion: ""'
        output_retrieve_primary_sa_yaml = output_retrieve_primary_sa_yaml_str.encode(
            "utf-8"
        )

        cmd_label_new_service_account = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} label serviceaccount {username} app.kubernetes.io/managed-by=spark-client"
        output_label_service_account = ""
        cmd_label_new_rolebinding = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} label rolebinding {username}-role app.kubernetes.io/managed-by=spark-client"
        output_label_new_rolebinding = ""

        values_subprocess = {
            cmd_retrieve_primary_sa_yaml: output_retrieve_primary_sa_yaml
        }

        values_os = {
            cmd_create_service_account: output_create_service_account,
            cmd_create_role_binding: output_create_role_binding,
            cmd_label_new_service_account: output_label_service_account,
            cmd_label_new_rolebinding: output_label_new_rolebinding,
        }

        # test logic
        env_snap = os.environ.get("SNAP")
        os.environ["SNAP"] = test_id

        defaults = dict()
        defaults[conf_key] = conf_value
        helpers.utils.set_up_user(
            username, namespace, kubeconfig, context, defaults, mark_primary=False
        )

        if env_snap:
            os.environ["SNAP"] = env_snap

        mock_os_system.assert_any_call(cmd_create_service_account)
        mock_os_system.assert_any_call(cmd_create_role_binding)

        mock_subprocess.assert_any_call(cmd_retrieve_primary_sa_yaml, shell=True)

        mock_os_system.assert_any_call(cmd_label_new_service_account)
        mock_os_system.assert_any_call(cmd_label_new_rolebinding)

    @patch("helpers.utils.os.system")
    @patch("helpers.utils.subprocess.check_output")
    def test_set_up_user_primary_not_defined(self, mock_subprocess, mock_os_system):
        # mock logic
        def side_effect_subprocess(*args, **kwargs):
            return values_subprocess[args[0]]

        def side_effect_os(*args, **kwargs):
            return values_os[args[0]]

        mock_os_system.side_effect = side_effect_os
        mock_os_system.return_value = 0

        mock_subprocess.side_effect = side_effect_subprocess

        test_id = str(uuid.uuid4())
        username = str(uuid.uuid4())
        namespace = str(uuid.uuid4())
        kubeconfig = str(uuid.uuid4())
        context = str(uuid.uuid4())
        conf_key = str(uuid.uuid4())
        conf_value = str(uuid.uuid4())

        cmd_create_service_account = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} create serviceaccount {username}"
        output_create_service_account = ""
        cmd_create_role_binding = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} create rolebinding {username}-role --role=view --serviceaccount={namespace}:{username}"
        output_create_role_binding = ""

        cmd_retrieve_primary_sa_yaml = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context}  get serviceaccount -l app.kubernetes.io/spark-client-primary=1 -A -o yaml"
        output_retrieve_primary_sa_yaml_str = (
            'apiVersion: v1\nitems: []\nkind: List\nmetadata:\n  resourceVersion: ""'
        )
        output_retrieve_primary_sa_yaml = output_retrieve_primary_sa_yaml_str.encode(
            "utf-8"
        )

        cmd_label_new_service_account = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} label serviceaccount {username} app.kubernetes.io/managed-by=spark-client app.kubernetes.io/spark-client-primary=1"
        output_label_service_account = ""
        cmd_label_new_rolebinding = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} label rolebinding {username}-role app.kubernetes.io/managed-by=spark-client app.kubernetes.io/spark-client-primary=1"
        output_label_new_rolebinding = ""

        values_subprocess = {
            cmd_retrieve_primary_sa_yaml: output_retrieve_primary_sa_yaml
        }

        values_os = {
            cmd_create_service_account: output_create_service_account,
            cmd_create_role_binding: output_create_role_binding,
            cmd_label_new_service_account: output_label_service_account,
            cmd_label_new_rolebinding: output_label_new_rolebinding,
        }

        # test logic
        env_snap = os.environ.get("SNAP")
        os.environ["SNAP"] = test_id

        defaults = dict()
        defaults[conf_key] = conf_value
        helpers.utils.set_up_user(
            username, namespace, kubeconfig, context, defaults, mark_primary=False
        )

        if env_snap:
            os.environ["SNAP"] = env_snap

        mock_os_system.assert_any_call(cmd_create_service_account)
        mock_os_system.assert_any_call(cmd_create_role_binding)

        mock_subprocess.assert_any_call(cmd_retrieve_primary_sa_yaml, shell=True)

        mock_os_system.assert_any_call(cmd_label_new_service_account)
        mock_os_system.assert_any_call(cmd_label_new_rolebinding)

    @patch("helpers.utils.os.system")
    @patch("helpers.utils.subprocess.check_output")
    def test_clean_up_user(self, mock_subprocess, mock_os_system):
        # mock logic
        def side_effect_os(*args, **kwargs):
            return values_os[args[0]]

        def side_effect_subprocess(*args, **kwargs):
            return values_subprocess[args[0]]

        mock_subprocess.side_effect = side_effect_subprocess
        mock_subprocess.return_value = 0
        mock_os_system.side_effect = side_effect_os
        mock_os_system.return_value = 0

        test_id = str(uuid.uuid4())
        username = str(uuid.uuid4())
        namespace = str(uuid.uuid4())
        kubeconfig = str(uuid.uuid4())
        context = str(uuid.uuid4())

        cmd_cleanup_service_account = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} delete serviceaccount {username}"
        output_cleanup_service_account = ""
        cmd_cleanup_role_binding = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} delete rolebinding {username}-role"
        output_cleanup_role_binding = ""

        cmd_delete_kubernetes_secret = f"{test_id}/kubectl --kubeconfig {kubeconfig} --namespace {namespace} --context {context} delete secret spark-client-sa-conf-{username}"
        output_delete_kubernetes_secret = ""

        values_os = {
            cmd_cleanup_service_account: output_cleanup_service_account,
            cmd_cleanup_role_binding: output_cleanup_role_binding,
        }

        values_subprocess = {
            cmd_delete_kubernetes_secret: output_delete_kubernetes_secret
        }

        # test logic
        env_snap = os.environ.get("SNAP")
        os.environ["SNAP"] = test_id

        helpers.utils.cleanup_user(username, namespace, kubeconfig, context)

        if env_snap:
            os.environ["SNAP"] = env_snap

        mock_os_system.assert_any_call(cmd_cleanup_service_account)
        mock_os_system.assert_any_call(cmd_cleanup_role_binding)

        mock_subprocess.assert_any_call(cmd_delete_kubernetes_secret, shell=True)


if __name__ == "__main__":

    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level="DEBUG")
    unittest.main()
