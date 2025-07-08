from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import json
import os

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL not set")

def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            data JSONB
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route("/get_data", methods=["GET"])
def get_data():
    user_id = str(request.args.get("user_id"))
    username = request.args.get("username") or "Anon"
    if not user_id:
        return jsonify({})

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT data FROM users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()

    if row:
        data = row[0]
    else:
        data = {
            "balance": 0,
            "perClick": 1,
            "passiveIncome": 0,
            "totalEarned": 0,
            "totalClicks": 0,
            "upgrades": {"click": 0, "passive": 0},
            "adsWatchedToday": 0,
            "adsWatchedTotal": 0,
            "ads_watched": {
                "interstitialToday": 0,
                "interstitialTotal": 0,
                "popupToday": 0,
                "popupTotal": 0,
                "inAppToday": 0,
                "inAppTotal": 0
            },
            "username": username
        }
        cur.execute("INSERT INTO users (user_id, username, data) VALUES (%s, %s, %s)",
                    (user_id, username, json.dumps(data)))
        conn.commit()

    cur.close()
    conn.close()
    return jsonify(data)

@app.route("/save_data", methods=["POST"])
def save_data():
    req = request.get_json()
    user_id = str(req.get("user_id"))
    data = req.get("data")
    username = data.get("username", "Anon")

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
    if cur.fetchone():
        cur.execute("UPDATE users SET data = %s, username = %s WHERE user_id = %s",
                    (json.dumps(data), username, user_id))
    else:
        cur.execute("INSERT INTO users (user_id, username, data) VALUES (%s, %s, %s)",
                    (user_id, username, json.dumps(data)))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/get_top_players", methods=["GET"])
def get_top_players():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT username, (data->>'totalEarned')::BIGINT FROM users WHERE username IS NOT NULL ORDER BY (data->>'totalEarned')::BIGINT DESC LIMIT 10")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([
        {"nickname": row[0], "totalEarned": int(row[1])} for row in rows
    ])

@app.route("/get_global_stats", methods=["GET"])
def get_global_stats():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT data FROM users")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    stats = {
        "totalEarned": 0,
        "totalClicks": 0,
        "clickUpgrades": 0,
        "passiveUpgrades": 0,
        "users": len(rows),
        "ads": {
            "interstitialToday": 0,
            "interstitialTotal": 0,
            "popupToday": 0,
            "popupTotal": 0,
            "inAppToday": 0,
            "inAppTotal": 0
        }
    }

    for row in rows:
        data = row[0]
        stats["totalEarned"] += data.get("totalEarned", 0)
        stats["totalClicks"] += data.get("totalClicks", 0)
        stats["clickUpgrades"] += data.get("upgrades", {}).get("click", 0)
        stats["passiveUpgrades"] += data.get("upgrades", {}).get("passive", 0)
        ads = data.get("ads_watched", {})
        stats["ads"]["interstitialToday"] += ads.get("interstitialToday", 0)
        stats["ads"]["interstitialTotal"] += ads.get("interstitialTotal", 0)
        stats["ads"]["popupToday"] += ads.get("popupToday", 0)
        stats["ads"]["popupTotal"] += ads.get("popupTotal", 0)
        stats["ads"]["inAppToday"] += ads.get("inAppToday", 0)
        stats["ads"]["inAppTotal"] += ads.get("inAppTotal", 0)

    return jsonify(stats)

@app.route("/reset_all", methods=["POST"])
def reset_all():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM users")
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "✅ Reset complete"})

if __name__ == "__main__":
    app.run(debug=True)
