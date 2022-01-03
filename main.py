import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

from splatoon import SalmonRotation, LobbyRotation, Splatoon

app = FastAPI()

sgt = timezone(timedelta(hours=8))


def formatted_time(t: datetime, tz):
    return t.astimezone(tz).strftime("%a, %b %d, %I %p")


def time_until_start_or_end_msg(start_time, end_time, now):
    if start_time < now:
        dt = end_time - now
        verb = 'Ends'
    else:
        dt = start_time - now
        verb = 'Starts'
    days = dt.days
    hours = dt.seconds // 3600
    minutes = (dt.seconds % 3600) // 60
    return f'{verb} in {days} d {hours} h {minutes} m'


def build_salmon_result(rota: SalmonRotation, t):
    msg = time_until_start_or_end_msg(rota.start_time, rota.end_time, t)
    return {
        "type": "article",
        "id": f'Salmon Run {rota.start_time.timestamp()}',
        "title": f'Salmon Run: {rota.stage}',
        "description": f'{formatted_time(rota.start_time, sgt)} - {formatted_time(rota.end_time, sgt)}\n{", ".join(rota.weapons)}',
        "input_message_content": {
            "message_text": f"""<strong>{rota.stage}</strong>
{formatted_time(rota.start_time, sgt)} - {formatted_time(rota.end_time, sgt)}
{msg}
{', '.join(rota.weapons)}""",
            "parse_mode": "HTML",
        },
        "thumb_url": "https://leanny.github.io/stages/Fld_Shakeup_Cop.png",
    }


def build_lobby_result(title, rota: LobbyRotation, t):
    msg = time_until_start_or_end_msg(rota.start_time, rota.end_time, t)
    return {
        "type": "article",
        "id": f'{title} {rota.start_time.timestamp()}',
        "title": title,
        "description": f'{formatted_time(rota.start_time, sgt)} - {formatted_time(rota.end_time, sgt)}\n{", ".join(rota.stages)}',
        "input_message_content": {
            "message_text": f"""<strong>{title}</strong>
{formatted_time(rota.start_time, sgt)} - {formatted_time(rota.end_time, sgt)}
{msg}
{', '.join(rota.stages)}""",
            "parse_mode": "HTML",
        },
        "thumb_url": "https://leanny.github.io/stages/Fld_Shakeup_Cop.png",
    }


class InlineQuery(BaseModel):
    id: str


class Update(BaseModel):
    inline_query: Optional[InlineQuery]


client = httpx.AsyncClient()
splatoon = Splatoon(client)


@app.post("/")
async def webhook(update: Update):
    if inline_query := update.inline_query:
        inline_query_id = inline_query.id
        t = datetime.now(tz=timezone.utc)

        salmon_rotations, lobby_schedule = await asyncio.gather(splatoon.salmon_schedule(), splatoon.lobby_schedule())

        results = []
        results.extend([build_salmon_result(rota, t) for rota in salmon_rotations])
        results.extend(
            [build_lobby_result(f'League Battle: {rota.rule}', rota, t) for rota in lobby_schedule.league[:2]])
        results.extend(
            [build_lobby_result(f'Ranked Battle: {rota.rule}', rota, t) for rota in lobby_schedule.gachi[:2]])
        results.extend([build_lobby_result('Turf War', rota, t) for rota in lobby_schedule.regular[:2]])
        res = {
            "method": "answerInlineQuery",
            "inline_query_id": inline_query_id,
            "results": results,
            "cache_time": 0,
        }
        return res
    return {}
