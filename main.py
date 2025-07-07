# === main.py (PostgreSQL version with fix for user_id type) ===
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import json

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL not set")

# === Инициализация таблицы ===
def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            data JSONB
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route("/get_data", methods=["GET"])
def get_data():
    user_id = str(request.args.get("user_id"))
    username = request.args.get("username")
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
            }
        }
        cur.execute("INSERT INTO users (user_id, username, data) VALUES (%s, %s, %s)",
                    (user_id, username or "", json.dumps(data)))
        conn.commit()

    cur.close()
    conn.close()
    print(f"✅ get_data returned for user_id={user_id}")
    return jsonify(data)

@app.route("/save_data", methods=["POST"])
def save_data():
    req = request.get_json()
    user_id = str(req.get("user_id"))  # ← Fix here
    data = req.get("data")

    print("=== /save_data called ===")
    print("user_id:", user_id)
    print("data:", data)

    if not user_id or not data:
        return jsonify({"error": "Missing user_id or data"}), 400

    if not isinstance(data, dict):
        print("❌ data is not a dict")
        return jsonify({"error": "Invalid data format"}), 400

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
    exists = cur.fetchone()

    if exists:
        cur.execute("UPDATE users SET data = %s, username = %s WHERE user_id = %s",
                    (json.dumps(data), data.get("username", ""), user_id))
    else:
        cur.execute("INSERT INTO users (user_id, username, data) VALUES (%s, %s, %s)",
                    (user_id, data.get("username", ""), json.dumps(data)))

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Data saved for user_id={user_id}")
    return jsonify({"status": "ok", "saved_data": data})

@app.route("/get_top_players", methods=["GET"])
def get_top_players():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT username, data FROM users")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for username, data in rows:
        try:
            total = data.get("totalEarned", 0)
            result.append({"nickname": username or "Anon", "totalEarned": total})
        except:
            continue

    result.sort(key=lambda x: -x["totalEarned"])
    return jsonify(result[:20])

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
            "interstitialToday": 0, "interstitialTotal": 0,
            "popupToday": 0, "popupTotal": 0,
            "inAppToday": 0, "inAppTotal": 0,
        }
    }

    for (data,) in rows:
        try:
            stats["totalEarned"] += data.get("totalEarned", 0)
            stats["totalClicks"] += data.get("totalClicks", 0)
            stats["clickUpgrades"] += data.get("upgrades", {}).get("click", 0)
            stats["passiveUpgrades"] += data.get("upgrades", {}).get("passive", 0)
            ads = data.get("ads_watched", {})
            for k in stats["ads"]:
                stats["ads"][k] += ads.get(k, 0)
        except:
            continue

    return jsonify(stats)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
