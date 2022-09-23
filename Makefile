build:
	python3 setup.py sdist

upload:
	twine upload dist/*	

clean:
	rm -rf cjutils.egg-info dist