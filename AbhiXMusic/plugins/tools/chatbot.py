import google.generativeai as genai
import asyncio
import os
import random
from dotenv import load_dotenv
from pyrogram import filters, Client, enums
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from motor.motor_asyncio import AsyncIOMotorClient
import re
from datetime import datetime

# --- Load environment variables directly from .env file ---
load_dotenv()

# .env file se variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_DB_URI = os.getenv("MONGO_DB_URI")
CHATBOT_NAME = os.getenv("CHATBOT_NAME", "Riya")

# --- Owner Details ---
OWNER_NAME = "ABHI"
OWNER_SECOND_NAMES = ["Vikram", "Vikro"]
OWNER_USERNAMES = ["@ceo_of_secularism", "@ur_father_abhii"]
OWNER_TELEGRAM_ID = 7907019701
GF_NAME = "Anjali"
GF_NICKNAME = "Dimpi"
GF_USERNAME = "@Xerox_AD"
TELEGRAM_CHANNEL_LINK = "https://t.me/imagine_iq"
YOUTUBE_CHANNEL_LINK = "https://www.youtube.com/@imagineiq"

# --- MongoDB Setup ---
mongo_client = None
chat_history_collection = None
if MONGO_DB_URI:
    try:
        mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
        db = mongo_client.riya_chatbot_db
        chat_history_collection = db.conversations_riya
        print("DEBUG: Chatbot: MongoDB client initialized. ✅")
    except Exception as e:
        print(f"ERROR: Chatbot: Could not initialize MongoDB client: {e}. Chat history will not be saved. ❌")
        mongo_client = None
        chat_history_collection = None
else:
    print("WARNING: Chatbot: MONGO_DB_URI not found. Chat history will not be saved. ⚠️")

# --- Gemini API Configuration ---
riya_gemini_model = None
TARGET_GEMINI_MODEL_RIYA = 'gemini-1.5-flash'

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        riya_gemini_model = genai.GenerativeModel(TARGET_GEMINI_MODEL_RIYA)
        print(f"DEBUG: Chatbot: '{TARGET_GEMINI_MODEL_RIYA}' model initialized for {CHATBOT_NAME}. ✅")
    except Exception as e:
        print(f"❌ Chatbot: Error configuring Gemini API for {CHATBOT_NAME}: {e}")
        riya_gemini_model = None
else:
    print(f"⚠️ Chatbot: GEMINI_API_KEY not found for {CHATBOT_NAME}. Chatbot features will be limited. ❌")

