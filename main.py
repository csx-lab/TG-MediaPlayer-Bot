import os
import subprocess
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import Update
from pytgcalls.types.stream import StreamAudioEnded
from pytgcalls.types.input_stream import InputStream, InputAudioStream

# --- Node.js check ---
try:
    node_version = subprocess.check_output(["node", "-v"]).decode().strip()
    print(f"Node.js version detected: {node_version}")
except Exception as e:
    print("Node.js not found in PATH! Please install Node.js v15+.")
    raise e

# --- Continue with your bot initialization ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
APPROVED_GROUPS = os.environ.get("GROUP_ID", "").split(",")

app = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

pytgcalls = PyTgCalls(app)

# --- Example music queue (dict keyed by chat_id) ---
queues = {}

# --- Helper functions ---
def is_approved_group(chat_id: int) -> bool:
    return str(chat_id) in APPROVED_GROUPS

async def start_playback(chat_id: int, audio_file: str):
    """Start playing audio in a voice chat"""
    await pytgcalls.join_group_call(
        chat_id,
        InputStream(
            InputAudioStream(
                audio_file
            )
        )
    )

# --- Pyrogram Handlers ---

# Start command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    await message.reply_text("Hello! Music bot is online 🎵")

# Play command
@app.on_message(filters.command("play") & filters.group)
async def play_cmd(client: Client, message: Message):
    if not is_approved_group(message.chat.id):
        return await message.reply_text("❌ This group is not approved to use this bot.")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /play <audio file URL or path>")

    audio_file = message.command[1]
    chat_id = message.chat.id

    if chat_id not in queues:
        queues[chat_id] = []

    queues[chat_id].append(audio_file)
    await message.reply_text(f"Added to queue: {audio_file}")

    if len(queues[chat_id]) == 1:
        # Only play if first in queue
        await start_playback(chat_id, audio_file)

# PyTgCalls event: stream ended
@pytgcalls.on_stream_end()
async def on_stream_end(update: StreamAudioEnded):
    chat_id = update.chat_id
    if chat_id in queues and queues[chat_id]:
        queues[chat_id].pop(0)  # remove finished song
        if queues[chat_id]:
            # play next song
            await start_playback(chat_id, queues[chat_id][0])
        else:
            # leave VC if queue empty
            await pytgcalls.leave_group_call(chat_id)

# Optional: other command examples (skip, stop)
@app.on_message(filters.command("skip") & filters.group)
async def skip_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    if not is_approved_group(chat_id):
        return
    if chat_id in queues and queues[chat_id]:
        await pytgcalls.leave_group_call(chat_id)
        queues[chat_id].pop(0)
        if queues[chat_id]:
            await start_playback(chat_id, queues[chat_id][0])
        await message.reply_text("Skipped to next song.")

@app.on_message(filters.command("stop") & filters.group)
async def stop_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    if not is_approved_group(chat_id):
        return
    await pytgcalls.leave_group_call(chat_id)
    queues[chat_id] = []
    await message.reply_text("Stopped playback and cleared queue.")

# --- Asyncio-safe startup ---
async def main():
    # Start Pyrogram client
    await app.start()
    print("Pyrogram client started")

    # Start PyTgCalls
    await pytgcalls.start()
    print("PyTgCalls started")

    # Keep bot running
    try:
        await asyncio.Event().wait()
    finally:
        # Clean shutdown
        await pytgcalls.stop()
        await app.stop()
        print("Bot stopped gracefully")

if __name__ == "__main__":
    asyncio.run(main())