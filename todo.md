# Todo

## Plan
Build the reactive component framework from the most important user-facing feature (the Component class) outward. Each task adds complete, testable functionality with all needed infrastructure included in the same commit. Foundation modules (serializer, utils, settings) ship alongside the first feature that needs them. Core request processing comes after the component system is solid.

## Tasks
- [x] Task 1: Core component framework with serialization and utilities — users define components as Python classes with reactive attributes and methods, the framework introspects public/private members, serializes data to JSON, manages settings, and provides lifecycle hooks and signals
- [x] Task 2: Type casting and method call parsing — cast frontend values to Python types based on type hints (int, float, datetime, UUID, bool, dataclass, Pydantic) and parse method call strings like "set_name('Bob', age=30)" into structured data via AST
- [x] Task 3: Template rendering with data-binding attributes — render component templates with automatic injection of component ID, serialized data, checksum, and metadata on the root HTML element, including HTML well-formedness checking
- [x] Task 4: Template tags for embedding components — {% unicorn 'component-name' %} tag to render components inline and {% unicorn_scripts %} for including required frontend scripts, with argument passing and parent/child support
- [x] Task 5: Action processing and message endpoint — AJAX POST endpoint that receives user interactions, validates checksums, classifies actions (syncInput, callMethod, reset, refresh, toggle), processes them against the component, and returns updated DOM/data/errors
- [x] Task 6: Component caching — persist component trees between AJAX requests using Django's cache framework, handle pickling with circular parent/child references via lightweight stubs
- [x] Task 7: Form validation — components declare a Django Form/ModelForm class and validate user input against it, with structured error reporting back to the frontend
- [x] Task 8: Management command — Django manage.py command to scaffold new component files (Python class and HTML template) in the appropriate app directory
- [x] Task 9: @timed profiling decorator — logs function execution time at DEBUG level when Django DEBUG=True, passes through with zero overhead in production
- [x] Task 10: Return class for method results — wraps method return values with special handling for HttpResponseRedirect, HashUpdate, LocationUpdate, PollUpdate
- [x] Task 11: DbModel class — wraps a Django model class reference with name and optional defaults dictionary
- [x] Task 12: ModelValueMixin — provides value() method for serializing Django model instances to dictionaries with optional field filtering
- [x] Task 13: set_property_from_data — type-aware property setting from request data supporting Model, UnicornField, dataclass, QuerySet, and type-hint casting with access control
- [x] Task 14: Return class integration — message view wraps method results in Return objects, response includes redirect/poll data, replaced inline property setter with full set_property_from_data
- [x] Task 15: Setter methods, $validate, $parent — setter method parsing (name='Bob'), $validate action, $parent method delegation through component tree
- [x] Task 16: Union/Optional type hints and Model resolution — method argument casting handles Union/Optional type hints, Model-typed args auto-resolved via pk lookup
- [x] Task 17: Serial request queuing and auth enforcement — serial queue via cache when SERIAL.ENABLED, authentication check with LoginRequiredMiddleware, ignore_m2m=True in initial data hydration
- [x] Task 18: Partial DOM rendering — extract partial DOM fragments by unicorn:key or id from rendered HTML for targeted updates
- [x] Task 19: Meta.safe, dispatch/as_view, error signal, QuerySet support — _handle_safe_fields for unescaped HTML, dispatch()/as_view() for standalone views, error signal on ValidationError, QuerySet in property traversal
