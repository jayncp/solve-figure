current_branch := shell("git branch --show-current")

[group('lint')]
lint:
    uv sync --all-groups
    uv run ruff check .
    uv run ruff format --check --diff .
    uv run ty check .

[group('lint')]
fix-lint:
    uv sync --all-groups
    uv run ruff check --fix --unsafe-fixes .
    uv run ruff format .

[group('test')]
test:
    uv sync --all-groups
    uv run pytest

[group('test')]
check:
    just lint
    just test

[group('git')]
switch:
    if [ {{ current_branch }} != "master" ]; then \
      git switch master; \
      git fetch -p; \
      git branch -D {{ current_branch }}; \
    fi
