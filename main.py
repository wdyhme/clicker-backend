# This is the updated backend code (main.py)
# To be used with your frontend to ensure proper data saving, shop functionality, bonus handling, and leaderboard logic

from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os
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

def ensure_user_structure(user, username="anon"):
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
def index():
    return "✅ Clicker backend is working"

@app.route("/get_data")
def get_data():
    user_id = request.args.get("user_id")
    username = request.args.get("username", "anon")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    all_data = load_all()
    user = all_data.get(user_id, {})
    user = ensure_user_structure(user, username)
    all_data[user_id] = user
    save_all(all_data)

    return jsonify(user)

@app.route("/save_data", methods=["POST"])
def save_data():
    try:
        req = request.get_json(force=True, silent=True)
        if not req:
            print("❌ No JSON body received")
            return jsonify({"error": "Empty or invalid JSON"}), 400

        print("🔵 SAVE_DATA REQUEST:", req)

        user_id = req.get("user_id")
        data = req.get("data")

        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        if not isinstance(data, dict):
            return jsonify({"error": "Invalid data format"}), 400

        all_data = load_all()
        user = all_data.get(user_id, {})
        user = ensure_user_structure(user, data.get("nickname", "anon"))

        for key in [
            "balance", "perClick", "passiveIncome",
            "totalEarned", "totalClicks",
            "adsWatchedToday", "adsWatchedTotal",
            "daily_bonus_claimed"
        ]:
            if key in data:
                user[key] = data[key]

        user["upgrades"] = data.get("upgrades", {"click": 0, "passive": 0})
        user["ads_watched"] = data.get("ads_watched", user["ads_watched"])
        user["last_activity"] = datetime.utcnow().isoformat()

        all_data[user_id] = user
        save_all(all_data)

        print(f"✅ Saved user {user_id}")
        return jsonify({"success": True})

    except Exception as e:
        print("❌ ERROR in /save_data:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/get_top_players")
def get_top_players():
    all_data = load_all()
    sorted_users = sorted(all_data.items(), key=lambda x: x[1].get("totalEarned", 0), reverse=True)
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
    return jsonify({
        "totalEarned": sum(u.get("totalEarned", 0) for u in all_data.values()),
        "totalClicks": sum(u.get("totalClicks", 0) for u in all_data.values()),
        "clickUpgrades": sum(u.get("upgrades", {}).get("click", 0) for u in all_data.values()),
        "passiveUpgrades": sum(u.get("upgrades", {}).get("passive", 0) for u in all_data.values()),
        "users": len(all_data),
        "ads": {
            "interstitialToday": sum(u.get("ads_watched", {}).get("interstitialToday", 0) for u in all_data.values()),
            "interstitialTotal": sum(u.get("ads_watched", {}).get("interstitialTotal", 0) for u in all_data.values()),
            "popupToday": sum(u.get("ads_watched", {}).get("popupToday", 0) for u in all_data.values()),
            "popupTotal": sum(u.get("ads_watched", {}).get("popupTotal", 0) for u in all_data.values()),
            "inAppToday": sum(u.get("ads_watched", {}).get("inAppToday", 0) for u in all_data.values()),
            "inAppTotal": sum(u.get("ads_watched", {}).get("inAppTotal", 0) for u in all_data.values())
        },
        "adsWatchedTotal": sum(u.get("adsWatchedTotal", 0) for u in all_data.values())
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
