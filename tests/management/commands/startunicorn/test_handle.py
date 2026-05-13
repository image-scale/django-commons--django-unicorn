import pytest
from django.core.management.base import CommandError

from dk_unicorn.management.commands.startunicorn import Command


def test_handle_no_args(settings):
    settings.BASE_DIR = "/tmp"

    with pytest.raises(CommandError):
        Command().handle()


def test_handle_existing_app(settings, tmp_path, monkeypatch, capsys):
    settings.BASE_DIR = tmp_path
    app_name = "example_coffee"

    monkeypatch.setattr(
        "dk_unicorn.management.commands.startunicorn.get_app_path",
        lambda _: tmp_path / app_name,
    )

    Command().handle(app_name=app_name, component_names=["hello-world"])

    assert (tmp_path / app_name / "components/__init__.py").exists()
    assert (tmp_path / app_name / "components/hello_world.py").exists()
    assert (tmp_path / app_name / "templates/unicorn/hello-world.html").exists()

    component_content = (tmp_path / app_name / "components/hello_world.py").read_text()
    assert "class HelloWorldView(UnicornView):" in component_content
    assert "from dk_unicorn.components import UnicornView" in component_content


def test_handle_creates_template(settings, tmp_path, monkeypatch):
    settings.BASE_DIR = tmp_path
    app_name = "myapp"

    monkeypatch.setattr(
        "dk_unicorn.management.commands.startunicorn.get_app_path",
        lambda _: tmp_path / app_name,
    )

    Command().handle(app_name=app_name, component_names=["my-widget"])

    template_path = tmp_path / app_name / "templates/unicorn/my-widget.html"
    assert template_path.exists()

    content = template_path.read_text()
    assert "<div>" in content


def test_handle_existing_component_skipped(settings, tmp_path, monkeypatch, capsys):
    settings.BASE_DIR = tmp_path
    app_name = "myapp"

    monkeypatch.setattr(
        "dk_unicorn.management.commands.startunicorn.get_app_path",
        lambda _: tmp_path / app_name,
    )

    (tmp_path / app_name).mkdir()
    (tmp_path / app_name / "components").mkdir()
    (tmp_path / app_name / "templates" / "unicorn").mkdir(parents=True)

    Command().handle(app_name=app_name, component_names=["hello-world"])

    captured = capsys.readouterr()
    assert "Created" in captured.out

    Command().handle(app_name=app_name, component_names=["hello-world"])

    captured = capsys.readouterr()
    assert "Skipping" in captured.out


def test_handle_app_not_found(settings, tmp_path):
    settings.BASE_DIR = tmp_path

    with pytest.raises(CommandError, match="does not exist"):
        Command().handle(app_name="nonexistent_app_xyz", component_names=["test"])


def test_handle_nested_component(settings, tmp_path, monkeypatch):
    settings.BASE_DIR = tmp_path
    app_name = "myapp"

    monkeypatch.setattr(
        "dk_unicorn.management.commands.startunicorn.get_app_path",
        lambda _: tmp_path / app_name,
    )

    Command().handle(app_name=app_name, component_names=["sub.nested-comp"])

    assert (tmp_path / app_name / "components/sub/__init__.py").exists()
    assert (tmp_path / app_name / "components/sub/nested_comp.py").exists()
    assert (tmp_path / app_name / "templates/unicorn/sub/nested-comp.html").exists()


def test_handle_multiple_components(settings, tmp_path, monkeypatch):
    settings.BASE_DIR = tmp_path
    app_name = "myapp"

    monkeypatch.setattr(
        "dk_unicorn.management.commands.startunicorn.get_app_path",
        lambda _: tmp_path / app_name,
    )

    Command().handle(app_name=app_name, component_names=["comp-a", "comp-b"])

    assert (tmp_path / app_name / "components/comp_a.py").exists()
    assert (tmp_path / app_name / "components/comp_b.py").exists()
    assert (tmp_path / app_name / "templates/unicorn/comp-a.html").exists()
    assert (tmp_path / app_name / "templates/unicorn/comp-b.html").exists()


def test_handle_first_component_message(settings, tmp_path, monkeypatch, capsys):
    settings.BASE_DIR = tmp_path
    app_name = "myapp"

    monkeypatch.setattr(
        "dk_unicorn.management.commands.startunicorn.get_app_path",
        lambda _: tmp_path / app_name,
    )

    Command().handle(app_name=app_name, component_names=["first-comp"])

    captured = capsys.readouterr()
    assert "Created components directory" in captured.out
    assert "Created templates directory" in captured.out
