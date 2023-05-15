.PHONY: build
build:
	python setup.py build_ext -if

.PHONY: doc
doc:
	pip install .
	pip install sphinx
	cd doc && make html

.PHONY: clean
clean:
	python setup.py clean
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -rf build

.PHONY: check
check:
	ruff .
	black *.py src
