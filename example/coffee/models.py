import uuid

from django.db import models


class Flavor(models.Model):
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    parent = models.ForeignKey("self", blank=True, null=True, on_delete=models.SET_NULL)
    float_value = models.FloatField(blank=True, null=True)
    decimal_value = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    uuid = models.UUIDField(default=uuid.uuid4)
    datetime = models.DateTimeField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    time = models.TimeField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)

    class Meta:
        app_label = "coffee"


class Favorite(models.Model):
    is_favorite = models.BooleanField(default=False)
    flavor = models.OneToOneField(Flavor, on_delete=models.CASCADE)

    class Meta:
        app_label = "coffee"


class Taste(models.Model):
    name = models.CharField(max_length=255)
    flavor = models.ManyToManyField(Flavor)

    class Meta:
        app_label = "coffee"


class Origin(models.Model):
    name = models.CharField(max_length=255)
    flavor = models.ManyToManyField(Flavor, related_name="origins")

    class Meta:
        app_label = "coffee"
