import sys
import os

kubectl_cmd='microk8s.kubectl'

def setup_user(username: str, namespace: str) -> None:
    clusterrolebindingname = username + '-role'
    clusterroleaccess='view'
    os.system("{} create serviceaccount {} --namespace={}".format(kubectl_cmd, username, namespace))
    os.system("{} create clusterrolebinding {} --clusterrole={}  --serviceaccount={}:{} --namespace={}".format(kubectl_cmd, clusterrolebindingname, clusterroleaccess, namespace, username, namespace))
	

def dump_ca_crt(secretname: str) -> None:
    os.system('{} get secret {} -o jsonpath="{{.data.ca\.crt}}" | base64 --decode'.format(kubectl_cmd, secretname))


def dump_token(secretname: str) -> None:
    os.system('{} get secret {} -o jsonpath="{{.data.token}}" | base64 --decode'.format(kubectl_cmd, secretname))

if __name__ == "__main__":

    if len(sys.argv) == 1:
        print("Usage: setup user|cert|token --help", file=sys.stderr)
        sys.exit(-1)


    if sys.argv[1] == 'user':
        if len(sys.argv) == 2 or sys.argv[2] == '-h' or sys.argv[2] == '--help':
            print("Usage: setup user username [namespace]", file=sys.stderr)
            sys.exit(-1)
        
        setup_user(username=sys.argv[2], namespace=sys.argv[3] if len(sys.argv) >= 4 else 'default')

    elif sys.argv[1] == 'cert':
        if len(sys.argv) == 2 or sys.argv[2] == '-h' or sys.argv[2] == '--help':
            print("Usage: setup cert secretname", file=sys.stderr)
            sys.exit(-1)

        dump_ca_crt(secretname=sys.argv[2])

    elif sys.argv[1] == 'token':
        if len(sys.argv) == 2 or sys.argv[2] == '-h' or sys.argv[2] == '--help':
            print("Usage: setup token secretname", file=sys.stderr)
            sys.exit(-1)

        dump_token(secretname=sys.argv[2])

    else:
        print("ERROR: Invalid Arguments.", file=sys.stderr)
        sys.exit(-2)

