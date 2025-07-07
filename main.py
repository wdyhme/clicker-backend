# === main.py ===
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import os

app = Flask(__name__)
CORS(app)

DB_PATH = "clicker.db"

# === Инициализация базы данных ===
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                data TEXT
            )
        ''')
        conn.commit()

init_db()

# === Получение данных пользователя ===
@app.route("/get_data", methods=["GET"])
def get_data():
    user_id = request.args.get("user_id")
    username = request.args.get("username")
    if not user_id:
        return jsonify({})

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT data FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            data = json.loads(row[0])
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
            # сохранить нового пользователя
            c.execute("INSERT INTO users (user_id, username, data) VALUES (?, ?, ?)",
                      (user_id, username or "", json.dumps(data)))
            conn.commit()
    return jsonify(data)

# === Сохранение данных пользователя ===
@app.route("/save_data", methods=["POST"])
def save_data():
    req = request.get_json()
    user_id = req.get("user_id")
    data = req.get("data")
    username = data.get("username", "")
    if not user_id or not data:
        return jsonify({"error": "Missing user_id or data"}), 400

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("REPLACE INTO users (user_id, username, data) VALUES (?, ?, ?)",
                  (user_id, username, json.dumps(data)))
        conn.commit()
    return jsonify({"status": "ok"})

# === Получение топа игроков ===
@app.route("/get_top_players", methods=["GET"])
def get_top_players():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT username, data FROM users")
        rows = c.fetchall()

        result = []
        for username, data_str in rows:
            try:
                data = json.loads(data_str)
                total = data.get("totalEarned", 0)
                result.append({
                    "nickname": username or "Anon",
                    "totalEarned": total
                })
            except:
                continue

        result.sort(key=lambda x: -x["totalEarned"])
        return jsonify(result[:20])

# === Запуск ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
