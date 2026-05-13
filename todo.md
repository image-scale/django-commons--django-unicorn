# Todo

## Plan
Build the reactive component framework from the most important user-facing feature (the Component class) outward. Each task adds complete, testable functionality with all needed infrastructure included in the same commit. Foundation modules (serializer, utils, settings) ship alongside the first feature that needs them. Core request processing comes after the component system is solid.

## Tasks
- [x] Task 1: Core component framework with serialization and utilities — users define components as Python classes with reactive attributes and methods, the framework introspects public/private members, serializes data to JSON, manages settings, and provides lifecycle hooks and signals
- [>] Task 2: Type casting and method call parsing — cast frontend values to Python types based on type hints (int, float, datetime, UUID, bool, dataclass, Pydantic) and parse method call strings like "set_name('Bob', age=30)" into structured data via AST
- [ ] Task 3: Template rendering with data-binding attributes — render component templates with automatic injection of component ID, serialized data, checksum, and metadata on the root HTML element, including HTML well-formedness checking
- [ ] Task 4: Template tags for embedding components — {% unicorn 'component-name' %} tag to render components inline and {% unicorn_scripts %} for including required frontend scripts, with argument passing and parent/child support
- [ ] Task 5: Action processing and message endpoint — AJAX POST endpoint that receives user interactions, validates checksums, classifies actions (syncInput, callMethod, reset, refresh, toggle), processes them against the component, and returns updated DOM/data/errors
- [ ] Task 6: Component caching — persist component trees between AJAX requests using Django's cache framework, handle pickling with circular parent/child references via lightweight stubs
- [ ] Task 7: Form validation — components declare a Django Form/ModelForm class and validate user input against it, with structured error reporting back to the frontend
- [ ] Task 8: Management command — Django manage.py command to scaffold new component files (Python class and HTML template) in the appropriate app directory
