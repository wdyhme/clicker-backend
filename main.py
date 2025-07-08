# === main.py (финальная версия, сохранение, получение, глобальная статистика) ===
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import json

app = Flask(__name__)
CORS(app)

# Получаем URL базы данных из переменных окружения
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL not set")

# Инициализация таблицы, если она не существует
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

# Получение данных пользователя
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
            "upgrades": {
                "click": 0,
                "passive": 0
            },
            "adsWatchedToday": 0,
            "adsWatchedTotal": 0,
            "ads_watched": {
                "interstitialToday": 0,
                "interstitialTotal": 0,
                "popupToday": 0,
                "popupTotal": 0
                # inApp теперь не учитываем
            },
            "username": username or "Anon"
        }
        cur.execute("INSERT INTO users (user_id, username, data) VALUES (%s, %s, %s)",
                    (user_id, username or "Anon", json.dumps(data)))
        conn.commit()

    cur.close()
    conn.close()
    return jsonify(data)

# Сохранение данных пользователя
@app.route("/save_data", methods=["POST"])
def save_data():
    req = request.get_json()
    user_id = str(req["user_id"])  # обязательно str

    data = req.get("data")
    username = data.get("username", "Anon")
    data_json = json.dumps(data)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("UPDATE users SET data = %s, username = %s WHERE user_id = %s",
                (data_json, username, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok"})


# Глобальная статистика
@app.route("/global_stats", methods=["GET"])
def global_stats():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT data FROM users")
    rows = cur.fetchall()

    total_earned = 0
    total_clicks = 0
    click_upgrades = 0
    passive_upgrades = 0
    interstitial_today = 0
    interstitial_total = 0
    popup_today = 0
    popup_total = 0
    users = 0

    for row in rows:
        data = row[0]
        users += 1
        total_earned += data.get("totalEarned", 0)
        total_clicks += data.get("totalClicks", 0)
        upgrades = data.get("upgrades", {})
        click_upgrades += upgrades.get("click", 0)
        passive_upgrades += upgrades.get("passive", 0)
        ads = data.get("ads_watched", {})
        interstitial_today += ads.get("interstitialToday", 0)
        interstitial_total += ads.get("interstitialTotal", 0)
        popup_today += ads.get("popupToday", 0)
        popup_total += ads.get("popupTotal", 0)

    cur.close()
    conn.close()

    return jsonify({
    "totalEarned": total_earned,
    "totalClicks": total_clicks,
    "clickUpgrades": click_upgrades,
    "passiveUpgrades": passive_upgrades,
    "users": users,
    "ads": {
        "interstitialToday": interstitial_today,
        "interstitialTotal": interstitial_total,
        "popupToday": popup_today,
        "popupTotal": popup_total
    }
})


# Полный сброс БД (для разработки, не вызывай случайно!)
@app.route("/reset_all", methods=["POST"])
def reset_all():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM users")
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "✅ Reset complete"})



@app.route("/get_top_players", methods=["GET"])
def get_top_players():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT username, (data->>'totalEarned')::BIGINT FROM users WHERE username IS NOT NULL ORDER BY (data->>'totalEarned')::BIGINT DESC LIMIT 10")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([
        {"nickname": row[0], "totalEarned": row[1]} for row in rows
    ])


if __name__ == "__main__":
    app.run(debug=True)
