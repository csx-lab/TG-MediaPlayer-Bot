import os
import asyncio
from pyrogram import Client, filters
from pytgcalls import PyTgCalls, idle
from pytgcalls.types import Update
from pytgcalls.types.input_stream import InputStream, InputAudioStream, InputVideoStream

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
APPROVED_GROUPS = os.getenv("APPROVED_GROUPS", "")
APPROVED_GROUPS = [int(g.strip()) for g in APPROVED_GROUPS.split(",") if g.strip()]

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
pytgcalls = PyTgCalls(app)

# Keep track of currently playing media per chat
playing_media = {}

@app.on_message(filters.command("displaygroupid") & filters.user(BOT_TOKEN) | filters.user("me"))
async def display_group_id(client, message):
    # Just for admin: show group IDs
    chat = message.chat
    await message.reply_text(f"Group ID: {chat.id}")

@app.on_message(filters.command("play") & filters.chat(APPROVED_GROUPS))
async def play_media(client, message):
    if not message.reply_to_message:
        await message.reply_text("Reply to a message containing media to play.")
        return

    media = message.reply_to_message
    chat_id = message.chat.id

    # Determine media type
    if media.audio or media.document or media.video:
        file_path = await media.download()
    else:
        await message.reply_text("Unsupported media type.")
        return

    # Stop currently playing if any
    if chat_id in playing_media:
        await pytgcalls.leave_group_call(chat_id)
        del playing_media[chat_id]

    # Play media in VC
    input_stream = InputStream(
        InputAudioStream(file_path)
    )

    await pytgcalls.join_group_call(chat_id, input_stream)
    playing_media[chat_id] = file_path
    await message.reply_text(f"Now playing your media in VC!")

@app.on_message(filters.command("stop") & filters.chat(APPROVED_GROUPS))
async def stop_media(client, message):
    chat_id = message.chat.id
    if chat_id in playing_media:
        await pytgcalls.leave_group_call(chat_id)
        del playing_media[chat_id]
        await message.reply_text("Stopped playback.")
    else:
        await message.reply_text("Nothing is playing.")

async def main():
    await app.start()
    await pytgcalls.start()
    print("Bot started with PyTgCalls")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())