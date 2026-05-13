# Goal

## Project
django-unicorn — a python project.

## Description
A reactive component framework for Django that adds interactive frontend behavior to Django templates using Python classes and standard Django template syntax — without requiring a JavaScript framework. Components are Python classes that extend a base class, with public attributes that become reactive data and methods callable from the frontend. The framework uses AJAX calls to sync state between browser and server, patching the DOM with server-rendered responses.

## Core Capabilities
- Component definition: users create component classes with reactive attributes and callable methods
- Lifecycle hooks: mount, hydrate, complete, rendered, updating/updated/resolved per-property hooks
- JSON serialization: serialize/deserialize Django models, querysets, Pydantic models, UUIDs, Decimals, datetimes
- Type casting: convert frontend string values to correct Python types based on type hints
- Method call parsing: parse method call strings from frontend using AST analysis
- Template rendering: render component templates with data-binding attributes (component ID, serialized data, checksum)
- Template tags: {% unicorn 'name' %} to embed components, {% unicorn_scripts %} for scripts
- Action processing: handle data sync (syncInput), method calls, reset, refresh, toggle via AJAX
- Message endpoint: POST-only AJAX view with checksum validation, action queue, response building
- Component caching: persist component state between requests using Django cache framework
- Form validation: validate input against Django Forms/ModelForms, report errors to frontend
- Management command: scaffold new component files (Python class + HTML template)
- Signals: Django signals for all lifecycle events
- Security: HMAC checksum validation, public/private access control, path traversal prevention

## Scope
- ~25 production source files to implement
- ~40 test files to write
- Reproduce all core source code, tests, and configuration
