import json
from datetime import datetime, timezone
from typing import Tuple, Mapping

from dataclasses import dataclass


@dataclass
class Rotation:
    start_time: datetime
    end_time: datetime
    stage: str
    weapons: Tuple[str]

    def start_time_formatted(self, tz=timezone.utc):
        return self.start_time.astimezone(tz).strftime("%a, %b %d, %I %p")

    def end_time_formatted(self, tz=timezone.utc):
        return self.end_time.astimezone(tz).strftime("%a, %b %d, %I %p")


def _load_rotations_since(t=datetime.now(timezone.utc)):
    with open('MapInfo.min.json') as f:
        map_info = json.load(f)

    maps = {}
    for m in map_info:
        maps[m['Id']] = m['MapFileName']

    with open('WeaponInfo_Main.min.json') as f:
        weapon_info = json.load(f)

    weapons = {}
    for w in weapon_info:
        weapons[w['Id']] = w['Name']

    with open('coop.min.json') as f:
        coop = json.load(f)

    with open('lang_dict_EUen.min.json') as f:
        strings: Mapping[str, str] = json.load(f)

    def weapon_name(id_):
        if id_ == -1:
            return '?'
        elif id_ == -2:
            return '??'
        else:
            return strings[weapons[id_]]

    rotations = []
    for phase in coop['Phases']:
        end_time = datetime.fromisoformat(phase['EndDateTime']).replace(tzinfo=timezone.utc)
        if end_time < t:
            continue
        start_time = datetime.fromisoformat(phase['StartDateTime']).replace(tzinfo=timezone.utc)
        stage = strings[maps[phase['StageID']]]
        loadout = tuple(weapon_name(w) for w in phase['WeaponSets'])
        rotations.append(Rotation(start_time, end_time, stage, loadout))

    return rotations


rotations = _load_rotations_since()


def rotations_since(t=datetime.now(timezone.utc)):
    for r in rotations:
        if r.end_time > t:
            yield r
