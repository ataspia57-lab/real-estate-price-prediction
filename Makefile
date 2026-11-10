.PHONY: install data train test run
install: ; pip install -r requirements.txt
data:    ; python data/generate_dataset.py
train:   ; python -m src.train
test:    ; python -m pytest -q
run:     ; python -m app.server
