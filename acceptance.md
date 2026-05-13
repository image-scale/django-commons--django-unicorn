# Acceptance Criteria

## Tasks 1-3: Previously completed
- [x] All criteria met

## Task 4: Template tags for embedding components

### Acceptance Criteria
- [ ] {% unicorn_scripts %} renders a script tag inclusion template
- [ ] {% unicorn 'component-name' %} renders a component inline in a template
- [ ] The unicorn tag generates a unique component_id for each component
- [ ] The unicorn tag resolves the component name from a template variable
- [ ] The unicorn tag accepts keyword arguments passed to the component
- [ ] Child components use parent ID as part of their component_id
- [ ] Component.create() factory discovers and instantiates components by name
- [ ] Component.create() searches through configured APPS to find components
- [ ] Component.create() raises ComponentModuleLoadError when module not found
- [ ] Component.create() raises ComponentClassLoadError when class not found
- [ ] get_locations returns list of (module, class) pairs for a component name
- [ ] URL configuration provides a message endpoint path
- [ ] unicorn_errors tag renders form validation errors from component context
