.PHONY: build release testpypi test lint

build:
	uv build

test:
	coverage run -m pytest tests/ -v
	coverage report --fail-under=80

lint:
	ruff check djangosdk/

release:
	@if [ -z "$(VERSION)" ]; then echo "Usage: make release VERSION=0.2.0"; exit 1; fi
	git tag v$(VERSION)
	git push origin v$(VERSION)

testpypi:
	uv publish --index testpypi
