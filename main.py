import os
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import InputAudioStream
import yt_dlp

# --- ENV ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
APPROVED_GROUPS = os.environ.get("APPROVED_GROUPS", "")

approved_group_ids = [int(x) for x in APPROVED_GROUPS.split(",") if x.strip()]

# --- CLIENTS ---
app = Client("vplay_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
pytgcalls = PyTgCalls(app)

# --- QUEUE ---
queues = {}  # {chat_id: [file_path, file_path, ...]}


# =========================
# HELPERS
# =========================
def is_approved(chat_id):
    return chat_id in approved_group_ids


def add_to_queue(chat_id, file):
    queues.setdefault(chat_id, []).append(file)


def pop_queue(chat_id):
    if queues.get(chat_id):
        return queues[chat_id].pop(0)


async def ensure_call(chat_id):
    """Join or start VC"""
    try:
        await pytgcalls.join_group_call(chat_id, InputAudioStream("silence.mp3"))
    except:
        try:
            await app.invoke(
                # starts voice chat
                raw.functions.phone.CreateGroupCall(
                    peer=await app.resolve_peer(chat_id),
                    random_id=app.rnd_id()
                )
            )
        except:
            pass


async def play_next(chat_id):
    file = pop_queue(chat_id)
    if not file:
        await pytgcalls.leave_group_call(chat_id)
        return

    stream = InputAudioStream(file)
    await pytgcalls.join_group_call(chat_id, stream)


# =========================
# DISPLAY GROUP ID
# =========================
@app.on_message(filters.command("displaygroupid"))
async def display_group_id(client, message):
    chat_id = message.chat.id

    if message.chat.type in ["group", "supergroup"]:
        member = await client.get_chat_member(chat_id, message.from_user.id)
        if member.status not in ("administrator", "creator"):
            return await message.reply_text("Admins only.")

    await message.reply_text(f"`{chat_id}`")


# =========================
# PLAY (YOUTUBE)
# =========================
@app.on_message(filters.command("play") & filters.group)
async def play(client: Client, message: Message):
    chat_id = message.chat.id

    if not is_approved(chat_id):
        return await message.reply_text("Not approved.")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /play song name")

    query = " ".join(message.command[1:])

    msg = await message.reply_text("Searching...")

    ydl_opts = {
        "format": "bestaudio",
        "quiet": True,
        "outtmpl": "yt_%(id)s.%(ext)s"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)["entries"][0]
            file = ydl.prepare_filename(info)

        add_to_queue(chat_id, file)

        await msg.edit(f"Added to queue:\n{info['title']}")

        if len(queues[chat_id]) == 1:
            await play_next(chat_id)

    except Exception as e:
        await msg.edit(f"Error:\n{e}")


# =========================
# VPLAY (REPLY MEDIA)
# =========================
@app.on_message(filters.command("vplay") & filters.reply & filters.group)
async def vplay(client, message):
    chat_id = message.chat.id

    if not is_approved(chat_id):
        return await message.reply_text("Not approved.")

    replied = message.reply_to_message

    if not (replied.audio or replied.voice or replied.video):
        return await message.reply_text("Reply to media.")

    file = await replied.download()

    add_to_queue(chat_id, file)

    await message.reply_text("Added to queue")

    if len(queues[chat_id]) == 1:
        await play_next(chat_id)


# =========================
# SKIP
# =========================
@app.on_message(filters.command("skip") & filters.group)
async def skip(_, message):
    chat_id = message.chat.id

    if queues.get(chat_id):
        await play_next(chat_id)
        await message.reply_text("Skipped.")
    else:
        await message.reply_text("Queue empty.")


# =========================
# STOP
# =========================
@app.on_message(filters.command("stop") & filters.group)
async def stop(_, message):
    chat_id = message.chat.id

    queues[chat_id] = []
    await pytgcalls.leave_group_call(chat_id)

    await message.reply_text("Stopped.")


# =========================
# MAIN
# =========================
async def main():
    await app.start()
    await pytgcalls.start()
    print("Bot running")
    await idle()


if __name__ == "__main__":
    asyncio.run(main())