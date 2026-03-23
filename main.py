import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputAudioStream, InputVideoStream
from pytgcalls.types.input_stream.quality import HighQualityAudio
import imageio_ffmpeg as ffmpeg

# --- Env vars ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
APPROVED_GROUPS = os.environ.get("APPROVED_GROUPS", "")  # comma-separated

approved_group_ids = [int(x) for x in APPROVED_GROUPS.split(",") if x.strip()]

# --- Pyrogram + PyTgCalls clients ---
app = Client("vplay_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
pytgcalls = PyTgCalls(app)

# --- Helper ---
def is_approved_group(chat_id: int) -> bool:
    return chat_id in approved_group_ids

# --- /displaygroupid (admin-only) ---
@app.on_message(filters.command("displaygroupid") & filters.group)
async def display_group_id(client: Client, message: Message):
    if not message.from_user or not message.from_user.is_admin:
        await message.reply_text("Only group admins can use this.")
        return
    await message.reply_text(f"Group ID: `{message.chat.id}`", quote=True)

# --- /play handler ---
@app.on_message(filters.command("play") & filters.reply & filters.group)
async def play_media(client: Client, message: Message):
    chat_id = message.chat.id
    if not is_approved_group(chat_id):
        await message.reply_text("This group is not approved for /play.")
        return

    replied_msg = message.reply_to_message
    if not (replied_msg.audio or replied_msg.voice or replied_msg.video):
        await message.reply_text("Reply must be to an audio/video message.")
        return

    # Determine stream type
    if replied_msg.audio or replied_msg.voice:
        stream = InputAudioStream(
            replied_msg.file_id,
            quality=HighQualityAudio()
        )
    else:
        stream = InputVideoStream(replied_msg.file_id)

    # Inline controls
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏯ Pause/Resume", callback_data=f"pause_{chat_id}"),
                InlineKeyboardButton("⏹ Stop", callback_data=f"stop_{chat_id}")
            ]
        ]
    )
    await message.reply_text("Starting playback...", reply_markup=buttons)

    # Join VC / start group call
    try:
        await pytgcalls.join_group_call(chat_id, stream)
    except Exception as e:
        await message.reply_text(f"Error joining VC: {e}")
        return

# --- Button callbacks ---
@app.on_callback_query()
async def button_cb(client, callback_query):
    data = callback_query.data
    chat_id = int(data.split("_")[1])
    action = data.split("_")[0]

    if action == "pause":
        try:
            await pytgcalls.pause_stream(chat_id)
        except:
            await pytgcalls.resume_stream(chat_id)
        await callback_query.answer("Toggled pause/resume")
    elif action == "stop":
        try:
            await pytgcalls.leave_group_call(chat_id)
            await callback_query.message.edit_text("Playback stopped.")
        except:
            await callback_query.answer("Failed to stop.")

# --- Run bot ---
async def main():
    await app.start()
    await pytgcalls.start()
    print("Bot is running...")
    await asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    asyncio.run(main())