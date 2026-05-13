import os
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError

from dk_unicorn.components.unicorn_view import to_pascal_case, to_snake_case

COMPONENT_FILE_CONTENT = """from dk_unicorn.components import UnicornView


class {pascal_case_component_name}View(UnicornView):
    pass
"""

TEMPLATE_FILE_CONTENT = """<div>
    <!-- put component code here -->
</div>
"""


def get_app_path(app_name):
    return Path(apps.get_app_config(app_name).path)


class Command(BaseCommand):
    help = "Creates a new component for dk-unicorn"

    def add_arguments(self, parser):
        parser.add_argument("app_name", type=str)
        parser.add_argument("component_names", nargs="+", type=str, help="Names of components")

    def check_initial_directories(self, app_directory):
        paths = {
            "components": app_directory / "components",
            "templates": app_directory / "templates" / "unicorn",
        }

        is_first = False

        if not paths["components"].exists():
            paths["components"].mkdir()
            self.stdout.write(self.style.SUCCESS(f"Created components directory in '{app_directory.name}'."))
            is_first = True

        (paths["components"] / "__init__.py").touch(exist_ok=True)

        if not paths["templates"].exists():
            paths["templates"].mkdir(parents=True, exist_ok=True)
            self.stdout.write(self.style.SUCCESS(f"Created templates directory in '{app_directory.name}'."))
            is_first = True

        return paths, is_first

    def obtain_nested_path(self, component_name):
        nested_paths = []

        if "." in component_name:
            (*nested_paths, component_name) = component_name.split(".")

        return "/".join(nested_paths), component_name

    def create_nested_directories(self, paths, nested_path):
        if not nested_path:
            return

        nested_paths = nested_path.split("/")

        component_path = paths["components"]
        template_path = paths["templates"]

        for part in nested_paths:
            component_path /= part
            template_path /= part

            if not component_path.exists():
                component_path.mkdir()

            if not template_path.exists():
                template_path.mkdir()

            (component_path / "__init__.py").touch(exist_ok=True)

    def create_component_and_template(self, paths, nested_path, component_name):
        snake_case_name = to_snake_case(component_name)
        pascal_case_name = to_pascal_case(component_name)

        component_path = paths["components"] / nested_path / f"{snake_case_name}.py"

        if component_path.exists():
            self.stdout.write(
                self.style.ERROR(f"Skipping creating {snake_case_name}.py because it already exists.")
            )
        else:
            component_path.write_text(
                COMPONENT_FILE_CONTENT.format(pascal_case_component_name=pascal_case_name)
            )
            self.stdout.write(self.style.SUCCESS(f"Created {component_path}."))

        template_path = paths["templates"] / nested_path / f"{component_name}.html"

        if template_path.exists():
            self.stdout.write(
                self.style.ERROR(f"Skipping creating {component_name}.html because it already exists.")
            )
        else:
            template_path.write_text(TEMPLATE_FILE_CONTENT)
            self.stdout.write(self.style.SUCCESS(f"Created {template_path}."))

    def handle(self, **options):
        base_path = getattr(options, "BASE_DIR", None)

        if not base_path:
            from django.conf import settings
            base_path = getattr(settings, "BASE_DIR", None)

        if not base_path:
            base_path = os.getcwd()

        base_path = Path(base_path)

        if "app_name" not in options:
            raise CommandError("An application name is required.")

        if "component_names" not in options:
            raise CommandError("At least one component name is required.")

        app_name = options["app_name"]

        try:
            app_directory = get_app_path(app_name)
        except LookupError as e:
            raise CommandError(
                f"An app named '{app_name}' does not exist yet. You might need to create it first."
            ) from e

        if not app_directory.exists():
            app_directory.mkdir()

        paths, is_first = self.check_initial_directories(app_directory)

        for component_name in options["component_names"]:
            nested_path, name = self.obtain_nested_path(component_name)
            self.create_nested_directories(paths, nested_path)
            self.create_component_and_template(paths, nested_path, name)
