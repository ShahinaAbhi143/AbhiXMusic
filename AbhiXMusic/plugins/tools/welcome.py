import os
from PIL import ImageDraw, Image, ImageChops, ImageFont
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from logging import getLogger
from AbhiXMusic import app

LOGGER = getLogger(__name__)

# Ensure LOG_CHANNEL_ID is defined in your config
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID", None)

# Dictionary to store welcome settings for each chat (default is True)
welcome_settings = {}

class temp:
    ME = None
    CURRENT = 2
    CANCEL = False
    MELCOW = {}
    U_NAME = None
    B_NAME = None

def circle(pfp, size=(825, 824)):
    LOGGER.info(f"Creating circular image with size {size}")
    try:
        pfp = pfp.resize(size, Image.LANCZOS).convert("RGBA")
        bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
        mask = Image.new("L", bigsize, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + bigsize, fill=255)
        mask = mask.resize(pfp.size, Image.LANCZOS)
        mask = ImageChops.darker(mask, pfp.split()[-1])
        pfp.putalpha(mask)
        return pfp
    except Exception as e:
        LOGGER.error(f"Error in circle function: {str(e)}")
        raise

def welcomepic(pic, user, chatname, id, uname):
    LOGGER.info(f"Generating welcome image for user {user} (ID: {id}) in chat {chatname}")
    try:
        background_path = "AbhiXMusic/assets/AbhiWel.png"
        if not os.path.exists(background_path):
            LOGGER.error(f"Background image not found at {background_path}")
            raise FileNotFoundError(f"Background image not found at {background_path}")
        
        font_path = "AbhiXMusic/assets/font.ttf"
        if not os.path.exists(font_path):
            LOGGER.error(f"Font file not found at {font_path}")
            raise FileNotFoundError(f"Font file not found at {font_path}")

        background = Image.open(background_path)
        pfp = Image.open(pic).convert("RGBA")
        pfp = circle(pfp)
        pfp = pfp.resize((825, 824))
        draw = ImageDraw.Draw(background)
        font = ImageFont.truetype(font_path, size=110)
        draw.text((2100, 1420), f'ID: {id}', fill=(255, 255, 255), font=font)
        pfp_position = (1990, 435)
        background.paste(pfp, pfp_position, pfp)
        output_path = f"downloads/welcome#{id}.png"
        background.save(output_path)
        LOGGER.info(f"Welcome image saved at {output_path}")
        return output_path
    except Exception as e:
        LOGGER.error(f"Error in welcomepic function: {str(e)}")
        raise

async def get_last_seen_status(user):
    try:
        status = user.status
        if status == "online":
            return "Online"
        elif status == "offline":
            return "Offline"
        elif status == "recently":
            return "Recently"
        elif status == "within_week":
            return "Within a week"
        elif status == "within_month":
            return "Within a month"
        elif status == "long_time_ago":
            return "A long time ago"
        else:
            return "Unknown"
    except Exception as e:
        LOGGER.error(f"Error fetching last seen status for user {user.id}: {str(e)}")
        return "Unknown"

async def get_user_bio(user_id):
    try:
        user = await app.get_chat(user_id)
        return user.bio if user.bio else "No bio available"
    except Exception as e:
        LOGGER.error(f"Error fetching bio for user {user_id}: {str(e)}")
        return "No bio available"

@app.on_message(filters.command(["welcome"], prefixes=["/", "!"]) & filters.group)
async def toggle_welcome(_, message):
    chat_id = message.chat.id
    LOGGER.info(f"Welcome command received in chat_id {chat_id}: {message.text}")

    # Check if user is admin
    try:
        user = await app.get_chat_member(chat_id, message.from_user.id)
        if not user.privileges or not user.privileges.can_change_info:
            LOGGER.info(f"User {message.from_user.id} is not an admin in chat_id {chat_id}")
            await message.reply("You need to be an admin to use this command!")
            return
    except Exception as e:
        LOGGER.error(f"Error checking admin status in chat_id {chat_id}: {str(e)}")
        await message.reply("Error checking admin status!")
        return

    # Parse command
    command = message.text.lower()
    if "on" in command:
        welcome_settings[chat_id] = True
        LOGGER.info(f"Welcome enabled for chat_id {chat_id}")
        await message.reply("Welcome messages enabled for this group!")
    elif "off" in command:
        welcome_settings[chat_id] = False
        LOGGER.info(f"Welcome disabled for chat_id {chat_id}")
        await message.reply("Welcome messages disabled for this group!")
    else:
        status = welcome_settings.get(chat_id, True)
        LOGGER.info(f"Welcome status requested for chat_id {chat_id}: {status}")
        await message.reply(f"Welcome messages are currently {'enabled' if status else 'disabled'} for this group.\nUse /welcome off to disable.")

