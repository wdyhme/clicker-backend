# ✅ main.py — исправленный backend с учётом всех ошибок
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATA_FILE = "users.json"

def load_all():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_all(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def ensure_user_structure(user, username):
    user.setdefault("nickname", username)
    user.setdefault("balance", 0)
    user.setdefault("perClick", 1)
    user.setdefault("passiveIncome", 0)
    user.setdefault("totalEarned", 0)
    user.setdefault("totalClicks", 0)
    user.setdefault("upgrades", {"click": 0, "passive": 0})
    user.setdefault("ads_watched", {
        "interstitialToday": 0, "interstitialTotal": 0,
        "popupToday": 0, "popupTotal": 0,
        "inAppToday": 0, "inAppTotal": 0
    })
    user.setdefault("adsWatchedToday", 0)
    user.setdefault("adsWatchedTotal", 0)
    user.setdefault("daily_bonus_claimed", False)
    user.setdefault("last_activity", datetime.utcnow().isoformat())
    return user

@app.route("/")
def root():
    return "✅ Clicker backend is working"

@app.route("/get_data")
def get_data():
    user_id = request.args.get("user_id")
    username = request.args.get("username", "")
    if not user_id or not username:
        return jsonify({"error": "missing user_id or username"}), 400

    if user_id == "debug":
        return jsonify({})  # Пропускаем debug_user

    all_data = load_all()
    user = all_data.get(user_id, {})
    user = ensure_user_structure(user, username)
    all_data[user_id] = user
    save_all(all_data)
    return jsonify(user)

@app.route("/save_data", methods=["POST"])
def save_data():
    req = request.get_json()
    user_id = req.get("user_id")
    data = req.get("data")
    if not user_id or not data:
        return jsonify({"error": "invalid payload"}), 400
    if user_id == "debug":
        return jsonify({"success": True})  # Не сохраняем debug_user

    all_data = load_all()
    user = all_data.get(user_id, {})
    user = ensure_user_structure(user, data.get("nickname", ""))

    for key in ["balance", "perClick", "passiveIncome", "totalEarned", "totalClicks",
                "adsWatchedToday", "adsWatchedTotal", "daily_bonus_claimed"]:
        user[key] = data.get(key, user.get(key))

    user["upgrades"] = data.get("upgrades", user["upgrades"])
    user["ads_watched"] = data.get("ads_watched", user["ads_watched"])
    user["last_activity"] = datetime.utcnow().isoformat()

    all_data[user_id] = user
    save_all(all_data)
    return jsonify({"success": True})

@app.route("/get_top_players")
def get_top_players():
    all_data = load_all()
    filtered = {uid: u for uid, u in all_data.items() if uid != "debug"}
    sorted_users = sorted(filtered.items(), key=lambda x: x[1].get("totalEarned", 0), reverse=True)
    return jsonify([
        {
            "nickname": u.get("nickname", ""),
            "totalEarned": u.get("totalEarned", 0)
        }
        for _, u in sorted_users[:20]
    ])

@app.route("/get_global_stats")
def get_global_stats():
    all_data = load_all()
    filtered = {uid: u for uid, u in all_data.items() if uid != "debug"}
    return jsonify({
        "totalEarned": sum(u.get("totalEarned", 0) for u in filtered.values()),
        "totalClicks": sum(u.get("totalClicks", 0) for u in filtered.values()),
        "clickUpgrades": sum(u.get("upgrades", {}).get("click", 0) for u in filtered.values()),
        "passiveUpgrades": sum(u.get("upgrades", {}).get("passive", 0) for u in filtered.values()),
        "users": len(filtered),
        "ads": {
            "interstitialToday": sum(u.get("ads_watched", {}).get("interstitialToday", 0) for u in filtered.values()),
            "interstitialTotal": sum(u.get("ads_watched", {}).get("interstitialTotal", 0) for u in filtered.values()),
            "popupToday": sum(u.get("ads_watched", {}).get("popupToday", 0) for u in filtered.values()),
            "popupTotal": sum(u.get("ads_watched", {}).get("popupTotal", 0) for u in filtered.values()),
            "inAppToday": sum(u.get("ads_watched", {}).get("inAppToday", 0) for u in filtered.values()),
            "inAppTotal": sum(u.get("ads_watched", {}).get("inAppTotal", 0) for u in filtered.values())
        },
        "adsWatchedTotal": sum(u.get("adsWatchedTotal", 0) for u in filtered.values())
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
