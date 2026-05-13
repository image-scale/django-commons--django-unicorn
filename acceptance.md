# Acceptance Criteria

## Task 1: Core component framework with serialization and utilities
### Acceptance Criteria
- [x] All criteria met (24/24)

## Task 2: Type casting and method call parsing
### Acceptance Criteria
- [x] All criteria met (19/19)

## Task 3: Template rendering with data-binding attributes

### Acceptance Criteria
- [ ] UnicornTemplateResponse renders component HTML and injects unicorn:id attribute on root element
- [ ] UnicornTemplateResponse injects unicorn:name with the component name
- [ ] UnicornTemplateResponse injects unicorn:key with the component key
- [ ] UnicornTemplateResponse injects unicorn:data with serialized frontend context variables
- [ ] UnicornTemplateResponse injects unicorn:calls with serialized JS calls array
- [ ] UnicornTemplateResponse injects unicorn:meta with a data checksum
- [ ] get_root_element extracts the first non-script HTML element from fragments
- [ ] get_root_element handles full HTML documents with unicorn:view attribute
- [ ] get_root_element raises error when no root element found
- [ ] assert_has_single_wrapper_element raises error for multiple root elements
- [ ] assert_has_single_wrapper_element raises error for void root elements (br, input, etc.)
- [ ] is_html_well_formed returns True for balanced HTML tags
- [ ] is_html_well_formed returns False for unbalanced HTML tags
- [ ] Component.render() returns rendered HTML string with unicorn attributes
- [ ] content_hash is computed and stored on the component for change detection
