from telethon import TelegramClient
import json
import asyncio

# ==== ENTER YOUR DETAILS HERE ====
api_id =                   # 👉 Your Telegram API ID (get it from https://my.telegram.org/apps)
api_hash = ""  # 👉 Your API Hash
channel_username = "Ignore_and_enjoy" 

# Output file
output_file = "telegram_channel_data.json"


async def main():
    client = TelegramClient("session_name", api_id, api_hash)
    await client.start()

    # Get channel entity
    channel = await client.get_entity(channel_username)

    # Collect channel metadata
    data = {
        "channel_name": channel.title,
        "channel_description": getattr(channel, "about", ""),
        "messages": []
    }

    # Iterate all messages
    async for msg in client.iter_messages(channel, reverse=True):
        message_data = {
            "Message ID": msg.id,
            "Text": msg.text or "",
            "Date & Time": msg.date.strftime("%Y-%m-%d %H:%M:%S") if msg.date else None,
            "Edit Date": msg.edit_date.strftime("%Y-%m-%d %H:%M:%S") if msg.edit_date else None,
            # Channel-specific stats
            "Views": msg.views,
            "Reactions": [r.reaction.emoticon for r in msg.reactions.results] if msg.reactions else [],

            "Pinned?": msg.pinned
        }

        data["messages"].append(message_data)

    # Save to JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"✅ Data saved to {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
