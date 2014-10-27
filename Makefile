.PHONY: coverage docs flakes cloc
	
coverage:
	-coverage run --timid --source=lymph -m py.test lymph
	coverage html

docs:
	cd docs && make html

clean-docs:
	cd docs && make clean html

flakes:
	@flake8 lymph | cat

cloc:
	@cloc --quiet lymph

