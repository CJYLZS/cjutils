build:
	python3 setup.py sdist

install:
	python3 setup.py install

remove:
	python3 -m pip uninstall -y cjutils

upload: clean build
	twine upload dist/*	

clean:
	rm -rf build cjutils.egg-info dist

format:
	python3 -m cjutools format -iP .

test:
	python3 test/test.py

all: clean format test build remove install
