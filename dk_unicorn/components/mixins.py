from django.db.models import Model

from dk_unicorn.serializer import model_value


class ModelValueMixin:
    def value(self, *fields):
        if isinstance(self, Model):
            return model_value(self, *fields)
        return {}
