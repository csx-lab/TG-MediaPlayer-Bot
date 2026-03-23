import os
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types import InputAudioStream
from pytgcalls.exceptions import GroupCallNotFound
import yt_dlp

# --- ENV ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
APPROVED_GROUPS = os.environ.get("APPROVED_GROUPS", "")
approved_group_ids = [int(x) for x in APPROVED_GROUPS.split(",") if x.strip()]

# --- CLIENTS ---
app = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
pytgcalls = PyTgCalls(app)

# --- GLOBAL STATE (per group) ---
queues = {}       # chat_id -> list of tracks
playing = {}      # chat_id -> current track
locks = {}        # chat_id -> asyncio.Lock to avoid race conditions

# --- HELPERS ---
def is_approved(chat_id):
    return chat_id in approved_group_ids

def add_track(chat_id, track):
    queues.setdefault(chat_id, []).append(track)
    locks.setdefault(chat_id, asyncio.Lock())

def pop_track(chat_id):
    if queues.get(chat_id):
        return queues[chat_id].pop(0)
    return None

def player_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Skip", callback_data="skip"),
         InlineKeyboardButton("Stop", callback_data="stop")],
        [InlineKeyboardButton("Pause", callback_data="pause"),
         InlineKeyboardButton("Resume", callback_data="resume")],
        [InlineKeyboardButton("Queue", callback_data="queue")]
    ])

async def ensure_vc(chat_id, stream):
    try:
        await pytgcalls.join_group_call(chat_id, stream)
    except GroupCallNotFound:
        await pytgcalls.create_group_call(chat_id)
        await asyncio.sleep(2)
        await pytgcalls.join_group_call(chat_id, stream)

# =========================
# PLAY NEXT TRACK
# =========================
async def play_next(chat_id):
    async with locks[chat_id]:
        track = pop_track(chat_id)
        if not track:
            playing.pop(chat_id, None)
            try:
                await pytgcalls.leave_group_call(chat_id)
            except: pass
            return

        playing[chat_id] = track
        stream = InputAudioStream(track["url"])

        try:
            await ensure_vc(chat_id, stream)
        except Exception as e:
            print(f"Error joining VC for {chat_id}: {e}")
            queues.setdefault(chat_id, []).insert(0, track)
            playing.pop(chat_id, None)

# =========================
# DISPLAY GROUP ID (admin only)
# =========================
@app.on_message(filters.command("displaygroupid"))
async def display_group_id(client, message: Message):
    chat_id = message.chat.id
    try:
        if message.chat.type in ["group", "supergroup"]:
            member = await client.get_chat_member(chat_id, message.from_user.id)
            if member.status not in ("administrator", "creator"):
                return await message.reply_text("Admins only.")
        await message.reply_text(f"Group ID: {chat_id}")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

# =========================
# PLAY COMMAND (YouTube smart)
# =========================
@app.on_message(filters.command("play") & filters.group)
async def play_command(client, message: Message):
    chat_id = message.chat.id
    if not is_approved(chat_id):
        return await message.reply_text("This group is not approved.")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /play <song name or URL>")

    query = " ".join(message.command[1:])
    msg = await message.reply_text("Processing...")

    ydl_opts = {
        "format": "bestaudio",
        "quiet": True,
        "noplaylist": False,  # allow playlist
        "extract_flat": True,  # faster for playlists
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)

            # if it's a playlist, queue each entry
            if "entries" in info:
                for entry in info["entries"]:
                    url = entry["url"]
                    title = entry.get("title", "Unknown")
                    add_track(chat_id, {"title": title, "url": url, "type": "yt"})
                await msg.edit(f"Added playlist with {len(info['entries'])} tracks", reply_markup=player_buttons())
            else:
                url = info["url"]
                title = info.get("title", "Unknown")
                add_track(chat_id, {"title": title, "url": url, "type": "yt"})
                await msg.edit(f"Added to queue: {title}", reply_markup=player_buttons())

        # start playback if nothing is playing
        if chat_id not in playing:
            asyncio.create_task(play_next(chat_id))

    except Exception as e:
        await msg.edit(f"Error: {e}")
        
# =========================
# VPLAY COMMAND (local media reply)
# =========================
@app.on_message(filters.command("vplay") & filters.reply & filters.group)
async def vplay_command(client, message: Message):
    chat_id = message.chat.id
    if not is_approved(chat_id):
        return await message.reply_text("This group is not approved.")

    replied = message.reply_to_message
    if not (replied.audio or replied.voice):
        return await message.reply_text("Reply to audio/voice message.")

    file_path = await replied.download()
    add_track(chat_id, {"title": replied.file_name or "Media", "url": file_path, "type": "file"})
    await message.reply_text(f"Added to queue: {replied.file_name}", reply_markup=player_buttons())

    if chat_id not in playing:
        asyncio.create_task(play_next(chat_id))

# =========================
# CALLBACK BUTTONS
# =========================
@app.on_callback_query()
async def button_handler(client, callback_query):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    current = playing.get(chat_id)

    if data == "skip":
        asyncio.create_task(play_next(chat_id))
        await callback_query.answer("Skipped track")
    elif data == "stop":
        queues[chat_id] = []
        try: await pytgcalls.leave_group_call(chat_id)
        except: pass
        playing.pop(chat_id, None)
        await callback_query.answer("Stopped playback")
    elif data == "pause":
        if current:
            await pytgcalls.pause_stream(chat_id)
            await callback_query.answer("Paused")
    elif data == "resume":
        if current:
            await pytgcalls.resume_stream(chat_id)
            await callback_query.answer("Resumed")
    elif data == "queue":
        q_text = "\n".join([f"{i+1}. {t['title']}" for i, t in enumerate(queues.get(chat_id, []))])
        if not q_text:
            q_text = "Queue is empty."
        await callback_query.answer(q_text, show_alert=True)

# =========================
# TRACK-END EVENT
# =========================
@pytgcalls.on_stream_end()
async def on_stream_end(_, update):
    chat_id = update.chat_id
    asyncio.create_task(play_next(chat_id))

# =========================
# MAIN
# =========================
async def main():
    await app.start()
    await pytgcalls.start()
    print("Bot is running")
    idle()

if __name__ == "__main__":
    asyncio.run(main())