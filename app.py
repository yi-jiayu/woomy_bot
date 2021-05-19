from datetime import datetime, timedelta, timezone
from itertools import islice

from flask import Flask, jsonify, request

from splatoon import Rotation, rotations_since

app = Flask(__name__)

sgt = timezone(timedelta(hours=8))


def build_result(rota: Rotation, t):
    if rota.start_time < t:
        dt = rota.end_time - t
        verb = 'Ends'
    else:
        dt = rota.start_time - t
        verb = 'Starts'
    hours = dt.seconds // 3600
    minutes = dt.seconds % 60
    msg = f'{verb} in {hours} h {minutes} m'
    return {
        "type": "article",
        "id": rota.start_time.isoformat(),
        "title": rota.stage,
        "description": f'{rota.start_time_formatted(sgt)} - {rota.end_time_formatted(sgt)}',
        "input_message_content": {
            "message_text": f"""<strong>{rota.stage}</strong>
{rota.start_time_formatted(sgt)} - {rota.end_time_formatted(sgt)}
{msg}
{', '.join(rota.weapons)}""",
            "parse_mode": "HTML",
        },
        "thumb_url": "https://leanny.github.io/stages/Fld_Shakeup_Cop.png",
    }


@app.post("/")
def webhook():
    data = request.get_json()
    if "inline_query" in data:
        inline_query = data["inline_query"]
        inline_query_id = inline_query["id"]
        t = datetime.now(tz=timezone.utc)
        rotas = islice(rotations_since(t), 5)
        results = [build_result(rota, t) for rota in rotas]
        res = {
            "method": "answerInlineQuery",
            "inline_query_id": inline_query_id,
            "results": results,
        }
        return jsonify(res)
    return "OK"
