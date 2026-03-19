import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputAudioStream, InputVideoStream
import imageio_ffmpeg as ffmpeg  # ensures FFmpeg is available

# force rebuild at 2026-03-19

# --- Environment variables ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
APPROVED_GROUPS = os.environ.get("APPROVED_GROUPS", "")  # comma-separated IDs

approved_group_ids = [int(x) for x in APPROVED_GROUPS.split(",") if x.strip()]

# --- Pyrogram client ---
app = Client("vplay_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- PyTgCalls client ---
pytgcalls = PyTgCalls(app)

# --- Helper to validate approved groups ---
def is_approved_group(chat_id: int) -> bool:
    return chat_id in approved_group_ids

# --- /vplay command handler ---
@app.on_message(filters.command("vplay") & filters.reply & filters.group)
async def vplay_handler(client: Client, message: Message):
    chat_id = message.chat.id
    if not is_approved_group(chat_id):
        await message.reply_text("This group is not approved for /vplay.")
        return

    # Parse repeat count
    try:
        times = int(message.command[1])
        if times < 1:
            times = 1
    except (IndexError, ValueError):
        times = 1  # default repeat once

    replied_msg = message.reply_to_message
    if not (replied_msg.audio or replied_msg.video or replied_msg.voice):
        await message.reply_text("Reply must be to an audio/video message.")
        return

    # Get the file
    file_path = await replied_msg.download(file_name="temp_media")
    await message.reply_text(f"Playing {replied_msg.file_name or 'media'} {times} time(s)...")

    # Start/ensure voice/video chat is active
    # This example assumes you are already in a group call

    for _ in range(times):
        if replied_msg.audio or replied_msg.voice:
            stream = InputAudioStream(file_path)
        else:
            stream = InputVideoStream(file_path)

        try:
            await pytgcalls.join_group_call(chat_id, stream)
            await asyncio.sleep(replied_msg.audio.duration if replied_msg.audio else 5)
            await pytgcalls.leave_group_call(chat_id)
        except Exception as e:
            await message.reply_text(f"Playback error: {e}")
            break

    os.remove(file_path)

# --- Run bot ---
async def main():
    await app.start()
    await pytgcalls.start()
    print("Bot is up and running.")
    await asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    asyncio.run(main())