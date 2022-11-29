import base64
import os
import subprocess
from abc import ABC, abstractmethod
from enum import Enum
from functools import cached_property
from typing import List, Callable, Optional, Dict, Any, Union

import yaml

from spark_client.domain import ServiceAccount, Defaults, PropertyFile
from spark_client.exceptions import NoAccountFound, FormatError, NoResourceFound
from spark_client.utils import WithLogging, umask_named_temporary_file, parse_yaml_shell_output


class KubeInterface(WithLogging):

    def __init__(
            self,
            kube_config_file: Union[str, Dict[str, Any]],
            context_name: Optional[str] = None,
            kubectl_cmd: str = "kubectl"
    ):
        self.kube_config_file = kube_config_file
        self._context_name = context_name
        self.kubectl_cmd = kubectl_cmd

    def with_context(self, context_name: str):
        return KubeInterface(self.kube_config_file, context_name, self.kubectl_cmd)

    def with_kubectl_cmd(self, kubectl_cmd: str):
        return KubeInterface(self.kube_config_file, self.context_name, kubectl_cmd)

    @cached_property
    def kube_config(self) -> Dict[str, Any]:
        if isinstance(self.kube_config_file, str):
            with open(self.kube_config_file, "r") as fid:
                return yaml.safe_load(fid)
        else:
            return self.kube_config_file

    @cached_property
    def available_contexts(self) -> List[str]:
        return [context["name"] for context in self.kube_config["contexts"]]

    @cached_property
    def context_name(self) -> str:
        return self.kube_config["current-context"] if self._context_name is None else self._context_name

    @cached_property
    def context(self) -> Dict[str, str]:
        return [
            context["context"]
            for context in self.kube_config["contexts"] if context["name"] == self.context_name
        ][0]

    @cached_property
    def cluster(self) -> Dict:
        return [
            cluster["cluster"]
            for cluster in self.kube_config["clusters"] if cluster["name"] == self.context["cluster"]
        ][0]

    @cached_property
    def api_server(self):
        return self.cluster["server"]

    @cached_property
    def namespace(self):
        return self.context.get("namespace", "default")

    @cached_property
    def user(self):
        return self.context.get("user", "default")

    def exec(
            self, cmd: str, namespace: Optional[str] = None, context: Optional[str] = None, output: Optional[str] = None
    ) -> Union[str, Dict[str, Any]]:
        base_cmd = f"{self.kubectl_cmd} --kubeconfig {self.kube_config_file} "

        if "--namespace" not in cmd or "-n" not in cmd:
            base_cmd += f" --namespace {namespace or self.namespace} "
        if "--context" not in cmd:
            base_cmd += f" --context {context or self.context_name} "

        base_cmd += f"{cmd} -o {output or 'yaml'} "

        self.logger.debug(f"Executing command: {base_cmd}")

        return parse_yaml_shell_output(base_cmd) if (output is None) or (output == "yaml") \
            else subprocess.check_output(base_cmd, shell=True, stderr=None).decode("utf-8")

    def get_service_accounts(self, namespace: Optional[str] = None, labels: Optional[List[str]] = None) \
            -> List[Dict[str, Any]]:
        cmd = "get serviceaccount"

        if labels is not None and len(labels) > 0:
            cmd += ' '.join([f" -l {label}" for label in labels])

        namespace = " -A" if namespace is None else f" -n {namespace}"

        all_service_accounts_raw = self.exec(cmd + namespace)

        if isinstance(all_service_accounts_raw, str):
            raise ValueError("Malformed output")

        return all_service_accounts_raw["items"]

    def get_secret(self, secret_name: str, namespace: str) -> Dict[str, Any]:
        try:
            secret = self.exec(
                f"get secret {secret_name} --ignore-not-found", namespace=namespace
            )
        except Exception:
            raise NoResourceFound(secret_name)

        if secret is None or len(secret) == 0:
            raise NoResourceFound(secret_name)

        result = dict()
        for k, v in secret["data"].items():
            # k1 = k.replace(".", "\\.")
            # value = self.kube_interface.exec(f"get secret {secret_name}", output=f"jsonpath='{{.data.{k1}}}'")
            result[k] = base64.b64decode(v).decode("utf-8")

        secret["data"] = result
        return secret

    def set_label(self, resource_type: str, resource_name: str, label: str, namespace: str):
        self.exec(
            f"label {resource_type} {resource_name} {label}",
            namespace=namespace,
        )

    def create(self, resource_type: str, resource_name: str, namespace: str, **extra_args):
        formatted_extra_args = " ".join([f"--{k}={v}" for k, v in extra_args.items()])
        self.exec(f"create {resource_type} {resource_name} {formatted_extra_args}", namespace=namespace, output="name")

    def delete(self, resource_type: str, resource_name: str, namespace: str):
        self.exec(f"delete {resource_type} {resource_name} --ignore-not-found", namespace=namespace, output="name")

    @classmethod
    def autodetect(
            cls,
            context_name: Optional[str] = None,
            kubectl_cmd: str = "kubectl"
    ) -> 'KubeInterface':

        cmd = kubectl_cmd

        if context_name:
            cmd += f" --context {context_name}"

        config = parse_yaml_shell_output(f"{cmd} config view --minify -o yaml")

        return KubeInterface(config, context_name=context_name, kubectl_cmd=kubectl_cmd)


