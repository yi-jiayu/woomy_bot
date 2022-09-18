from dataclasses import dataclass
from datetime import datetime

import pendulum


@dataclass
class SalmonRotation:
    start_time: datetime
    end_time: datetime
    stage: str
    weapons: list[str]
    thumbnail: str


@dataclass
class Schedule:
    salmon_run: list[SalmonRotation]


class Client:
    def __init__(self, http_client):
        self.http_client = http_client

    async def schedule(self) -> Schedule:
        response = await self.http_client.get(
            "https://splatoon3.ink/data/schedules.json"
        )
        response.raise_for_status()
        data = response.json()
        salmon_run_schedule_data = data["data"]["coopGroupingSchedule"][
            "regularSchedules"
        ]["nodes"]
        salmon_run_rotations = []
        for datum in salmon_run_schedule_data:
            start_time = pendulum.parse(datum["startTime"])
            end_time = pendulum.parse(datum["endTime"])
            stage = datum["setting"]["coopStage"]["name"]
            thumbnail = datum["setting"]["coopStage"]["thumbnailImage"]["url"]
            weapons = [weapon["name"] for weapon in datum["setting"]["weapons"]]
            salmon_run_rotations.append(
                SalmonRotation(
                    start_time=start_time,
                    end_time=end_time,
                    stage=stage,
                    weapons=weapons,
                    thumbnail=thumbnail,
                )
            )
        return Schedule(
            salmon_run=salmon_run_rotations,
        )
