import logging
import unittest
import uuid

from spark_client.services import KubeInterface, parse_conf_overrides
from tests import TestCase


class TestServices(TestCase):
    def test_conf_expansion_cli(self):
        home_var = "/this/is/my/home"

        parsed_property = parse_conf_overrides(
            ["my-conf=$HOME/folder", "my-other-conf=/this/does/$NOT/change"],
            environ_vars={"HOME": home_var},
        )
        self.assertEqual(parsed_property.props["my-conf"], f"{home_var}/folder")
        self.assertEqual(
            parsed_property.props["my-other-conf"], "/this/does/$NOT/change"
        )

    def test_kube_interface(self):

        # mock logic
        test_id = str(uuid.uuid4())
        username1 = str(uuid.uuid4())
        context1 = str(uuid.uuid4())
        token1 = str(uuid.uuid4())
        username2 = str(uuid.uuid4())
        context2 = str(uuid.uuid4())
        token2 = str(uuid.uuid4())
        username3 = str(uuid.uuid4())
        context3 = str(uuid.uuid4())
        token3 = str(uuid.uuid4())
        test_kubectl_cmd = str(uuid.uuid4())

        kubeconfig_yaml = {
            "apiVersion": "v1",
            "clusters": [
                {
                    "cluster": {
                        "certificate-authority-data": f"{test_id}-1",
                        "server": f"https://0.0.0.0:{test_id}-1",
                    },
                    "name": f"{context1}-cluster",
                },
                {
                    "cluster": {
                        "certificate-authority-data": f"{test_id}-2",
                        "server": f"https://0.0.0.0:{test_id}-2",
                    },
                    "name": f"{context2}-cluster",
                },
                {
                    "cluster": {
                        "certificate-authority-data": f"{test_id}-3",
                        "server": f"https://0.0.0.0:{test_id}-3",
                    },
                    "name": f"{context3}-cluster",
                },
            ],
            "contexts": [
                {
                    "context": {
                        "cluster": f"{context1}-cluster",
                        "user": f"{username1}",
                    },
                    "name": f"{context1}",
                },
                {
                    "context": {
                        "cluster": f"{context2}-cluster",
                        "user": f"{username2}",
                    },
                    "name": f"{context2}",
                },
                {
                    "context": {
                        "cluster": f"{context3}-cluster",
                        "user": f"{username3}",
                    },
                    "name": f"{context3}",
                },
            ],
            "current-context": f"{context2}",
            "kind": "Config",
            "preferences": {},
            "users": [
                {"name": f"{username1}", "user": {"token": f"{token1}"}},
                {"name": f"{username2}", "user": {"token": f"{token2}"}},
                {"name": f"{username3}", "user": {"token": f"{token3}"}},
            ],
        }

        k = KubeInterface(kube_config_file=kubeconfig_yaml)

        self.assertEqual(k.context_name, context2)
        self.assertEqual(k.with_context(context3).context_name, context3)
        self.assertEqual(
            k.with_context(context3).context.get("cluster"), f"{context3}-cluster"
        )
        self.assertEqual(
            k.with_kubectl_cmd(test_kubectl_cmd).kubectl_cmd, test_kubectl_cmd
        )
        self.assertEqual(k.kube_config, kubeconfig_yaml)

        self.assertTrue(context1 in k.available_contexts)
        self.assertTrue(context2 in k.available_contexts)
        self.assertTrue(context3 in k.available_contexts)
        self.assertEqual(len(k.available_contexts), 3)

        current_context = k.context
        self.assertEqual(current_context.get("cluster"), f"{context2}-cluster")
        self.assertEqual(current_context.get("user"), f"{username2}")

        current_cluster = k.cluster
        self.assertEqual(
            current_cluster.get("certificate-authority-data"), f"{test_id}-2"
        )
        self.assertEqual(current_cluster.get("server"), f"https://0.0.0.0:{test_id}-2")


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level="DEBUG")
    unittest.main()
