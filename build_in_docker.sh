docker run --rm -it -v "$(pwd):/app" -w /app -e PIP_ROOT_USER_ACTION='ignore' python:3.13.2 bash -c "
	pip3 install --upgrade setuptools 
	python3 -m pip install -r requirements.txt
	python3 --version
	python3 setup.py build_apps
"
