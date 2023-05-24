import os

from spark8t.domain import Defaults, PropertyFile, ServiceAccount
from spark8t.services import K8sServiceAccountRegistry, KubeInterface

# Defaults for spark-client
defaults = Defaults(dict(os.environ))  # General defaults

# Create a interface connection to k8s
kube_interface = KubeInterface(defaults.kube_config)
# or use KubeInterface.autodetect(kubectl_cmd="kubectl")

# We have some properties of the connection readily available
kube_interface.namespace
kube_interface.api_server

# To interact with the K8s CLI
service_accounts = kube_interface.exec("get sa -A")
service_accounts_namespace = kube_interface.exec(
    "get sa", namespace=kube_interface.namespace
)

# Registry to Interact with K8s to create and manage the Spark service accounts
registry = K8sServiceAccountRegistry(kube_interface)

# Listing spark service accounts
spark_service_accounts = registry.all()

configurations = PropertyFile({"my-key": "my-value"})
service_account = ServiceAccount(
    name="my-spark",
    namespace="default",
    api_server=kube_interface.api_server,
    primary=False,
    extra_confs=configurations,
)

service_account_id = registry.create(service_account)

# This should now be populated
spark_service_accounts = registry.all()

# Accounts can be retrieved by id, namely "namespace:user"
retrieved_account = registry.get(service_account_id)
# or retrieved_account = registry.get(service_account.id)

# We can change primary
registry.set_primary(service_account.id)

# Reset configurations
registry.set_configurations(
    service_account.id, PropertyFile({"my-key-2": "my-value-2"})
)

# get the primary
primary_account = registry.get_primary()

if primary_account is None:
    raise ValueError()

# Read properties file
static_property = PropertyFile.read(defaults.static_conf_file)

merged_property = static_property + primary_account.extra_confs
# merged_property = static_property + primary_account.configurations      # configurations also have namespace and accountName properties set

# Write out property file
with open("my-file", "w") as fid:
    merged_property.log().write(fid)

# Delete service account
registry.delete(primary_account.id)
