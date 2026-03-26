from pathlib import Path

from equilibrium.app import build_status_message, run_demo_pipeline


def test_build_status_message_mentions_figure_path() -> None:
    message = build_status_message("output/demo.png")
    assert "demo pipeline complete" in message
    assert "output/demo.png" in message


def test_run_demo_pipeline_creates_figure(tmp_path: Path) -> None:
    figure_path = run_demo_pipeline(tmp_path)
    assert figure_path.exists()
    assert figure_path.suffix == ".png"
