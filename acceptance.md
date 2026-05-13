# Acceptance Criteria

## Tasks 1-4: Previously completed
- [x] All criteria met

## Task 5: Action processing and message endpoint

### Acceptance Criteria
- [x] Action base class parses action_type and payload from a dict
- [x] SyncInput action extracts name and value from payload
- [x] CallMethod action parses method_name, args, and kwargs from payload name
- [x] Reset, Refresh, Toggle actions are correctly classified
- [x] set_property_value sets a simple property on a component
- [x] set_property_value handles nested dot-notation properties (e.g. "author.name")
- [x] set_property_value enforces access control (rejects private properties)
- [x] set_property_value fires updating/updated signals and lifecycle hooks
- [x] ComponentRequest parses JSON body, extracts data/id/epoch/actions
- [x] ComponentRequest validates checksum integrity (rejects tampered data)
- [x] The message view processes a POST request with syncInput actions
- [x] The message view processes callMethod actions and returns method results
- [x] The message view handles $reset by restoring component to initial state
- [x] The message view handles $toggle by inverting a boolean property
- [x] The message view returns JSON with id, dom, data, errors, and calls
- [x] The message view requires POST method (rejects GET)
- [x] The message view validates CSRF token

## Task 6: Component caching

### Acceptance Criteria
- [x] CacheableComponent strips request, extra_context, and forms before pickling
- [x] CacheableComponent replaces parent/children with PointerUnicornView stubs
- [x] CacheableComponent restores all stripped state on context exit
- [x] CacheableComponent restores state even when pickle fails (UnicornCacheError)
- [x] cache_full_tree caches entire component tree via Django cache
- [x] restore_from_cache rebuilds parent/child tree from cached stubs
- [x] restore_from_cache returns None for missing cache keys
- [x] Component.create() checks cache before building a new component
- [x] Component.create() with use_cache=False bypasses cache
- [x] Message view calls cache_full_tree before rendering

## Task 7: Form validation

### Acceptance Criteria
- [x] Component validates data using form_class (Form or ModelForm)
- [x] validate() returns errors dict with field-specific validation errors
- [x] validate(model_names=[...]) only validates specified fields
- [x] is_valid() returns True/False based on validation
- [x] _handle_validation_error processes dict ValidationErrors with error codes
- [x] _handle_validation_error processes string ValidationErrors
- [x] _handle_validation_error raises AssertionError when no error code
- [x] Message view catches ValidationError from method calls
- [x] Message view calls validate after processing actions
- [x] Validation errors appear in response JSON errors field

## Task 8: Management command

### Acceptance Criteria
- [x] startunicorn command accepts app_name and component_names arguments
- [x] Command creates components directory with __init__.py
- [x] Command creates templates/unicorn directory
- [x] Command generates Python component file with PascalCase class name
- [x] Command generates HTML template file with component name
- [x] Command skips existing component/template files with a message
- [x] Command handles nested component names (e.g. "sub.my-widget")
- [x] Command handles multiple component names in one invocation
- [x] Command raises CommandError for non-existent apps