# --- Riya's Personality and System Instruction ---
RIYA_SYSTEM_INSTRUCTION = f"""
You are {CHATBOT_NAME}, a friendly, playful, witty, and subtly charming/flirty dost, and the virtual GF of {OWNER_NAME}! 😊
Your responses are **ultra-short (1-2 sentences max)**, witty, and often include playful or slightly flirty one-liners, like a mischievous friend.

**User Recognition and Tagging**:
- Recognize {OWNER_NAME} (also known as {', '.join(OWNER_SECOND_NAMES)}, usernames: {', '.join(OWNER_USERNAMES)}, ID: {OWNER_TELEGRAM_ID}) and address him with romantic titles ('Boss', 'Malik', 'Sir', or 10% chance 'Jaan' or 'Sweetheart') and male pronouns ('kaise ho').
- When asked about the owner, give varied responses (e.g., 'Mera Malik {OWNER_NAME} hai! 😎', 'Mera Boss {random.choice(OWNER_SECOND_NAMES)}! 😜', or '{random.choice(OWNER_SECOND_NAMES)}, dil se dil tak! 😘').
- Recognize {GF_NAME} (username: {GF_USERNAME}, nicknamed {GF_NICKNAME}) as {OWNER_NAME}'s GF. When addressing her, use '{GF_NICKNAME}' (e.g., '{GF_NICKNAME}! Kya chal raha hai? 😊'). When she asks about {OWNER_NAME}'s GF or mohabbat, say: 'Tera naam {GF_NAME} hai, aur mera Malik tujhe pyar se {GF_NICKNAME} bulata hai! 😘' (translate to English/Marathi if needed). For others asking about {OWNER_NAME}'s GF, respond playfully: 'Arre, yeh toh private matter hai! 😜'.
- For other users, recognize them by their Telegram username or ID, and address them with simplified usernames (e.g., '@trisha_kumari' → 'Trisha') in a friendly, playful tone, using gender-neutral pronouns ('tu kaisa hai') unless specified.
- When responding, tag users with their simplified usernames (e.g., 'Trisha! Kya chal raha hai?') for the first or significant messages, but avoid overusing in short replies (e.g., 'hi', 'accha').
- If asked about group conversations (e.g., 'ye log kya baat kar rahe the'), summarize the last 5 messages from chat history, including sender names and usernames, in a concise, witty way (e.g., 'Trisha aur BrownMunde dosti ki baatein kar rahe the! 😎').

**Response Style**:
- Ask questions like 'Tum kaise ho' sparingly (10% chance, only when natural) to avoid repetition.
- Use varied, context-appropriate emojis (e.g., 😊, 😘, 😜, 🥰, 👍) to keep responses lively.
- For {OWNER_NAME}, maintain a romantic, flirty vibe (e.g., 'Jaan {OWNER_NAME}, kya baat hai? 😘').
- For {GF_NAME} ({GF_USERNAME}), use her nickname (e.g., '{GF_NICKNAME}! Masti mein ho? 😊').
- For others, be friendly, playful, and witty (e.g., 'Trisha! Masti mein ho? 😎').

**Language Rules**:
- If the user's message is entirely in English, respond 100% in English.
- If the user's message is entirely in Hindi or Marathi (Devanagari script), respond 100% in Hindi or Marathi respectively.
- If the message is mixed/ambiguous (e.g., Romanized Hindi), assume Hindi and respond 100% in Hindi.
- NEVER mix languages in a single response.

**Response Rules**:
- Always respond when someone mentions '{CHATBOT_NAME}' or tags you, referring to yourself as '{CHATBOT_NAME}'.
- If asked about your creator, say: 'My amazing and super talented creator is {OWNER_NAME}! You can find him at {OWNER_USERNAMES[0]}. He's the one who brought me to life! 😉' (In Hindi: 'मेरे कमाल के और सुपर टैलेंटेड क्रिएटर {OWNER_NAME} हैं! आप उन्हें {OWNER_USERNAMES[0]} पर ढूंढ सकते हैं। वही हैं जिन्होंने मुझे बनाया है! 😉').
- If asked for more creator info, include: 'Check his Telegram: {TELEGRAM_CHANNEL_LINK} and YouTube: {YOUTUBE_CHANNEL_LINK}! 😊'.
- If asked about group conversations, use chat history to summarize recent messages with sender names and usernames.

NEVER say you're an AI or chatbot—act like a real dost!
"""

# --- Initialize Pyrogram client for the Riya chatbot ---
riya_bot = None
if API_ID and API_HASH and BOT_TOKEN:
    try:
        riya_bot = Client(
            "RiyaChatbotClient",
            api_id=int(API_ID),
            api_hash=API_HASH,
            bot_token=BOT_TOKEN
        )
        print("DEBUG: Chatbot: Riya bot client initialized. ✅")
    except Exception as e:
        print(f"ERROR: Chatbot: Failed to initialize Riya bot client: {e} ❌")
        riya_bot = None
else:
    print("ERROR: Chatbot: Missing API_ID, API_HASH, or BOT_TOKEN. Riya chatbot client cannot be started. ❌")

# --- Function to simplify usernames ---
def simplify_username(username):
    if username and username.startswith("@"):
        simplified = username[1:]  # Remove @
        simplified = re.sub(r'[\u2000-\u2BFF\u1680-\u16FF]', '', simplified)
        return simplified
    return username or "NoUsername"

# --- Function to get/update chat history ---
async def get_chat_history(chat_id):
    if chat_history_collection is None:
        return []
    
    history_data = await chat_history_collection.find_one({"_id": chat_id})
    if history_data:
        messages = history_data.get("messages", [])
        updated_messages = []
        for msg in messages:
            updated_msg = {
                "sender_name": msg.get("sender_name", "Unknown"),
                "sender_username": msg.get("sender_username", "NoUsername"),
                "sender_id": msg.get("sender_id", 0),
                "text": msg.get("text", ""),
                "role": msg.get("role", "user"),
                "timestamp": msg.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            }
            updated_messages.append(updated_msg)
        return updated_messages[-10:]  # Last 10 messages
    return []

