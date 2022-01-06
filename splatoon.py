from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class SalmonRotation:
    start_time: datetime
    end_time: datetime
    stage: str
    weapons: list[str]
    thumbnail: str


@dataclass
class LobbyRotation:
    start_time: datetime
    end_time: datetime
    rule: str
    stages: tuple[str, str]
    thumbnails: tuple[str, str]


@dataclass
class LobbySchedule:
    gachi: list[LobbyRotation]
    regular: list[LobbyRotation]
    league: list[LobbyRotation]


class Splatoon:
    def __init__(self, client):
        self.client = client

    async def salmon_schedule(self) -> list[SalmonRotation]:
        res = await self.client.get('https://splatoon2.ink/data/coop-schedules.json')
        data = res.json()
        rotations = []
        for rotation in data['details']:
            start_time = datetime.fromtimestamp(rotation['start_time'], timezone.utc)
            end_time = datetime.fromtimestamp(rotation['end_time'], timezone.utc)
            stage = rotation['stage']['name']
            weapons = [weapon['weapon']['name'] for weapon in rotation['weapons']]
            thumbnail = rotation['stage']['image']
            rotations.append(SalmonRotation(start_time, end_time, stage, weapons, thumbnail))
        return rotations

    async def lobby_schedule(self) -> LobbySchedule:
        res = await self.client.get('https://splatoon2.ink/data/schedules.json')
        data = res.json()

        def build_rotation(raw):
            start_time = datetime.fromtimestamp(raw['start_time'], timezone.utc)
            end_time = datetime.fromtimestamp(raw['end_time'], timezone.utc)
            rule = raw['rule']['name']
            stages: tuple[str, str] = (raw['stage_a']['name'], raw['stage_b']['name'])
            thumbnails: tuple[str, str] = (raw['stage_a']['image'], raw['stage_b']['image'])
            return LobbyRotation(start_time, end_time, rule, stages, thumbnails)

        return LobbySchedule(
            gachi=[build_rotation(r) for r in data['gachi']],
            regular=[build_rotation(r) for r in data['regular']],
            league=[build_rotation(r) for r in data['league']],
        )
