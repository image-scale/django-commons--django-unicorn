# Acceptance Criteria

## Task 1: Core component framework with serialization and utilities

### Acceptance Criteria
- [ ] A Component base class can be instantiated with component_id and component_name
- [ ] Public attributes (non-underscore, non-protected) are discoverable via an attributes method
- [ ] Public methods (non-underscore, non-protected) are discoverable via a methods method
- [ ] Protected names (Django TemplateView internals, lifecycle hooks) are excluded from public access
- [ ] Lifecycle hooks (mount, hydrate, complete, rendered, updating, updated, resolved, calling, called) exist as no-op overridable methods
- [ ] Component.reset() restores attributes to their initial values
- [ ] Component.call(function_name, *args) queues JavaScript calls for the frontend
- [ ] generate_checksum(data) produces an HMAC-SHA256 based short checksum using SECRET_KEY
- [ ] serializer.dumps() serializes dicts, ints, floats, strings, lists, Decimals, and nested structures to JSON
- [ ] serializer.dumps() converts float values to strings to prevent JS integer coercion
- [ ] serializer.loads() deserializes JSON strings back to dicts
- [ ] serializer.dumps() serializes Django Model instances to dicts with pk and field values
- [ ] serializer.dumps() handles objects with a to_json() method
- [ ] Settings are read from Django's UNICORN config key with fallback to DJANGO_UNICORN
- [ ] get_cache_alias() returns the configured cache alias or "default"
- [ ] get_serial_enabled() returns whether serial mode is enabled
- [ ] Error classes exist: ComponentLoadError, ComponentModuleLoadError, ComponentClassLoadError, UnicornViewError, UnicornCacheError
- [ ] 12 lifecycle signals are defined as Django Signal instances
- [ ] get_method_arguments(func) returns the parameter names of a callable
- [ ] is_non_string_sequence(obj) returns True for lists/tuples/sets but False for strings
- [ ] sanitize_html() escapes HTML special characters
- [ ] get_frontend_context_variables() returns serialized JSON of public attributes
- [ ] Component Meta.exclude removes attributes from public access
- [ ] Component Meta.javascript_exclude removes attributes from frontend context but keeps them on the component
