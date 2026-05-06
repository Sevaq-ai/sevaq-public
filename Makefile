PYTHON ?= .venv/bin/python

.PHONY: install test backend dashboard

install:
	$(PYTHON) -m pip install -r backend/requirements.txt
	$(PYTHON) -m pip install -r dashboard/requirements.txt

test:
	$(PYTHON) -m pytest -q tests

backend:
	SEVAQ_DEMO_MODE=mock $(PYTHON) -m uvicorn --app-dir backend app.main:app --reload

dashboard:
	$(PYTHON) -m streamlit run dashboard/streamlit_app.py
