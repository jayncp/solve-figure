from equilibrium.app import build_status_message


def test_build_status_message_mentions_bootstrap() -> None:
    message = build_status_message()
    assert "bootstrap" in message
    assert "tests" in message
