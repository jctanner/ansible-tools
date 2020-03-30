.PHONY: clean publish tests integration units

clean:

publish:
	twine upload dist/*

integration:

units:
	PYTHONPATH=$(shell pwd) pytest tests

tests:
	units
	integration
