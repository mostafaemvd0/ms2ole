from flask import Flask, render_template, request, session, redirect, jsonify
import discord
import asyncio
import os
import json
import threading

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "xK9mP2qL8nR4vT6w")

DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "Mo6en123@")
GUILD_ID = int(os.environ.get("GUILD_ID", "1193839352837591050"))

RANKS = [
    1289301033914335326, 1289301032807170181, 1289301031855067146,
    1289301030936379508, 1289301029875224666, 1289301028356882578,
    1289301027459305603, 1289301026477838419, 1289301025500692640,
    1289301024447795210, 1289301023176917197, 1289301022036066378,
    1289301019913748571, 1289301017824989244, 1289301015337897995,
]

RANK_NAMES = [
    "جندي", "جندي اول", "عريف", "وكيل رقيب", "رقيب",
    "رقيب اول", "رئيس رقباء", "ملازم", "ملازم اول", "نقيب",
    "رائد", "مقدم", "عقيد", "عميد", "لواء"
]

watched_members = {}
try:
    with open("members.json", "r") as f:
        watched_members = json.load(f)
except:
    pass

def save_members():
    with open("members.json", "w") as f:
        json.dump(watched_members, f)

intents = discord.Intents.all()
bot = discord.Client(intents=intents)
loop = asyncio.new_event_loop()

def run_bot():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot.start(os.environ.get("DISCORD_TOKEN")))

threading.Thread(target=run_bot, daemon=True).start()

def run_async(coro):
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    try:
        return future.result(timeout=30)
    except Exception as e:
        print(f"Error: {e}")
        raise

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == DASHBOARD_PASSWORD:
            session["logged_in"] = True
            return redirect("/dashboard")
        return render_template("login.html", error="كلمة السر غلط!")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect("/")
    return render_template("dashboard.html", ranks=RANK_NAMES, members=watched_members)

@app.route("/send_message", methods=["POST"])
def send_message():
    if not session.get("logged_in"):
        return jsonify({"error": "غير مصرح"}), 401
    data = request.json
    channel_id = int(data.get("channel_id"))
    message = data.get("message")
    async def _send():
        await bot.wait_until_ready()
        channel = bot.get_channel(channel_id)
        if not channel:
            channel = await bot.fetch_channel(channel_id)
        await channel.send(message)
    try:
        run_async(_send())
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/promote", methods=["POST"])
def promote():
    if not session.get("logged_in"):
        return jsonify({"error": "غير مصرح"}), 401
    data = request.json
    member_id = int(data.get("member_id"))
    async def _promote():
        await bot.wait_until_ready()
        guild = await bot.fetch_guild(GUILD_ID)
        member = await guild.fetch_member(member_id)
        current_rank_index = -1
        for i, rank_id in enumerate(RANKS):
            if any(r.id == rank_id for r in member.roles):
                current_rank_index = i
        if current_rank_index == -1:
            return {"error": "مش عنده رتبة"}
        if current_rank_index >= len(RANKS) - 1:
            return {"error": "وصل لأعلى رتبة"}
        old_role = guild.get_role(RANKS[current_rank_index])
        new_role = guild.get_role(RANKS[current_rank_index + 1])
        await member.remove_roles(old_role)
        await member.add_roles(new_role)
        return {
            "success": True,
            "old_rank": RANK_NAMES[current_rank_index],
            "new_rank": RANK_NAMES[current_rank_index + 1],
            "member": member.display_name
        }
    try:
        result = run_async(_promote())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/give_role", methods=["POST"])
def give_role():
    if not session.get("logged_in"):
        return jsonify({"error": "غير مصرح"}), 401
    data = request.json
    member_ids = data.get("member_ids", [])
    rank_index = int(data.get("rank_index"))
    async def _give():
        await bot.wait_until_ready()
        guild = await bot.fetch_guild(GUILD_ID)
        new_role = guild.get_role(RANKS[rank_index])
        results = []
        for mid in member_ids:
            try:
                member = await guild.fetch_member(int(mid))
                for rank_id in RANKS:
                    old_role = guild.get_role(rank_id)
                    if old_role in member.roles:
                        await member.remove_roles(old_role)
                await member.add_roles(new_role)
                results.append({"id": mid, "name": member.display_name, "success": True})
            except Exception as e:
                results.append({"id": mid, "error": str(e)})
        return results
    try:
        res = run_async(_give())
        return jsonify({"results": res})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/add_member", methods=["POST"])
def add_member():
    if not session.get("logged_in"):
        return jsonify({"error": "غير مصرح"}), 401
    data = request.json
    member_id = str(data.get("member_id"))
    name = data.get("name", member_id)
    watched_members[member_id] = {"name": name}
    save_members()
    return jsonify({"success": True})

@app.route("/remove_member", methods=["POST"])
def remove_member():
    if not session.get("logged_in"):
        return jsonify({"error": "غير مصرح"}), 401
    data = request.json
    member_id = str(data.get("member_id"))
    watched_members.pop(member_id, None)
    save_members()
    return jsonify({"success": True})

@bot.event
async def on_member_remove(member):
    from datetime import datetime
    LEAVE_CHANNEL_ID = int(os.environ.get("LEAVE_CHANNEL_ID", "1496300944550395925"))
    
    if str(member.id) not in watched_members:
        return
    
    channel = bot.get_channel(LEAVE_CHANNEL_ID)
    if not channel:
        channel = await bot.fetch_channel(LEAVE_CHANNEL_ID)
    
    rank_name = "بدون رتبة"
    for i, rank_id in enumerate(RANKS):
        if any(r.id == rank_id for r in member.roles):
            rank_name = RANK_NAMES[i]
    
    await channel.send(
        f"🚨 **عضو غادر السيرفر**\n"
        f"👤 {member.name}\n"
        f"🆔 {member.id}\n"
        f"⭐ الرتبة: {rank_name}\n"
        f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
