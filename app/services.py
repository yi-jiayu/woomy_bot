import pendulum
from django.db import transaction

from . import models


@transaction.atomic
def load_salmon_run_shifts(schedule_response):
    shifts = []
    shift_data = schedule_response["data"]["coopGroupingSchedule"]["regularSchedules"][
        "nodes"
    ]
    for shift_datum in shift_data:
        stage_data = shift_datum["setting"]["coopStage"]
        stage, _ = models.SalmonRunStage.objects.get_or_create(
            name=stage_data["name"],
        )

        weapon_data = shift_datum["setting"]["weapons"]
        weapons = []
        for weapon_datum in weapon_data:
            weapon, _ = models.Weapon.objects.get_or_create(
                name=weapon_datum["name"],
            )
            weapons.append(weapon)

        start_time = pendulum.parse(shift_datum["startTime"])
        end_time = pendulum.parse(shift_datum["endTime"])
        shift, _ = models.SalmonRunShift.objects.update_or_create(
            time=(start_time, end_time),
            defaults={
                "stage": stage,
            },
        )
        shift.weapons.set(weapons)
        shifts.append(shift)
    return shifts
