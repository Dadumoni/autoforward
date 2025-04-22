import os
import json
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, ChatInviteLink

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

DATA_FILE = "data.json"
forwarded_media_ids = set()

app = Client("AutoForwardBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Load config
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"target_chat_id": None, "source_chat_ids": []}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_file_unique_id(msg: Message):
    media = msg.photo or msg.video or msg.document or msg.audio or msg.animation or msg.voice
    return media.file_unique_id if media else None

async def forward_if_unique(msg: Message):
    data = load_data()
    media_id = get_file_unique_id(msg)
    if media_id and media_id in forwarded_media_ids:
        return
    try:
        await msg.forward(data["target_chat_id"])
        if media_id:
            forwarded_media_ids.add(media_id)
    except Exception as e:
        print(f"Error forwarding: {e}")
        if "CHAT_WRITE_FORBIDDEN" in str(e):
            print("⚠️ Target channel access denied.")

# Handle new messages from all sources
@app.on_message(filters.all)
async def forward_handler(client, msg):
    data = load_data()
    if msg.chat.id in data["source_chat_ids"]:
        await forward_if_unique(msg)

# Command: Set target chat
@app.on_message(filters.command("set_target") & filters.private)
async def set_target_handler(client, msg: Message):
    if len(msg.command) < 2:
        return await msg.reply("Usage: /set_target <invite_link>")

    link = msg.command[1]
    try:
        chat = await client.join_chat(link)
        data = load_data()
        data["target_chat_id"] = chat.id
        save_data(data)
        await msg.reply(f"✅ Target channel set: `{chat.title}` (`{chat.id}`)")
    except Exception as e:
        await msg.reply(f"❌ Failed to join: {e}")

# Command: Add source channel
@app.on_message(filters.command("add_source") & filters.private)
async def add_source_handler(client, msg: Message):
    if len(msg.command) < 2:
        return await msg.reply("Usage: /add_source <invite_link>")
    link = msg.command[1]
    try:
        chat = await client.join_chat(link)
        data = load_data()
        if chat.id not in data["source_chat_ids"]:
            data["source_chat_ids"].append(chat.id)
            save_data(data)
            await msg.reply(f"✅ Added source: `{chat.title}` (`{chat.id}`)")
        else:
            await msg.reply("ℹ️ Source already added.")
    except Exception as e:
        await msg.reply(f"❌ Failed to join: {e}")

# Command: Remove source
@app.on_message(filters.command("remove_source") & filters.private)
async def remove_source_handler(client, msg: Message):
    if len(msg.command) < 2:
        return await msg.reply("Usage: /remove_source <chat_id>")
    try:
        cid = int(msg.command[1])
        data = load_data()
        if cid in data["source_chat_ids"]:
            data["source_chat_ids"].remove(cid)
            save_data(data)
            await msg.reply(f"✅ Removed source `{cid}`.")
        else:
            await msg.reply("Source not found.")
    except ValueError:
        await msg.reply("Invalid chat ID.")

# Command: List sources
@app.on_message(filters.command("list_sources") & filters.private)
async def list_sources_handler(client, msg: Message):
    data = load_data()
    lines = []
    for cid in data["source_chat_ids"]:
        try:
            chat = await client.get_chat(cid)
            lines.append(f"• {chat.title} (`{cid}`)")
        except:
            lines.append(f"• [❌ Unavailable] (`{cid}`)")
    if not lines:
        await msg.reply("No sources added.")
    else:
        await msg.reply("📡 Source Channels:\n" + "\n".join(lines))

# Auto-remove deleted/banned sources on error
@app.on_message(filters.all)
async def check_source_validity(client, msg):
    data = load_data()
    if msg.chat.id in data["source_chat_ids"]:
        try:
            await client.get_chat(msg.chat.id)
        except:
            data["source_chat_ids"].remove(msg.chat.id)
            save_data(data)
            print(f"❌ Source removed (no longer exists): {msg.chat.id}")

app.run()
