import io
import os
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from spark_client.utils import WithLogging, union


class PropertyFile(WithLogging):
    def __init__(self, props: Dict[str, Any]):
        self.props = props

    def __len__(self):
        return len(self.props)

    @classmethod
    def _is_property_with_options(cls, key: str) -> bool:
        """Check if a given property is known to be options-like requiring special parsing.

        Args:
            key: Property for which special options-like parsing decision has to be taken
        """
        return key in ["spark.driver.extraJavaOptions"]

    @classmethod
    def _read_property_file_unsafe(cls, name: str) -> Dict:
        """Read properties in given file into a dictionary.

        Args:
            name: file name to be read
        """
        defaults = dict()
        with open(name) as f:
            for line in f:
                kv = list(filter(None, re.split("=| ", line.strip())))
                k = kv[0].strip()
                if cls._is_property_with_options(k):
                    kv2 = line.split("=", 1)
                    v = kv2[1].strip()
                else:
                    v = kv[1].strip()
                defaults[k] = os.path.expandvars(v)
        return defaults

    @classmethod
    def read(cls, filename: str) -> "PropertyFile":
        """Safely read properties in given file into a dictionary.

        Args:
            filename: file name to be read safely
        """
        try:
            return PropertyFile(cls._read_property_file_unsafe(filename))
        except FileNotFoundError as e:
            raise e

    def write(self, fp: io.TextIOWrapper) -> "PropertyFile":
        """Write a given dictionary to provided file descriptor.

        Args:
            fp: file pointer to write to
        """
        for k, v in self.props.items():
            line = f"{k}={v.strip()}"
            fp.write(line + "\n")
        return self

    def log(self, log_func: Optional[Callable[[str], None]] = None) -> "PropertyFile":
        """Print a given dictionary to screen."""

        printer = (lambda msg: self.logger.info(msg)) if log_func is None else log_func

        for k, v in self.props.items():
            printer(f"{k}={v}")
        return self

    @classmethod
    def _parse_options(cls, options_string: Optional[str]) -> Dict:
        options: Dict[str, str] = dict()

        if not options_string:
            return options

        # cleanup quotes
        line = options_string.strip().replace("'", "").replace('"', "")
        for arg in line.split("-D")[1:]:
            kv = arg.split("=")
            options[kv[0].strip()] = kv[1].strip()

        return options

    @property
    def options(self) -> Dict[str, Dict]:
        """Extract properties which are known to be options-like requiring special parsing."""
        return {
            k: self._parse_options(v)
            for k, v in self.props.items()
            if self._is_property_with_options(k)
        }

    @staticmethod
    def _construct_options_string(options: Dict) -> str:
        result = ""
        for k in options:
            v = options[k]
            result += f" -D{k}={v}"
        return result

    @classmethod
    def empty(cls) -> "PropertyFile":
        return PropertyFile(dict())

    def __add__(self, other: "PropertyFile"):
        return self.union([other])

    def union(self, others: List["PropertyFile"]) -> "PropertyFile":
        all_together = [self] + others

        simple_properties = union(*[prop.props for prop in all_together])
        merged_options = {
            k: self._construct_options_string(v)
            for k, v in union(*[prop.options for prop in all_together])
        }
        return PropertyFile(union(*[simple_properties, merged_options]))


class Defaults:
    def __init__(self, environ: Dict = dict(os.environ)):
        self.environ = environ if environ is not None else {}

    @property
    def snap_folder(self) -> str:
        return self.environ["SNAP"]

    @property
    def static_conf_file(self) -> str:
        """Return static config properties file packaged with the client snap."""
        return f"{self.environ.get('SNAP')}/conf/spark-defaults.conf"

    @property
    def dynamic_conf_file(self) -> str:
        """Return dynamic config properties file generated during client setup."""
        return f"{self.environ.get('SNAP_USER_DATA')}/spark-defaults.conf"

    @property
    def env_conf_file(self) -> Optional[str]:
        """Return env var provided by user to point to the config properties file with conf overrides."""
        return self.environ.get("SNAP_SPARK_ENV_CONF")

    @property
    def snap_temp_dir(self) -> str:
        """Return /tmp directory as seen by the snap, for user's reference."""
        return "/tmp/snap.spark-client"

    @property
    def service_account(self):
        return "spark"

    @property
    def namespace(self):
        return "defaults"

    @property
    def home_folder(self):
        return self.environ.get("SNAP_REAL_HOME", self.environ["HOME"])

    @property
    def kube_config(self) -> str:
        """Return default kubeconfig to use if not explicitly provided."""
        return self.environ.get("KUBECONFIG", f"{self.home_folder}/.kube/config")

    @property
    def kubectl_cmd(self) -> str:
        """Return default kubectl command."""
        return (
            f"{self.environ['SNAP']}/kubectl" if "SNAP" in self.environ else "kubectl"
        )

    @property
    def spark_submit(self) -> str:
        return f"{self.environ['SNAP']}/bin/spark-submit"

    @property
    def spark_shell(self) -> str:
        return f"{self.environ['SNAP']}/bin/spark-shell"

    @property
    def pyspark(self) -> str:
        return f"{self.environ['SNAP']}/bin/spark-shell"


@dataclass
class ServiceAccount:
    name: str
    namespace: str
    api_server: str
    primary: bool = False
    extra_confs: PropertyFile = PropertyFile.empty()

    @property
    def id(self):
        return f"{self.namespace}:{self.name}"

    @property
    def _k8s_configurations(self):
        return PropertyFile(
            {
                "spark.kubernetes.authenticate.driver.serviceAccountName": self.name,
                "spark.kubernetes.namespace": self.namespace,
            }
        )

    @property
    def configurations(self) -> PropertyFile:
        return self.extra_confs + self._k8s_configurations
