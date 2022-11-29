from unittest import TestCase

from helpers_new.domain import Defaults, ServiceAccount, PropertyFile
from helpers_new.services import K8sServiceAccountRegistry, KubeInterface, AbstractServiceAccountRegistry
from tests import integration_test


class TestRegistry(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.defaults = Defaults()
        cls.kube_interface = KubeInterface(cls.defaults.kube_config)

    def get_registry(self) -> AbstractServiceAccountRegistry:
        return K8sServiceAccountRegistry(self.kube_interface)

    def setUp(self) -> None:
        # Make sure there are no service account before each test is run
        registry = self.cleanup_registry(self.get_registry())
        self.assertEqual(len(registry.all()), 0)

    def tearDown(self) -> None:
        # Make sure there are no service account before each test is run
        registry = self.cleanup_registry(self.get_registry())
        self.assertEqual(len(registry.all()), 0)

    @staticmethod
    def cleanup_registry(registry: AbstractServiceAccountRegistry):
        [registry.delete(account.id) for account in registry.all()]
        return registry

    @integration_test
    def test_registry_io(self):
        registry = self.get_registry()

        self.assertEqual(len(registry.all()), 0)

        service_account = ServiceAccount(
            "my-spark", "default",
            self.kube_interface.api_server,
            primary=True,
            extra_confs=PropertyFile({"my-key": "my-value"})
        )

        registry.create(service_account)

        self.assertEqual(len(registry.all()), 1)

        retrieved_service_account = registry.get(service_account.id)

        self.assertEqual(service_account.id, retrieved_service_account.id)
        self.assertEqual(service_account.name, retrieved_service_account.name)
        self.assertEqual(service_account.namespace, retrieved_service_account.namespace)
        self.assertEqual(service_account.primary, retrieved_service_account.primary)
        self.assertEqual(service_account.extra_confs.props, retrieved_service_account.extra_confs.props)

        registry.delete(service_account.id)