class AbstractServiceAccountRegistry(WithLogging, ABC):
    @abstractmethod
    def all(self) -> List['ServiceAccount']:
        """Return all existing service accounts."""
        pass

    @abstractmethod
    def create(self, service_account: ServiceAccount) -> str:
        """Create a new service account and return ids associated id."""
        pass

    @abstractmethod
    def set_configurations(self, account_id: str, configurations: PropertyFile) -> str:
        """Create a new service account and return ids associated id."""
        pass

    @abstractmethod
    def delete(self, account_id: str) -> str:
        """Create a new service account and return ids associated id."""
        pass

    @abstractmethod
    def set_primary(self, account_id: str) -> str:
        """Set the primary account to the one related to the provided account id."""
        pass

    def _retrieve_account(self, condition: Callable[[ServiceAccount], bool]):
        all_accounts = self.all()

        if len(all_accounts) == 0:
            raise NoAccountFound("There are no service account available. "
                                 "Please create a primary service account first.")
        primary_accounts = [account for account in all_accounts if condition(account) is True]
        if len(primary_accounts) == 0:
            raise NoAccountFound("There are no service account available. "
                                 "Please create a service account first.")

        if len(primary_accounts) > 1:
            self.logger.warning(
                f"More than one account was found: {','.join([account.name for account in primary_accounts])}. "
                f"Choosing the first: {primary_accounts[0].name}. "
                "Note that this may lead to un-expected behaviour if the other primary is chosen"
            )

        return primary_accounts[0]

    def get_primary(self) -> Optional[ServiceAccount]:
        try:
            return self._retrieve_account(lambda account: account.primary is True)
        except NoAccountFound:
            return None

    def get(self, account_id: str) -> Optional[ServiceAccount]:
        try:
            return self._retrieve_account(lambda account: account.id == account_id)
        except NoAccountFound:
            return None