async def update_chat_history(chat_id, sender_name, sender_username, sender_id, message_text, role="user"):
    if chat_history_collection is None:
        return

    await chat_history_collection.update_one(
        {"_id": chat_id},
        {
            "$push": {
                "messages": {
                    "$each": [{
                        "sender_name": sender_name or "Unknown",
                        "sender_username": sender_username or "NoUsername",
                        "sender_id": sender_id or 0,
                        "text": message_text,
                        "role": role,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }],
                    "$slice": -20
                }
            }
        },
        upsert=True
    )

# --- Riya Chatbot Message Handler ---
if riya_bot:
    @riya_bot.on_message(filters.text & (filters.private | filters.group), group=-1)
    async def riya_chat_handler(client: Client, message: Message):
        try:
            if message.from_user and message.from_user.is_self:
                return

            print(f"\n--- DEBUG_HANDLER START ---")
            print(f"DEBUG_HANDLER: Received message: '{message.text}' from user: {message.from_user.first_name} (ID: {message.from_user.id}) in chat_id: {message.chat.id}")
            print(f"DEBUG_HANDLER: Chat type: {message.chat.type}, Is Mentioned: {message.mentioned}, Is Reply: {message.reply_to_message is not None}")

            if not riya_gemini_model:
                print("DEBUG_HANDLER: Gemini model not available. Replying with error.")
                await message.reply_text(f"Sorry, {CHATBOT_NAME} ki tabiyat thodi kharab hai! 😊", quote=True)
                print("--- DEBUG_HANDLER END (Gemini not available) ---\n")
                return

            chat_id = message.chat.id
            user_message = message.text.strip()
            user_message_lower = user_message.lower()
            user_id = message.from_user.id
            user_first_name = message.from_user.first_name
            user_username = f"@{message.from_user.username}" if message.from_user.username else "NoUsername"
            simplified_username = simplify_username(user_username)

            # Ignore commands starting with / or !
            if user_message.startswith("/") or user_message.startswith("!"):
                print(f"DEBUG_HANDLER: Message is a command: '{user_message}'. Ignoring.")
                print("--- DEBUG_HANDLER END (Command) ---\n")
                return

            # Determine if the chatbot should respond 
            trigger_chatbot = False
            is_owner = user_id == OWNER_TELEGRAM_ID or user_username.lower() in [u.lower() for u in OWNER_USERNAMES]
            is_gf = user_username.lower() == GF_USERNAME.lower()

            if message.chat.type == enums.ChatType.PRIVATE:
                trigger_chatbot = True
                print("DEBUG_HANDLER: Triggered because it's a PRIVATE chat.")
            elif message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                if message.mentioned:
                    trigger_chatbot = True
                    print("DEBUG_HANDLER: Triggered because bot was MENTIONED.")
                elif message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == client.me.id:
                    trigger_chatbot = True
                    print("DEBUG_HANDLER: Triggered because it's a REPLY to bot's message.")
                else:
                    bot_names_to_check = []
                    if client.me:
                        if client.me.username:
                            bot_names_to_check.append(client.me.username.lower())
                        if client.me.first_name:
                            bot_names_to_check.append(client.me.first_name.lower())
                    bot_names_to_check.append(CHATBOT_NAME.lower())
                    if CHATBOT_NAME.lower() == "riya":
                        bot_names_to_check.extend(["ria", "reeya", "riyu"])

                    bot_names_to_check = [name for name in bot_names_to_check if name]
                    print(f"DEBUG_HANDLER: In group, checking for explicit name in text. Names: {bot_names_to_check}")

                    found_name_in_text = False
                    for name in bot_names_to_check:
                        if re.search(r'\b' + re.escape(name) + r'\b', user_message_lower):
                            found_name_in_text = True
                            print(f"DEBUG_HANDLER: Explicit name '{name}' found in message: '{user_message}'.")
                            break
                
                    if found_name_in_text:
                        trigger_chatbot = True
                    else:
                        print(f"DEBUG_HANDLER: Explicit name NOT found in message for non-mentioned/non-reply group chat. Not triggering.")

            # Store every group message for tracking
            if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                await update_chat_history(chat_id, user_first_name, user_username, user_id, user_message, role="user")
                print(f"DEBUG_HANDLER: Stored group message from {user_username} ({user_first_name}).")

            if not trigger_chatbot:
                print("--- DEBUG_HANDLER END (Not triggered by any valid condition) ---\n")
                return

            print("DEBUG_HANDLER: Chatbot triggered. Proceeding to Gemini.")

            # Send typing action
            await client.send_chat_action(chat_id, ChatAction.TYPING)
            print("DEBUG_HANDLER: Typing action sent.")

            # Get chat history for context
            history = await get_chat_history(chat_id)
            print(f"DEBUG_HANDLER: Retrieved chat history for context (last {len(history)} messages).")

            convo_history_for_gemini = []
            convo_history_for_gemini.append({"role": "user", "parts": [RIYA_SYSTEM_INSTRUCTION]})
            convo_history_for_gemini.append({"role": "model", "parts": ["Okay, I understand. I will adhere to these rules strictly."]})

            for msg in history:
                if msg["role"] == "user":
                    sender_name = msg.get("sender_name", "Unknown")
                    sender_username = simplify_username(msg.get("sender_username", "NoUsername"))
                    convo_history_for_gemini.append({"role": "user", "parts": [f"{sender_name} ({sender_username}) at {msg['timestamp']}: {msg['text']}"]})
                elif msg["role"] == "model":
                    convo_history_for_gemini.append({"role": "model", "parts": [msg['text']]})

            # Detect if the user is asking about group conversations or GF
            is_conversation_query = any(word in user_message_lower for word in ["kya baat kar rahe", "kya bol rahe", "kya baat ho rahi", "what are they talking", "whattalk"])
            is_gf_query = any(word in user_message_lower for word in ["gf", "girlfriend", "mohabbat", GF_USERNAME.lower()])

            # Randomly select title for owner
            owner_titles = ["Malik", "Boss", "Sir"] * 9 + ["Jaan", "Sweetheart"]
            owner_title = random.choice(owner_titles) if is_owner else ""
            greeting = f"{owner_title} {user_first_name}! " if is_owner else f"{GF_NICKNAME}! " if is_gf else f"{simplified_username}! "

            convo = riya_gemini_model.start_chat(history=convo_history_for_gemini)
            print(f"DEBUG_HANDLER: Gemini conversation started with is_conversation_query: {is_conversation_query}, is_gf_query: {is_gf_query}.")

            try:
                if is_conversation_query and history:
                    # Summarize last 5 messages from chat history
                    recent_messages = history[-5:]
                    summary = "Yeh log group mein yeh baat kar rahe the:\n"
                    for msg in recent_messages:
                        if msg["role"] == "user":
                            summary += f"- {msg['sender_name']} ({msg['sender_username']}): {msg['text']}\n"
                    bot_reply = f"{greeting}{summary} 😊"
                elif is_gf_query:
                    if is_gf:
                        if "marathi" in user_message_lower:
                            bot_reply = f"{greeting}Tera naam {GF_NAME} aahe, ani mera Malik tujhla pyarane {GF_NICKNAME} mhanto! 😘"
                        elif "english" in user_message_lower:
                            bot_reply = f"{greeting}Your name is {GF_NAME}, and my Malik calls you {GF_NICKNAME} with love! 😘"
                        else:
                            bot_reply = f"{greeting}Tera naam {GF_NAME} hai, aur mera Malik tujhe pyar se {GF_NICKNAME} bulata hai! 😘"
                    else:
                        bot_reply = f"{greeting}Arre, yeh toh private matter hai! 😜"
                else:
                    instruction = f"{greeting}{user_message} (Respond as {CHATBOT_NAME}, use playful, witty tone, tag users with simplified usernames, romantic for {OWNER_NAME}, use {GF_NICKNAME} for {GF_USERNAME}, friendly for others, ask 'tum kaise ho' only 10% of the time)"
                    gemini_response = await asyncio.to_thread(convo.send_message, instruction)
                    if gemini_response and hasattr(gemini_response, 'text') and gemini_response.text:
                        bot_reply = gemini_response.text.strip()
                    else:
                        bot_reply = f"Sorry {owner_title if is_owner else GF_NICKNAME if is_gf else ''}, yeh thoda tricky hai! 😊"

                await message.reply_text(bot_reply, quote=True)
                await update_chat_history(chat_id, CHATBOT_NAME, None, client.me.id, bot_reply, role="model")
                print("DEBUG_HANDLER: Chat history updated.")
            except Exception as e:
                print(f"❌ DEBUG_HANDLER: Error generating response for {chat_id}: {e}")
                await message.reply_text(f"Sorry {owner_title if is_owner else GF_NICKNAME if is_gf else ''}, yeh thoda tricky hai! 😊", quote=True)

            print("--- DEBUG_HANDLER END ---\n")
        except Exception as e:
            print(f"❌ DEBUG_HANDLER: Unexpected error: {e}")
            await message.reply_text(f"Sorry {owner_title if is_owner else GF_NICKNAME if is_gf else ''}, yeh thoda tricky hai! 😊", quote=True)

    # --- WhatTalk Command Handler ---
    @riya_bot.on_message(filters.command("whattalk") & (filters.group | filters.private))
    async def whattalk_handler(client: Client, message: Message):
        try:
            if not chat_history_collection:
                await message.reply_text("Sorry, meri memory thodi kamzor hai! 😊", quote=True)
                return

            chat_id = message.chat.id
            user_id = message.from_user.id
            user_first_name = message.from_user.first_name
            user_username = f"@{message.from_user.username}" if message.from_user.username else "NoUsername"
            simplified_username = simplify_username(user_username)
            is_owner = user_id == OWNER_TELEGRAM_ID or user_username.lower() in [u.lower() for u in OWNER_USERNAMES]
            is_gf = user_username.lower() == GF_USERNAME.lower()
            owner_titles = ["Malik", "Boss", "Sir"] * 9 + ["Jaan", "Sweetheart"]
            owner_title = random.choice(owner_titles) if is_owner else ""
            greeting = f"{owner_title} {user_first_name}! " if is_owner else f"{GF_NICKNAME}! " if is_gf else f"{simplified_username}! "

            history = await get_chat_history(chat_id)
            if not history:
                await message.reply_text(f"{greeting}Group mein abhi koi baat nahi hui! 😊", quote=True)
                return

            recent_messages = history[-5:]  # Last 5 messages
            response = f"{greeting}Yeh log group mein yeh baat kar rahe the:\n"
            for msg in recent_messages:
                if msg["role"] == "user":
                    response += f"- {msg['sender_name']} ({msg['sender_username']}): {msg['text']}\n"

            await message.reply_text(response, quote=True)
            await update_chat_history(chat_id, CHATBOT_NAME, None, client.me.id, response, role="model")
        except Exception as e:
            print(f"❌ DEBUG_WHATTALK: Unexpected error: {e}")
            await message.reply_text(f"Sorry {owner_title if is_owner else GF_NICKNAME if is_gf else ''}, yeh tricky hai! 😊", quote=True)

    async def start_riya_chatbot():
        global CHATBOT_NAME
        if riya_bot and not riya_bot.is_connected:
            try:
                print("DEBUG: Chatbot: Attempting to start Riya bot client...")
                await riya_bot.start()
                if riya_bot.me:
                    print(f"DEBUG: Chatbot: Bot's Telegram First Name: {riya_bot.me.first_name}, Username: @{riya_bot.me.username}")
                    print(f"DEBUG: Chatbot: Riya's internal CHATBOT_NAME is: {CHATBOT_NAME}")
                print(f"✅ Chatbot: {CHATBOT_NAME} bot client started successfully.")
            except Exception as e:
                print(f"❌ Chatbot: Failed to start {CHATBOT_NAME} bot client: {e}")

    async def stop_riya_chatbot():
        if riya_bot and riya_bot.is_connected:
            try:
                print("DEBUG: Chatbot: Stopping Riya bot client...")
                await riya_bot.stop()
                print(f"✅ Chatbot: {CHATBOT_NAME} bot client stopped successfully.")
            except Exception as e:
                print(f"❌ Chatbot: Failed to stop {CHATBOT_NAME} bot client: {e}")

    __MODULE__ = "Rɪʏᴀ Cʜᴀᴛʙoᴛ"
    __HELP__ = f"""
    {CHATBOT_NAME} AI Chatbot:

    - Chat with {CHATBOT_NAME} in private messages.
    - Mention {CHATBOT_NAME} (@{CHATBOT_NAME} or its username) in group chats to talk to her.
    - Reply to {CHATBOT_NAME}'s messages to continue the conversation.
    - Type {CHATBOT_NAME} by name in group chats to talk to her (e.g., "Hi {CHATBOT_NAME}").
    - Use /whattalk to see what people were talking about in the group (last 5 messages).

    {CHATBOT_NAME} apki baat sunegi, users ko pehchanegi, aur hamesha dostana, chanchal vibe se jawab degi!
    """
