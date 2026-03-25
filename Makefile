PYTHON ?= python3
DB ?= subscriptions.db
OUTDIR ?= subscriptions
CATALOGUE ?= ../configs

.PHONY: help check import generate rebuild clean

help:
	@printf '%s\n' \
		'Available targets:' \
		'  make check     - syntax-check Python scripts' \
		'  make import    - rebuild the SQLite database from configs' \
		'  make generate  - generate subscription files from the database' \
		'  make rebuild   - run import and generate' \
		'  make clean     - remove generated database and subscriptions'

check:
	$(PYTHON) -m py_compile import_configs.py generate_subscriptions.py

import:
	./import_configs.py --catalogue "$(CATALOGUE)" --dbpath "$(DB)"

generate:
	./generate_subscriptions.py --dbpath "$(DB)" --outdir "$(OUTDIR)"

rebuild: import generate

clean:
	rm -rf "$(DB)" "$(OUTDIR)"