class K8sServiceAccountRegistry(AbstractServiceAccountRegistry):

    def __init__(
            self,
            kube_interface: KubeInterface,
            defaults: Defaults = Defaults(),
    ):
        self.defaults = defaults
        self.kube_interface = kube_interface if kube_interface is not None \
            else KubeInterface(self.defaults.kube_config, kubectl_cmd=self.defaults.kubectl_cmd)

    SPARK_MANAGER_LABEL = "app.kubernetes.io/managed-by"
    PRIMARY_LABEL = "app.kubernetes.io/spark-client-primary"

    def all(self) -> List['ServiceAccount']:
        service_accounts = self.kube_interface.get_service_accounts(
            labels=[f"{self.SPARK_MANAGER_LABEL}=spark-client"]
        )
        return [self._build_service_account_from_raw(raw["metadata"]) for raw in service_accounts]

    @staticmethod
    def _get_secret_name(name):
        return f"spark-client-sa-conf-{name}"

    def _retrieve_account_configurations(self, name: str, namespace: str) -> PropertyFile:
        secret_name = self._get_secret_name(name)

        try:
            secret = self.kube_interface.get_secret(secret_name, namespace=namespace)["data"]
        except Exception:
            return PropertyFile.empty()

        return PropertyFile(secret)

    def _build_service_account_from_raw(self, metadata: Dict[str, Any]):
        name = metadata["name"]
        namespace = metadata["namespace"]
        primary = self.PRIMARY_LABEL in metadata["labels"]

        return ServiceAccount(
            name=name,
            namespace=namespace,
            primary=primary,
            api_server=self.kube_interface.api_server,
            extra_confs=self._retrieve_account_configurations(name, namespace)
        )

    def set_primary(self, account_id: str) -> str:

        # Relabeling primary
        primary_account = self.get_primary()

        if primary_account is not None:
            self.kube_interface.set_label(
                "serviceaccount", primary_account.name, f"{self.PRIMARY_LABEL}-", primary_account.namespace
            )
            self.kube_interface.set_label(
                "rolebinding", f"{primary_account.name}-role", f"{self.PRIMARY_LABEL}-", primary_account.namespace
            )

        service_account = self.get(account_id)

        self.kube_interface.set_label(
            "serviceaccount", service_account.name, f"{self.PRIMARY_LABEL}=True", service_account.namespace
        )
        self.kube_interface.set_label(
            "rolebinding", f"{service_account.name}-role", f"{self.PRIMARY_LABEL}=True", service_account.namespace
        )

        return account_id

    def create(self, service_account: ServiceAccount) -> str:
        rolebindingname = service_account.name + "-role"
        roleaccess = "view"

        self.kube_interface.create(
            "serviceaccount", service_account.name, namespace=service_account.namespace
        )
        self.kube_interface.create(
            "rolebinding", rolebindingname, namespace=service_account.namespace,
            **{"role": roleaccess, "serviceaccount": service_account.id}
        )

        self.kube_interface.set_label(
            "serviceaccount", service_account.name, f"{self.SPARK_MANAGER_LABEL}=spark-client",
            namespace=service_account.namespace
        )
        self.kube_interface.set_label(
            "rolebinding", rolebindingname, f"{self.SPARK_MANAGER_LABEL}=spark-client",
            namespace=service_account.namespace
        )

        if service_account.primary is True:
            self.set_primary(service_account.id)

        if len(service_account.extra_confs) > 0:
            self.set_configurations(service_account.id, service_account.extra_confs)

        return service_account.id

    def _create_account_configuration(self, service_account: ServiceAccount):
        secret_name = self._get_secret_name(service_account.name)

        try:
            self.kube_interface.delete(f"secret", secret_name, namespace=service_account.namespace)
        except Exception:
            pass

        with umask_named_temporary_file(
                mode="w", prefix="spark-dynamic-conf-k8s-", suffix=".conf"
        ) as t:
            self.logger.debug(
                f"Spark dynamic props available for reference at {t.name}\n"
            )

            service_account.extra_confs.write(t.file)

            t.flush()

            self.kube_interface.create(
                "secret generic", secret_name, namespace=service_account.namespace,
                **{"from-env-file": str(t.name)},
            )

    def set_configurations(self, account_id: str, configurations: PropertyFile) -> str:
        """Create a new service account and return ids associated id."""
        namespace, name = account_id.split(":")

        self._create_account_configuration(
            ServiceAccount(
                name=name, namespace=namespace, api_server=self.kube_interface.api_server, extra_confs=configurations
            )
        )

        return account_id

    def delete(self, account_id: str) -> str:
        """Create a new service account and return ids associated id."""
        namespace, name = account_id.split(":")

        rolebindingname = name + "-role"

        self.kube_interface.delete("serviceaccount", name, namespace=namespace)
        self.kube_interface.delete("rolebinding", rolebindingname, namespace=namespace)

        try:
            self.kube_interface.delete("secret", self._get_secret_name(name), namespace=namespace)
        except Exception:
            pass

        return account_id


