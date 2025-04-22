from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio

API_ID = 123456  # your API ID
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"

TARGET_CHAT_ID = -1001234567890
SOURCE_CHAT_IDS = [
    -1001111111111,
    -1002222222222,
]

# Set to store unique file IDs of already forwarded media
forwarded_media_ids = set()

app = Client("AutoForwardBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def get_file_unique_id(message: Message):
    if message.photo:
        return message.photo.file_unique_id
    elif message.video:
        return message.video.file_unique_id
    elif message.document:
        return message.document.file_unique_id
    elif message.animation:
        return message.animation.file_unique_id
    elif message.audio:
        return message.audio.file_unique_id
    elif message.voice:
        return message.voice.file_unique_id
    return None

async def forward_if_unique(message: Message):
    media_id = get_file_unique_id(message)
    if media_id and media_id in forwarded_media_ids:
        print(f"🛑 Duplicate media skipped (ID: {media_id})")
        return
    try:
        await message.forward(TARGET_CHAT_ID)
        print(f"📨 Forwarded: {message.chat.id} -> {TARGET_CHAT_ID}")
        if media_id:
            forwarded_media_ids.add(media_id)
    except Exception as e:
        print(f"❌ Error forwarding message: {e}")

@app.on_message(filters.chat(SOURCE_CHAT_IDS))
async def forward_new_messages(client: Client, message: Message):
    await forward_if_unique(message)

async def forward_existing_messages():
    print("📦 Forwarding old messages...")
    for chat_id in SOURCE_CHAT_IDS:
        try:
            async for msg in app.get_chat_history(chat_id, reverse=True):
                await forward_if_unique(msg)
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Error reading chat {chat_id}: {e}")
    print("✅ Done with old messages. Listening for new ones...")

from pyrogram.idle import idle

async def main():
    await app.start()
    await forward_existing_messages()
    await idle()
    await app.stop()

app.run(main())
