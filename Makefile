.PHONY: clean publish tests integration units

clean:

publish:
	twine upload dist/*

integration:
	./tests/integration/runtests.sh

units:
	PYTHONPATH=$(shell pwd) pytest tests

tests:
	units
	integration
