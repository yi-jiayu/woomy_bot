from flask import Flask, jsonify, request

app = Flask(__name__)


@app.post("/")
def webhook():
    data = request.get_json()
    if "inline_query" in data:
        inline_query = data["inline_query"]
        inline_query_id = inline_query["id"]
        res = {
            "method": "answerInlineQuery",
            "inline_query_id": inline_query_id,
            "results": [
                {
                    "type": "article",
                    "id": "1",
                    "title": "Spawning Grounds",
                    "description": "Mon, 17/05, 20:00 GMT+8 — Wed, 19/05, 08:00 GMT+8",
                    "input_message_content": {
                        "message_text": """<strong>Spawning Grounds</strong>
Mon, 17/05, 20:00 GMT+8 — Wed, 19/05, 08:00 GMT+8
Undercover Brella, .96 Gal, Glooga Dualies, Splatterscope""",
                        "parse_mode": "HTML",
                    },
                    "thumb_url": "https://leanny.github.io/stages/Fld_Shakeup_Cop.png",
                }
            ],
        }
        return jsonify(res)
    return "OK"
