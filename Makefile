export PROJECTNAME=$(shell basename "$(PWD)")
export CONTEXT_DIR=build

.SILENT: ;               # no need for @

setup: ## Setup Virtual Env
	python3.11 -m venv venv
	./venv/bin/pip3 install -r requirements-dev.txt
	./venv/bin/python3 -m pip install --upgrade pip

deps: ## Install dependencies
	./venv/bin/pip3 install --upgrade -r requirements-dev.txt
	./venv/bin/python3 -m pip install --upgrade pip

pre-commit: ## Manually run all pre-commit hooks
	./venv/bin/pre-commit install
	./venv/bin/pre-commit run --all-files

pre-commit-tool: ## Manually run a single pre-commit hook
	./venv/bin/pre-commit run $(TOOL) --all-files

clean: ## Clean package
	find . -type d -name '__pycache__' | xargs rm -rf
	rm -rf build dist

package: clean pre-commit ## Run installer
	pyinstaller app.spec

install-macosx: package ## Installs application in users Application folder
	./scripts/install-macosx.sh ChatCircuit.app

context: clean ## Build context file from application sources
	echo "Generating context in $(CONTEXT_DIR) directory"
	mkdir -p $(CONTEXT_DIR)/
	llm-context-builder.py --extensions .py --ignored_dirs build dist generated venv .venv .idea .aider.tags.cache.v3 --print_contents > $(CONTEXT_DIR)/chat-circuit.py
	echo `pwd`/$(CONTEXT_DIR)/chat-circuit.py | pbcopy

run: ## Runs the application
	export PYTHONPATH=`pwd`:$PYTHONPATH && ./venv/bin/python3 main.py

test: ## Tests the application
	./venv/bin/pytest -v

.PHONY: help
.DEFAULT_GOAL := help

help: Makefile
	echo
	echo " Choose a command run in "$(PROJECTNAME)":"
	echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	echo
