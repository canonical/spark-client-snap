# Signifies our desired python version
# Makefile macros (or variables) are defined a little bit differently than traditional bash, keep in mind that in the Makefile there's top-level Makefile-only syntax, and everything else is bash script syntax.
PYTHON = poetry run

# .PHONY defines parts of the makefile that are not dependant on any specific file
# This is most often used to store functions
.PHONY = help setup format build install uninstall checks unittest integration-test clean

folders := helpers tests
files := $(shell find . -name "*.py")

# Uncomment to store cache installation in the environment
# package_dir := $(shell python -c 'import site; print(site.getsitepackages()[0])')
package_dir := .make_cache
package_name=$(shell grep 'name:' snap/snapcraft.yaml | tail -n1 | awk '{print $$2}')


$(shell mkdir -p $(package_dir))

POETRY_EXISTS := $(shell command -v poetry 2> /dev/null)
SNAP_EXISTS := $(shell snap list | grep $(package_name) 2> /dev/null)

export PATH := ${PATH}:${HOME}/.local/bin

pre_deps_tag := $(package_dir)/.pre_deps
checks_tag := $(package_dir)/.check_tag
build_tag := $(package_dir)/.build_tag
install_tag := $(package_dir)/.install_tag
setup_tag := $(package_dir)/.setup_tag
k8s_tag := $(package_dir)/.k8s_tag

# ======================
# Rules and Dependencies
# ======================

help:
	@echo "---------------HELP-----------------"
	@echo "Package Name: $(package_name)"
	@echo " "
	@echo "Type 'make' followed by one of these keywords:"
	@echo " "
	@echo "  - setup for installing base requirements"
	@echo "  - format for reformatting files to adhere to PEP8 standards"
	@echo "  - build for creating the SNAP file"
	@echo "  - install for installing the package"
	@echo "  - uninstall for uninstalling the environment"
	@echo "  - checks for running format, mypy, lint and tests altogether"
	@echo "  - unittest for running unittests"
	@echo "  - integration-test for running integration tests"
	@echo "  - clean for removing cache file"
	@echo "------------------------------------"


$(pre_deps_tag):
ifndef POETRY_EXISTS
	@echo "Installing Poetry"
	curl -sSL https://install.python-poetry.org | python3 -
	which poetry
	poetry --version
	touch $(pre_deps_tag)
else
	@echo "Poetry already installed"
	poetry --version
	touch $(pre_deps_tag)
endif


$(setup_tag): $(pre_deps_tag) pyproject.toml
	@echo "==Setting up package environment=="
	poetry config virtualenvs.prefer-active-python true
	poetry lock --no-update
	poetry install --with unit
	touch $(setup_tag)

setup: $(setup_tag)

requirements.txt: poetry.lock pyproject.toml
	poetry export -f requirements.txt --output requirements.txt --without dev

format: setup $(files)
	${PYTHON} tox -e fmt

unittest: setup $(files)
	${PYTHON} tox -e unit

$(checks_tag): $(setup_tag)
	${PYTHON} tox
	touch $(checks_tag)

checks: $(checks_tag)

$(build_tag): checks snap/snapcraft.yaml
	@echo "==Building SNAP=="
	snapcraft
	ls -rt  *.snap | tail -1 > $(build_tag)

build: $(build_tag)

$(install_tag): $(build_tag)
	@echo "==Installing SNAP $(package_name)=="
	sudo snap install $(shell cat $(build_tag)) --dangerous
	touch $(install_tag)

install: $(install_tag)

uninstall:
	@echo "==Uninstall SNAP $(package_name)=="
	sudo snap remove $(package_name)
	rm -f $(install_tag)

$(k8s_tag):
	/bin/bash ./tests/integration/setup-microk8s.sh
	sg microk8s ./tests/integration/config-microk8s.sh
	touch $(k8s_tag)

microk8s: $(k8s_tag)

integration-tests: setup microk8s
ifndef SNAP_EXISTS
	@echo "Installing snap first"
	make install
	${PYTHON} tox -e integration
else
	@echo "snap already installed"
	${PYTHON} tox -e integration
endif

clean:
	@echo "==Cleaning environment=="
	rm -rf *.snap requirements.txt
	rm -rf *.egg-info .mypy_cache .mypy .tox .pytest_cache .make_cache .coverage .kube
	rm -rf $(shell find . -name "*.pyc") $(shell find . -name "__pycache__")
