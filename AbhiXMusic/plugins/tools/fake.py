import requests
from pyrogram import filters
from AbhiXMusic import app

@app.on_message(filters.command(["FAKE", "fake"]))
async def fkadress(_, message):
    try:
        # Split the command and get the country name (if provided)
        query = message.text.split(maxsplit=1)[1].strip() if len(message.text.split()) > 1 else None
        if not query:
            await message.reply_text("Please provide a country name, e.g., /fake india")
            return

        url = f"https://randomuser.me/api/?nat={query}"
        response = requests.get(url)
        data = response.json()

        if "results" in data:
            fk = data["results"][0]

            name = f"{fk['name']['title']} {fk['name']['first']} {fk['name']['last']}"
            address = f"{fk['location']['street']['number']} {fk['location']['street']['name']}"
            city = fk["location"]["city"]
            state = fk["location"]["state"]
            country = fk["location"]["country"]
            postal = fk["location"]["postcode"]
            email = fk["email"]
            phone = fk["phone"]
            picture = fk["picture"]["large"]
            gender = fk["gender"]

            fkinfo = f"""
**ɴᴀᴍᴇ** ⇢ `{name}`
**ɢᴇɴᴅᴇʀ** ⇢ `{gender}`
**ᴀᴅᴅʀᴇss** ⇢ `{address}`
**ᴄᴏᴜɴᴛʀʏ** ⇢ `{country}`
**ᴄɪᴛʏ** ⇢ `{city}`
**ɢᴇɴᴅᴇʀ** ⇢ `{gender}`
**sᴛᴀᴛᴇ** ⇢ `{state}`
**ᴘᴏsᴛᴀʟ** ⇢ `{postal}`
**ᴇᴍᴀɪʟ** ⇢ `{email}`
**ᴘʜᴏɴᴇ** ⇢ `{phone}`
"""

            await message.reply_photo(photo=picture, caption=fkinfo)
        else:
            await message.reply_text("ᴏᴏᴘs ɴᴏᴛ ғᴏᴜɴᴅ ᴀɴʏ ᴀᴅᴅʀᴇss.\nᴛʀʏ ᴀɴᴏᴛʜᴇʀ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ.")
    except Exception as e:
        await message.reply_text(f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ: {str(e)}")

__MODULE__ = "Fᴀᴋᴇ"
__HELP__ = """

/fake [ᴄᴏᴜɴᴛʀʏ ɴᴀᴍᴇ ] - ᴛᴏ ɢᴇᴛ ʀᴀɴᴅᴏᴍ ᴀᴅᴅʀᴇss"""