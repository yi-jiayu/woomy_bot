import pendulum
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import DateTimeRangeField
from django.db import models


class User(AbstractUser):
    pass


class Weapon(models.Model):
    name = models.TextField(unique=True)


class SalmonRunStage(models.Model):
    name = models.TextField(unique=True)


class SalmonRunShift(models.Model):
    stage = models.ForeignKey(SalmonRunStage, on_delete=models.CASCADE)
    time = DateTimeRangeField()

    weapons = models.ManyToManyField(Weapon, blank=True)

    def __str__(self):
        weapons = ", ".join(self.weapons.values_list("name", flat=True))
        stage = self.stage.name
        start_time = self.start_time.format("ddd, MMM D, H A")
        end_time = self.end_time.format("ddd, MMM D, H A")
        return f"{stage} ({start_time} to {end_time}): {weapons}"

    @property
    def start_time(self) -> pendulum.DateTime:
        return pendulum.instance(self.time.lower)

    @property
    def end_time(self) -> pendulum.DateTime:
        return pendulum.instance(self.time.upper)
