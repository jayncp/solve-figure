current_branch := shell("git branch --show-current")

[group('lint')]
lint:
    uv sync
    uvx ruff check .
    uvx ruff format --check --diff .
    uvx ty check .

[group('lint')]
fix-lint:
    uvx ruff check --fix --unsafe-fixes .
    uvx ruff format .

[group('git')]
switch:
    if [ {{ current_branch }} != "master" ]; then \
      git switch master; \
      git fetch -p; \
      git branch -D {{ current_branch }}; \
    fi