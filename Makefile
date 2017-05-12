PYTHON := python3
TOX := $(PYTHON) -m tox --sitepackages
DOCS_DIR = docs

.NOTPARALLEL:
.PHONY: all clean clean_socket cscope docs lint pep8 test

all: tox
	echo "All tests passed"

clean_coverage:
	rm -f .coverage .coverage.*

tox: clean_socket
	$(TOX)

clean: clean_coverage
	rm -fr build dist *.egg-info .tox MANIFEST .cache
	find ./ -name '*.py[co]' -exec rm -f {} \;
	find ./ -depth -name __pycache__ -exec rm -rf {} \;

README: README.md
	echo -e '.. WARNING: AUTO-GENERATED FILE. DO NOT EDIT.\n' > $@
	pandoc --from=markdown --to=rst $< >> $@

.PHONY: egg_info packages
egg_info:
	$(PYTHON) setup.py egg_info

packages: egg_info README
	$(PYTHON) setup.py packages
	cd dist && for F in *.gz; do sha512sum $${F} > $${F}.sha512sum.txt; done