class InMemoryAccountRegistry(AbstractServiceAccountRegistry):

    def __init__(self, cache: Dict[str, ServiceAccount]):
        self.cache = cache

        self._consistency_check()

    def _consistency_check(self):
        primaries = [account for account in self.all() if account.primary is True]

        if len(primaries) > 1:
            self.logger.warning("There exists more than one primary in the service account registry.")

    def all(self) -> List['ServiceAccount']:
        return list(self.cache.values())

    def create(self, service_account: ServiceAccount) -> str:
        if (service_account.primary is True) and any([account.primary for account in self.all()]):
            self.logger.info("Primary service account provided. Switching primary account from account")
            for account_id, account in self.cache.items():
                if account.primary is True:
                    self.logger.debug(f"Setting primary of account {account.id} to False")
                    account.primary = False

        self.cache[service_account.id] = service_account
        return service_account.id

    def delete(self, account_id: str) -> str:
        return self.cache.pop(account_id).id

    def set_primary(self, account_id: str) -> str:
        if account_id not in self.cache.keys():
            raise NoAccountFound(account_id)

        if any([account.primary for account in self.all()]):
            self.logger.info("Switching primary account")
            for account_id, account in self.cache.items():
                if account.primary is True:
                    self.logger.debug(f"Setting primary of account {account.id} to False")
                    account.primary = False

        self.cache[account_id].primary = True
        return account_id

    def set_configurations(self, account_id: str, configurations: PropertyFile) -> str:
        if account_id not in self.cache.keys():
            raise NoAccountFound(account_id)

        self.cache[account_id].extra_confs = configurations
        return account_id


def parse_conf_overrides(conf_args: List, environ: Dict = os.environ) -> PropertyFile:
    """Parse --conf overrides passed to spark-submit

    Args:
        conf_args: list of all --conf 'k1=v1' type args passed to spark-submit.
            Note v1 expression itself could be containing '='
        environ: dictionary with environment variables as key-value pairs
    """
    conf_overrides = dict()
    if conf_args:
        for c in conf_args:
            try:
                kv = c.split("=")
                k = kv[0]
                v = "=".join(kv[1:])
                conf_overrides[k] = environ.get(v, v)
            except IndexError:
                raise FormatError("Configuration related arguments parsing error. "
                                  "Please check input arguments and try again.")
    return PropertyFile(conf_overrides)


class SparkDeployMode(str, Enum):
    CLIENT = "client"
    CLUSTER = "cluster"


class SparkInterface(WithLogging):

    def __init__(self, service_account: ServiceAccount, defaults: Defaults):
        self.service_account = service_account
        self.defaults = defaults

    @staticmethod
    def _read_properties_file(namefile: Optional[str]) -> PropertyFile:
        return PropertyFile.read(namefile) if namefile is not None else PropertyFile.empty()

    def spark_submit(self, deploy_mode: SparkDeployMode, cli_property: Optional[str], extra_args: List[str]):
        with umask_named_temporary_file(
                mode="w", prefix="spark-conf-", suffix=".conf"
        ) as t:
            self.logger.debug(f"Spark props available for reference at {t.name}\n")

            (
                    self._read_properties_file(self.defaults.static_conf_file) +
                    self.service_account.configurations +
                    self._read_properties_file(self.defaults.env_conf_file) +
                    self._read_properties_file(cli_property)
            ).log().write(t.file)

            t.flush()

            submit_args = [
                              f"--master k8s://{self.service_account.api_server}",
                              f"--deploy-mode {deploy_mode}",
                              f"--properties-file {t.name}",
                          ] + extra_args

            submit_cmd = f"{self.defaults.spark_submit} {' '.join(submit_args)}"

            self.logger.debug(submit_cmd)
            os.system(submit_cmd)

    def spark_shell(self, cli_property: PropertyFile, extra_args: List[str]):
        pass

    def pyspark_shell(self, cli_property: PropertyFile, extra_args: List[str]):
        pass
