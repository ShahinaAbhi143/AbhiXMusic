from pyrogram import filters
from pyrogram.types import Message
from AbhiXMusic import app
from config import BANNED_USERS

# Temporary in-memory storage for filters (if database functions are not available)
FILTERS = {}

# Helper functions (in case database functions are not available)
async def add_filter(keyword: str, response: str):
    """Add a filter to the in-memory storage."""
    FILTERS[keyword.lower()] = response

async def delete_filter(keyword: str):
    """Delete a filter from the in-memory storage."""
    keyword = keyword.lower()
    if keyword in FILTERS:
        del FILTERS[keyword]

async def get_filter(keyword: str) -> str | None:
    """Get a filter response from the in-memory storage."""
    return FILTERS.get(keyword.lower())

async def get_all_filters() -> list:
    """Get all filters from the in-memory storage."""
    return list(FILTERS.keys())

@app.on_message(filters.command("addfilter") & ~BANNED_USERS)
async def addfilter_command(_, message: Message):
    """Add a new filter with a keyword and response."""
    try:
        if len(message.command) < 3:
            await message.reply("Usage: /addfilter <keyword> <response>")
            return

        keyword = message.command[1]
        response = " ".join(message.command[2:])
        
        await add_filter(keyword, response)
        await message.reply(f"Filter `{keyword}` added successfully!")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

@app.on_message(filters.command("delfilter") & ~BANNED_USERS)
async def delfilter_command(_, message: Message):
    """Delete an existing filter by keyword."""
    try:
        if len(message.command) < 2:
            await message.reply("Usage: /delfilter <keyword>")
            return

        keyword = message.command[1]
        await delete_filter(keyword)
        await message.reply(f"Filter `{keyword}` deleted successfully!")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

@app.on_message(filters.command("listfilters") & ~BANNED_USERS)
async def listfilters_command(_, message: Message):
    """List all existing filters."""
    try:
        all_filters = await get_all_filters()
        if not all_filters:
            await message.reply("No filters found!")
            return

        filter_list = "\n".join([f"• {f}" for f in all_filters])
        await message.reply(f"**Filters:**\n{filter_list}")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

@app.on_message(~filters.command(["addfilter", "delfilter", "listfilters"]) & ~BANNED_USERS)
async def apply_filter(_, message: Message):
    """Apply a filter if a keyword matches the message."""
    try:
        if not message.text:
            return

        text = message.text.lower()
        response = await get_filter(text)
        if response:
            await message.reply(response)
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

__MODULE__ = "Filters"
__HELP__ = """
**Filters**

• /addfilter <keyword> <response> - Adds a filter that replies with the response when the keyword is mentioned.
• /delfilter <keyword> - Deletes a filter.
• /listfilters - Lists all active filters.
"""
