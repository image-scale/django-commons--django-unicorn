from django.dispatch import Signal

component_mounted = Signal()
component_hydrated = Signal()
component_completed = Signal()
component_rendered = Signal()
component_parent_rendered = Signal()
component_property_updating = Signal()
component_property_updated = Signal()
component_property_resolved = Signal()
component_method_calling = Signal()
component_method_called = Signal()
component_pre_parsed = Signal()
component_post_parsed = Signal()
