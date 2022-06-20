.PHONY: test detail_test api_test temp_test server_test

test:
	python3 -m pytest --cov=DbAdapter -s testDB.py

detail_test:
	python3 -m pytest --cov=DbAdapter --cov-report term-missing -s testDB.py

api_test:
	python3 -m pytest -s test_gRPC_API.py

temp_test:
	python3 -m pytest -s tempTest.py

server_test:
	python3 -m pytest --cov=ServerClass --cov-report term-missing -s server_test.py

2pc_test:
	python3 -m pytest -s test_2pc.py