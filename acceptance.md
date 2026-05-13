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
