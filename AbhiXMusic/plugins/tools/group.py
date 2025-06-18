from pyrogram import enums, filters
from pyrogram.types import Message
from AbhiXMusic import app
from AbhiXMusic.utils.decorators import AdminRightsCheck  # Updated import

# Temporary placeholder for adminsOnly decorator (replaced with AdminRightsCheck)
@app.on_message(filters.command("removephoto"))
@AdminRightsCheck  # Updated to use AdminRightsCheck
async def deletechatphoto(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    msg = await message.reply_text("**ᴘʀᴏᴄᴇssɪɴɢ....**")
    admin_check = await app.get_chat_member(chat_id, user_id)
    if message.chat.type == enums.ChatType.PRIVATE:
        await msg.edit("**ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋ ᴏɴ ɢʀᴏᴜᴘs !**")
    try:
        if admin_check.privileges.can_change_info:
            await app.delete_chat_photo(chat_id)
            await msg.edit(
                "**ɢʀᴏᴜᴘs  ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏ ʀᴇᴍᴏᴠᴇᴅ  !\nʙʏ** {}".format(
                    message.from_user.mention
                )
            )
    except BaseException:
        await msg.edit(
            "**ᴛʜᴇ ᴜsᴇʀ ᴍᴏsᴛ ɴᴇᴇᴅ ᴄʜᴀɴɢᴇ ɪɴғᴏ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ᴛᴏ ʀᴇᴍᴏᴠᴇ ɢʀᴏᴜᴘ ᴘʜᴏᴛᴏ !**"
        )


@app.on_message(filters.command("setphoto"))
@AdminRightsCheck  # Updated to use AdminRightsCheck
async def setchatphoto(_, message: Message):
    reply = message.reply_to_message
    chat_id = message.chat.id
    user_id = message.from_user.id
    msg = await message.reply_text("ᴘʀᴏᴄᴇssɪɴɢ...")
    admin_check = await app.get_chat_member(chat_id, user_id)
    if message.chat.type == enums.ChatType.PRIVATE:
        await msg.edit("`ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋ ᴏɴ ɢʀᴏᴜᴘs !`")
    elif not reply:
        await msg.edit("**ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴘʜᴏᴛᴏ ᴏʀ ᴅᴏᴄᴜᴍᴇɴᴛ.**")
    elif reply:
        try:
            if admin_check.privileges.can_change_info:
                photo = await reply.download()
                await message.chat.set_photo(photo=photo)
                await msg.edit_text(
                    "**ɴᴇᴡ ɢʀᴏᴜᴘ ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏ ᴄʜᴀɴɢᴇᴅ !\nʙʏ** {}".format(
                        message.from_user.mention
                    )
                )
            else:
                await msg.edit("**sᴏᴍᴇᴛʜɪɴɢ ᴡʀᴏɴɢ ʜᴀᴘᴘᴇɴᴇᴅ ᴛʀʏ ᴀɴᴏᴛʜᴇʀ ᴘʜᴏᴛᴏ !**")

        except BaseException:
            await msg.edit(
                "**ᴛʜᴇ ᴜsᴇʀ ᴍᴏsᴛ ɴᴇᴇᴅ ᴄʜᴀɴɢᴇ ɪɴғᴏ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ᴘʜᴏᴛᴏ !**"
            )


@app.on_message(filters.command("settitle"))
@AdminRightsCheck  # Updated to use AdminRightsCheck
async def setgrouptitle(_, message: Message):
    reply = message.reply_to_message
    chat_id = message.chat.id
    user_id = message.from_user.id
    msg = await message.reply_text("ᴘʀᴏᴄᴇssɪɴɢ...")
    if message.chat.type == enums.ChatType.PRIVATE:
        await msg.edit("**ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋ ᴏɴ ɢʀᴏᴜᴘs !**")
    elif reply:
        try:
            title = message.reply_to_message.text
            admin_check = await app.get_chat_member(chat_id, user_id)
            if admin_check.privileges.can_change_info:
                await message.chat.set_title(title)
                await msg.edit(
                    "**ɴᴇᴡ ɢʀᴏᴜᴘ ɴᴀᴍᴇ ᴄʜᴀɴɢᴇᴅ !\nʙʏ** {}".format(
                        message.from_user.mention
                    )
                )
        except AttributeError:
            await msg.edit(
                "ᴛʜᴇ ᴜsᴇʀ ᴍᴏsᴛ ɴᴇᴇᴅ **ᴄʜᴀɴɢᴇ ɪɴғᴏ** ᴀᴅᴍɪɴ ʀɪɢʜᴛs ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ᴛɪᴛʟᴇ !"
            )
    elif len(message.command) > 1:
        try:
            title = message.text.split(None, 1)[1]
            admin_check = await app.get_chat_member(chat_id, user_id)
            if admin_check.privileges.can_change_info:
                await message.chat.set_title(title)
                await msg.edit(
                    "**ɴᴇᴡ ɢʀᴏᴜᴘ ɴᴀᴍᴇ ᴄʜᴀɴɢᴇᴅ !\nʙʏ** {}".format(
                        message.from_user.mention
                    )
                )
        except AttributeError:
            await msg.edit(
                "**ᴛʜᴇ ᴜsᴇʀ ᴍᴏsᴛ ɴᴇᴇᴅ ᴄʜᴀɴɢᴇ ɪɴғᴏ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ᴛɪᴛʟᴇ !**"
            )

    else:
        await msg.edit(
            "**ʏᴏᴜ ɴᴇᴇᴅ ʀᴇᴘʟʏ ᴛᴏ ᴛᴇxᴛ ᴏʀ ɢɪᴠᴇ sᴏᴍᴇ ᴛᴇxᴛ ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ᴛɪᴛʟᴇ **"
        )


@app.on_message(filters.command(["setdiscription", "setdesc"]))
@AdminRightsCheck  # Updated to use AdminRightsCheck
async def setg_discription(_, message: Message):
    reply = message.reply_to_message
    chat_id = message.chat.id
    user_id = message.from_user.id
    msg = await message.reply_text("**ᴘʀᴏᴄᴇssɪɴɢ...**")
    if message.chat.type == enums.ChatType.PRIVATE:
        await msg.edit("**ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋs ᴏɴ ɢʀᴏᴜᴘs!**")
    elif reply:
        try:
            discription = message.reply_to_message.text
            admin_check = await app.get_chat_member(chat_id, user_id)
            if admin_check.privileges.can_change_info:
                await message.chat.set_description(discription)
                await msg.edit(
                    "**ɴᴇᴡ ᴅɪsᴄʀɪᴘᴛɪᴏɴ ᴏғ ɢʀᴏᴜᴘ ᴄʜᴀɴɢᴇᴅ!**\nʙʏ {}".format(
                        message.from_user.mention
                    )
                )
        except AttributeError:
            await msg.edit(
                "**ᴛʜᴇ ᴜsᴇʀ ᴍᴜsᴛ ʜᴀᴠᴇ ᴄʜᴀɴɢᴇ ɪɴғᴏ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ᴅɪsᴄʀɪᴘᴛɪᴏɴ!**"
            )
    elif len(message.command) > 1:
        try:
            discription = message.text.split(None, 1)[1]
            admin_check = await app.get_chat_member(chat_id, user_id)
            if admin_check.privileges.can_change_info:
                await message.chat.set_description(discription)
                await msg.edit(
                    "**ɴᴇᴡ ᴅɪsᴄʀɪᴘᴛɪᴏɴ ᴏғ ɢʀᴏᴜᴘ ᴄʜᴀɴɢᴇᴅ!**\nʙʏ {}".format(
                        message.from_user.mention
                    )
                )
        except AttributeError:
            await msg.edit(
                "**ᴛʜᴇ ᴜsᴇʀ ᴍᴜsᴛ ʜᴀᴠᴇ ᴄʜᴀɴɢᴇ ɪɴғᴏ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ᴅɪsᴄʀɪᴘᴛɪᴏɴ!**"
            )
    else:
        await msg.edit(
            "**ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ʀᴇᴘʟʏ ᴛᴏ ᴛᴇxᴛ ᴏʀ ɢɪᴠᴇ sᴏᴍᴇ ᴛᴇxᴛ ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ᴅɪsᴄʀɪᴘᴛᴏɴ!**"
        )