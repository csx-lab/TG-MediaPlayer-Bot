import os
import asyncio
from pyrogram import Client, filters
from pytgcalls import PyTgCalls, idle
from pytgcalls.types.input_stream import InputAudioStream, InputVideoStream, InputStream

# --- CONFIG FROM ENV VARS ---
API_ID = int(os.getenv("API_ID", "123456"))           # your Telegram API ID
API_HASH = os.getenv("API_HASH", "your_api_hash")     # your Telegram API Hash
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")  # bot token
# Comma-separated list of allowed group chat IDs
APPROVED_GROUPS = [int(x) for x in os.getenv("APPROVED_GROUPS", "-1001234567890").split(",")]

# --- CREATE CLIENTS ---
app = Client("video_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
pytgcalls = PyTgCalls(app)

# --- PLAY FUNCTION ---
async def play_media(chat_id, file_id, repeat=-1, is_video=True):
    """
    Play the given media file in VC.
    repeat = -1 -> infinite
    """
    # Join VC
    await pytgcalls.join_group_call(
        chat_id,
        InputStream(
            InputAudioStream(file_id),
            InputVideoStream(file_id) if is_video else None
        ),
        stream_type="video"
    )

    count = 0
    while repeat == -1 or count < repeat:
        count += 1
        print(f"Playing media: iteration {count}")
        # naive sleep: adjust according to media duration
        await asyncio.sleep(5)  # You can replace with actual duration

    # Leave VC after done
    await pytgcalls.leave_group_call(chat_id)

# --- COMMAND HANDLER ---
@app.on_message(filters.command("vplay") & filters.reply)
async def vplay(client, message):
    # Check if chat is approved
    if message.chat.id not in APPROVED_GROUPS:
        await message.reply_text("⚠️ This bot is not allowed in this group.")
        print(f"Unauthorized /vplay attempt in chat {message.chat.id} by {message.from_user.id}")
        return

    reply = message.reply_to_message
    if not reply:
        await message.reply_text("⚠️ Reply to a message containing audio/video.")
        return

    # Extract repeat count
    try:
        repeat = int(message.command[1])
    except (IndexError, ValueError):
        repeat = -1  # infinite by default

    # Determine file_id
    file_id = None
    is_video = False
    if reply.audio:
        file_id = reply.audio.file_id
    elif reply.video:
        file_id = reply.video.file_id
        is_video = True
    elif reply.document:
        file_id = reply.document.file_id
        is_video = True
    else:
        await message.reply_text("⚠️ The replied message does not contain audio/video.")
        return

    await message.reply_text(f"▶️ Playing media {('∞ times' if repeat==-1 else f'{repeat} times')}...")
    asyncio.create_task(play_media(message.chat.id, file_id, repeat, is_video))

# --- START BOT ---
async def main():
    await app.start()
    await pytgcalls.start()
    print(f"Bot running. Approved groups: {APPROVED_GROUPS}")
    await idle()  # Keep the bot alive
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())