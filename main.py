import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputStream, InputAudioStream, InputVideoStream
from pytgcalls.exceptions import GroupCallNotFound

# Load environment variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
APPROVED_GROUPS = [int(gid.strip()) for gid in os.getenv("APPROVED_GROUPS", "").split(",")]

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
pytgcalls = PyTgCalls(app)

# Track currently playing
current_calls = {}

@app.on_message(filters.command("displaygroupid") & filters.user(filters.usernames(["me"])))
async def display_group_id(client, message):
    # Shows group IDs for admin purposes
    chat = message.chat
    await message.reply_text(f"Group ID: `{chat.id}`", parse_mode="markdown")

@app.on_message(filters.command("play") & filters.chat(APPROVED_GROUPS))
async def play_media(client, message):
    """Play replied media in VC"""
    if not message.reply_to_message or not message.reply_to_message.media:
        await message.reply_text("Reply to a media file (audio/video) to play it in VC.")
        return

    chat_id = message.chat.id

    # Join VC if not already joined
    if chat_id not in current_calls:
        try:
            await pytgcalls.join_group_call(
                chat_id,
                InputStream(
                    InputAudioStream("input.raw")  # placeholder, will replace with ffmpeg pipe
                ),
            )
            current_calls[chat_id] = True
        except GroupCallNotFound:
            await message.reply_text("No active VC found. Please start one first.")
            return

    # Download media to temp file in memory (no permanent storage)
    file_path = await app.download_media(message.reply_to_message)
    if file_path.endswith((".mp4", ".mkv", ".webm")):
        input_stream = InputStream(InputVideoStream(file_path))
    else:
        input_stream = InputStream(InputAudioStream(file_path))

    await pytgcalls.change_stream(chat_id, input_stream)
    await message.reply_text(f"Streaming `{os.path.basename(file_path)}` in VC")

@app.on_message(filters.command("stop") & filters.chat(APPROVED_GROUPS))
async def stop_media(client, message):
    chat_id = message.chat.id
    if chat_id in current_calls:
        await pytgcalls.leave_group_call(chat_id)
        current_calls.pop(chat_id, None)
        await message.reply_text("Stopped streaming and left VC.")
    else:
        await message.reply_text("Not streaming anything in this VC.")

# Auto-start PyTgCalls
async def main():
    await app.start()
    await pytgcalls.start()
    print("Bot is online...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())