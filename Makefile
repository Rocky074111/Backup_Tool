.PHONY: all install test clean coverage lint docs

all: install test

install:
	pip install -e .

test:
	python -m unittest discover tests

coverage:
	python run_tests.py --html

lint:
	pip install flake8
	flake8 backuptool tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

docs:
	pip install sphinx
	mkdir -p docs/source
	sphinx-quickstart -q -p "Backup Tool" -a "Your Name" -v "0.1.0" docs/source
	sphinx-build -b html docs/source docs/build

clean-win:
	if exist build rmdir /s /q build
	if exist dist rmdir /s /q dist
	if exist *.egg-info rmdir /s /q *.egg-info
	if exist .coverage del .coverage
	if exist htmlcov rmdir /s /q htmlcov
	if exist __pycache__ rmdir /s /q __pycache__
	for /r . %%f in (*.pyc) do del %%f
	for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