@app.on_message(filters.new_chat_members & filters.group, group=0)
async def welcome_new_members(_, message):
    chat_id = message.chat.id
    LOGGER.info(f"NewChatMembers event triggered for chat_id {chat_id}")

    # Check if welcome is disabled for this chat (default is True)
    if welcome_settings.get(chat_id, True) == False:
        LOGGER.info(f"Welcome is disabled for chat_id {chat_id}")
        return

    LOGGER.info(f"Skipping Pyrogram permissions check for chat_id {chat_id} as bot can send messages")

    # Handle bot being added to the group
    for u in message.new_chat_members:
        if u.id == app.me.id:
            if LOG_CHANNEL_ID:
                await app.send_message(LOG_CHANNEL_ID, f"""
NEW GROUP
➖➖➖➖➖➖➖➖➖➖➖
𝗡𝗔𝗠𝗘: {message.chat.title}
𝗜𝗗: {message.chat.id}
𝐔𝐒𝐄𝐑𝐍𝐀𝗠𝗘: @{message.chat.username if message.chat.username else "None"}
➖➖➖➖➖➖➖➖➖➖➖
""")
                LOGGER.info(f"Sent new group info to LOG_CHANNEL_ID {LOG_CHANNEL_ID}")
            else:
                LOGGER.warning("LOG_CHANNEL_ID not set, cannot send new group info")
            welcome_settings[chat_id] = True
            LOGGER.info(f"Welcome enabled by default for chat_id {chat_id}")
            continue

        # Welcome new members with photo and caption
        LOGGER.info(f"New member: {u.first_name} (ID: {u.id}) in chat {message.chat.title}")

        try:
            # Fetch additional user info
            last_seen = await get_last_seen_status(u)
            bio = await get_user_bio(u.id)

            # Download user profile picture
            pic = "AbhiXMusic/assets/AbhiWel.png"
            if u.photo:
                try:
                    pic = await app.download_media(
                        u.photo.big_file_id, file_name=f"pp{u.id}.png"
                    )
                    LOGGER.info(f"Profile picture downloaded for user {u.id} at {pic}")
                except Exception as e:
                    LOGGER.error(f"Error downloading profile picture for user {u.id}: {str(e)}")
                    pic = "AbhiXMusic/assets/AbhiWel.png"

            # Generate welcome image
            welcomeimg = welcomepic(
                pic, u.first_name, message.chat.title, u.id, u.username
            )

            # Prepare caption with the specified format
            caption = f"""
𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗧𝗼 {message.chat.title}
➖➖➖➖➖➖➖➖➖➖➖
➻ ᴜsᴇʀ ɪᴅ ‣ {u.id}
➻ ғɪʀsᴛ ɴᴀᴍᴇ ‣ {u.first_name}
➻ ʟᴀsᴛ ɴᴀᴍᴇ ‣ {u.last_name if u.last_name else "None"}
➻ ᴜsᴇʀɴᴀᴍᴇ ‣ @{u.username if u.username else "None"}
➻ ᴍᴇɴᴛɪᴏɴ ‣ {u.mention}
➻ ʟᴀsᴛ sᴇᴇɴ ‣ {last_seen}
➻ ᴅᴄ ɪᴅ ‣ {u.dc_id if u.dc_id else "Unknown"}
➻ ʙɪᴏ ‣ {bio}
➻ ᴛᴇʟᴇɢʀᴀᴍ ᴘʀᴇᴍɪᴜᴍ ‣ {'True' if u.is_premium else 'False'}
➖➖➖➖➖➖➖➖➖➖➖
๏ 𝐌𝐀𝐃𝐄 𝐁𝐘 ➠ [Aʙнɪ 𓆩🇽𓆪 �_KI𝗡𝗚 📿](https://t.me/imagine_iq)
"""

            # Send welcome photo with caption
            LOGGER.info(f"Sending welcome photo for user {u.id} in chat_id {chat_id}")
            temp.MELCOW[f"welcome-{chat_id}"] = await app.send_photo(
                chat_id,
                photo=welcomeimg,
                caption=caption,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⦿ ᴀᴅᴅ ᴍᴇ ⦿", url="https://t.me/RockXMusic_Robot?startgroup=true")]])
            )
            LOGGER.info(f"Welcome photo sent for user {u.id} in chat_id {chat_id}")
        except Exception as e:
            LOGGER.error(f"Error sending welcome photo for user {u.id}: {str(e)}")
            continue

        # Clean up files
        try:
            if os.path.exists(f"downloads/welcome#{u.id}.png"):
                os.remove(f"downloads/welcome#{u.id}.png")
                LOGGER.info(f"Deleted welcome image for user {u.id}")
            if os.path.exists(f"downloads/pp{u.id}.png"):
                os.remove(f"downloads/pp{u.id}.png")
                LOGGER.info(f"Deleted profile picture for user {u.id}")
        except Exception as e:
            LOGGER.error(f"Error cleaning up files: {str(e)}")
