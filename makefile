.PHONY lint:
lint:
	echo "Running ruff..."
	uvx ruff check --config pyproject.toml --diff ./src

.PHONY format:
format:
	echo "Running ruff check with --fix..."
	uvx ruff check --config pyproject.toml --fix --unsafe-fixes ./src

.PHONY outdated:
outdated:
	uv tree --outdated --universal