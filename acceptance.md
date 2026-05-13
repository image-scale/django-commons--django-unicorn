# Acceptance Criteria

## Task 1: Core component framework with serialization and utilities
### Acceptance Criteria
- [x] All criteria met (24/24)

## Task 2: Type casting and method call parsing

### Acceptance Criteria
- [ ] cast_value(int, "42") returns 42
- [ ] cast_value(float, "3.14") returns 3.14
- [ ] cast_value(bool, "True") returns True, cast_value(bool, "False") returns False
- [ ] cast_value(datetime, "2020-09-12T01:02:03") returns a datetime object
- [ ] cast_value(date, "2020-09-12") returns a date object
- [ ] cast_value(time, "01:02:03") returns a time object
- [ ] cast_value(UUID, "valid-uuid-string") returns a UUID object
- [ ] cast_value handles Optional types (returns None for None value)
- [ ] cast_value handles Union types (tries each type in order)
- [ ] cast_value handles list[int] (casts each element)
- [ ] cast_attribute_value uses type hints from the object to cast values
- [ ] get_type_hints returns type hints for a class including parent classes
- [ ] parse_call_method_name("method_name()") returns ("method_name", (), {})
- [ ] parse_call_method_name("set_name('Bob')") returns ("set_name", ("Bob",), {})
- [ ] parse_call_method_name("set_val(1, key='test')") returns ("set_val", (1,), {"key": "test"})
- [ ] parse_call_method_name handles $-prefixed special methods
- [ ] parse_kwarg("key='value'") returns {"key": "value"}
- [ ] eval_value("42") returns 42 (integer), eval_value("'hello'") returns "hello" (string)
- [ ] eval_value handles datetime/UUID strings that aren't valid Python literals
