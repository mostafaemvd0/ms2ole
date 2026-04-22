import discord
import os
import json
from datetime import datetime

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

GUILD_ID = int(os.environ.get("GUILD_ID", "1193839352837591050"))
LEAVE_CHANNEL_ID = int(os.environ.get("LEAVE_CHANNEL_ID", "1496300944550395925"))

RANKS = [
    1289301033914335326,  # جندي
    1289301032807170181,  # جندي اول
    1289301031855067146,  # عريف
    1289301030936379508,  # وكيل رقيب
    1289301029875224666,  # رقيب
    1289301028356882578,  # رقيب اول
    1289301027459305603,  # رئيس رقباء
    1289301026477838419,  # ملازم
    1289301025500692640,  # ملازم اول
    1289301024447795210,  # نقيب
    1289301023176917197,  # رائد
    1289301022036066378,  # مقدم
    1289301019913748571,  # عقيد
    1289301017824989244,  # عميد
    1289301015337897995,  # لواء
]

RANK_NAMES = [
    "جندي", "جندي اول", "عريف", "وكيل رقيب", "رقيب",
    "رقيب اول", "رئيس رقباء", "ملازم", "ملازم اول", "نقيب",
    "رائد", "مقدم", "عقيد", "عميد", "لواء"
]

@client.event
async def on_ready():
    await tree.sync()
    print(f"البوت شغال: {client.user}")

@client.event
async def on_member_remove(member):
    channel = client.get_channel(LEAVE_CHANNEL_ID)
    if channel:
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

client.run(os.environ.get("DISCORD_TOKEN"))
