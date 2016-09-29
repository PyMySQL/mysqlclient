.PHONY: build
build:
	python3 setup.py build_ext -if


.PHONY: clean
clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm *.so
	python3 setup.py clean
