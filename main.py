from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

import splatoon3

app = FastAPI()

sgt = timezone(timedelta(hours=8))


def time_until_start_or_end_msg(start_time, end_time, now):
    parts = []
    if start_time < now:
        dt = end_time - now
        parts.append(f"Ends in")
    else:
        dt = start_time - now
        parts.append(f"Starts in")
    if days := dt.days:
        parts.append(f"{days} d")
    if hours := dt.seconds // 3600:
        parts.append(f"{hours} h")
    if minutes := (dt.seconds % 3600) // 60:
        parts.append(f"{minutes} m")
    return " ".join(parts)


def build_salmon_result(rota: splatoon3.SalmonRotation, t):
    msg = time_until_start_or_end_msg(rota.start_time, rota.end_time, t)
    start_time = rota.start_time.astimezone(sgt).strftime("%a, %b %d, %I %p")
    end_time = rota.end_time.astimezone(sgt).strftime("%a, %b %d, %I %p")
    return {
        "type": "article",
        "id": f"Salmon Run {rota.start_time.timestamp()}",
        "title": f"Salmon Run: {rota.stage}",
        "description": f'{start_time} - {end_time}\n{", ".join(rota.weapons)}',
        "input_message_content": {
            "message_text": f"""<strong>{rota.stage}</strong>
{start_time} - {end_time}
{msg}
{', '.join(rota.weapons)}""",
            "parse_mode": "HTML",
        },
        "thumb_url": rota.thumbnail,
    }


class InlineQuery(BaseModel):
    id: str


class Update(BaseModel):
    inline_query: Optional[InlineQuery]


http_client = httpx.AsyncClient(
    headers={"user-agent": "https://github.com/yi-jiayu/woomy_bot"}
)
splatoon_client = splatoon3.Client(http_client=http_client)


@app.post("/")
async def webhook(update: Update):
    if inline_query := update.inline_query:
        inline_query_id = inline_query.id
        t = datetime.now(tz=timezone.utc)

        schedule = await splatoon_client.schedule()

        results = []
        results.extend([build_salmon_result(rota, t) for rota in schedule.salmon_run])
        res = {
            "method": "answerInlineQuery",
            "inline_query_id": inline_query_id,
            "results": results,
            "cache_time": 30,
        }
        return res
    return {}
