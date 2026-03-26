"""Application entrypoints."""


def build_status_message() -> str:
    """Return a short package status summary for the bootstrap stage."""
    return "equilibrium bootstrap ready: config, base interfaces, and tests"


def main() -> None:
    """CLI entrypoint."""
    print(build_status_message())
