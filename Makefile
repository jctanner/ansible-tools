.PHONY: clean publish tests integration units

clean:
	rm -rf *egg*
	rm -rf dist
	rm -rf .pytest_cache
	find . -type f -name "*.pyc" | xargs rm -f

publish:
	rm -rf dist
	python setup.py sdist
	twine upload dist/*

integration:
	./tests/integration/runtests.sh

units:
	PYTHONPATH=$(shell pwd) pytest tests

tests:
	units
	integration
