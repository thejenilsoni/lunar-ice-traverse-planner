.PHONY: api web test quality demo

api:
	uvicorn services.api.app.main:app --reload --port 8000

web:
	npm run dev

test:
	pytest
	npm run test:web

quality:
	ruff check ml services tests scripts
	pytest
	npm run test:web
	npm run lint
	npm run typecheck
	npm run build

demo:
	python scripts/generate_demo_scene.py
