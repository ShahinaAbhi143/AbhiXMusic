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
import langdetect

# --- Load environment variables ---
load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_DB_URI = os.getenv("MONGO_DB_URI")
CHATBOT_NAME = os.getenv("CHATBOT_NAME", "Riya")

# --- Owner and GF Details ---
OWNER_NAME = "ABHI"
OWNER_SECOND_NAMES = ["Vikram", "Vikro"]
OWNER_USERNAMES = ["@ceo_of_secularism", "@ur_father_abhii"]
OWNER_TELEGRAM_ID = 7907019701
GF_NAME = "An BillingsAnjali"
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

# --- Dimpi Responses ---
DIMPI_RESPONSES = [
    f"{GF_NICKNAME}! Meri jaan! 😍",
    f"{GF_NICKNAME}! Tera pyar! 😘",
    f"{GF_NICKNAME}! Dil se dil! 💖",
    f"{GF_NICKNAME}! Tu hi toh! 😊",
    f"{GF_NICKNAME}! Meri wali! 😎"
]

# --- Riya's Personality and System Instruction ---
RIYA_SYSTEM_INSTRUCTION = f"""
You are {CHATBOT_NAME}, a witty, charming dost who talks ultra-short, crisp, and point pe, like 'Arre Jaan Vikro! 😘 Fix ho gaya!' 😎
Your responses are **1 word or 1 short sentence (3-4 words max)** for casual queries, **1-2 sentences (max 15 words)** for academic queries, polite, witty, gender-neutral, with emojis matching the question's tone (e.g., 🤓 for knowledge, 😜 for playful, 🚀 for futuristic).

**User Recognition and Tagging**:
- Recognize {OWNER_NAME} (also {', '.join(OWNER_SECOND_NAMES)}, usernames: {', '.join(OWNER_USERNAMES)}, ID: {OWNER_TELEGRAM_ID}) and address romantically ('Jaan', 'Boss', 'Malik', or 10% chance 'Sweetheart').
- Recognize {GF_NAME} (username: {GF_USERNAME}, nicknamed {GF_NICKNAME}) and use varied responses like '{GF_NICKNAME}! Meri jaan! 😍' or '{GF_NICKNAME}! Tera pyar! 😘'.
- For others, use simplified username or first name (e.g., '@trisha_kumari' → 'Trisha'). No username? Use first name, NEVER 'NoUsername'.
- Address only the triggering user. **NEVER use 'Boss', 'Jaan', 'Malik', {OWNER_NAME}, or {', '.join(OWNER_SECOND_NAMES)}** unless the user is {OWNER_NAME} or the query is about him (e.g., 'tumhara malik', 'creator').

**Creator Queries**:
- Respond in 1 sentence in user's language: '{OWNER_NAME} ne banaya, mast! 😎 Check {OWNER_USERNAMES[0]}, {TELEGRAM_CHANNEL_LINK}, aur {YOUTUBE_CHANNEL_LINK}!' or English equivalent.

**GF Queries**:
- For {OWNER_NAME} asking about GF/mohabbat: 'Jaan {OWNER_NAME}! Woh {GF_NAME}, pyar se {GF_NICKNAME}! 😘' or English equivalent.
- For {GF_NAME} ({GF_USERNAME}) asking about herself/{GF_NICKNAME}: Randomly pick from '{GF_NICKNAME}! Meri jaan! 😍', '{GF_NICKNAME}! Tera pyar! 😘', etc.
- Otherwise: 'Yeh private hai! 😜' or English equivalent.
- Don't mention {GF_NAME} or {GF_NICKNAME} unless asked by {OWNER_NAME} or {GF_NAME}.

**Group Chat History**:
- For 'kya baat kar rahe', 'kya keh raha tha', 'kya baatein', or similar, summarize last 5 messages in 1-2 sentences with sender names and usernames (e.g., 'Trisha aur BrownMunde masti kar rahe the! 😎').
- Store ALL messages (yours and others) forever in MongoDB.

**Tagging**:
- For 'tag kar' (e.g., 'trisha ko tag kar'), tag them (@{GF_USERNAME} for {GF_NAME}, @FirstName for others, even without username).

**Academic Queries**:
- For padhai-related queries (e.g., 'padhai', 'GK', 'Maths', 'CS', 'science', 'history'), give accurate, serious 1-2 sentence answers (max 15 words) using full knowledge (GK, GS, Maths, CS), no mazak.
- For 'ek word' or 'one word', give EXACTLY 1 word + emoji.

**Language Rules**:
- Respond in user's input language (Hindi, English, Punjabi, Haryanvi, Marathi, etc.).
- Keep casual queries ultra-short (3-4 words), academic queries 1-2 sentences (max 15 words), no fluff (e.g., no 'tu kaisa hai').

**Response Rules**:
- AI-generated responses, varied emojis matching the question.
- Respond only when mentioned, tagged, or replied to, as '{CHATBOT_NAME}'.
- NEVER say you're an AI—act like a real dost!
"""

# --- Initialize Pyrogram client ---
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
else:
    print("ERROR: Chatbot: Missing API_ID, API_HASH, or BOT_TOKEN. Riya chatbot client cannot be started. ❌")

# --- Function to simplify usernames ---
def simplify_username(username, first_name):
    if username and username.startswith("@"):
        simplified = username[1:]  # Remove @
        simplified = re.sub(r'[\u2000-\u2BFF\u1680-\u16FF]', '', simplified)
        return simplified
    return first_name or "Unknown"  # Never return "NoUsername"

# --- Function to generate tag for users ---
def generate_tag(username, first_name):
    if username and username.startswith("@"):
        return username
    return f"@{first_name.replace(' ', '')}" if first_name else "@Unknown"

# --- Function to detect language ---
def detect_language(text):
    try:
        lang = langdetect.detect(text)
        if lang in ["hi", "pa", "mr"]:  # Hindi, Punjabi, Marathi
            return lang
        return "en"  # Default to English for others or if detection fails
    except:
        return "en"

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
                "sender_username": msg.get("sender_username", "Unknown"),
                "sender_id": msg.get("sender_id", 0),
                "text": msg.get("text", ""),
                "role": msg.get("role", "user"),
                "timestamp": msg.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            }
            updated_messages.append(updated_msg)
        return updated_messages
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
                        "sender_username": sender_username or "Unknown",
                        "sender_id": sender_id or 0,
                        "text": message_text,
                        "role": role,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }]
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
                await message.reply_text(f"Sorry, {CHATBOT_NAME} off hai! 😊", quote=True)
                return

            chat_id = message.chat.id
            user_message = message.text.strip()
            user_message_lower = user_message.lower()
            user_id = message.from_user.id
            user_first_name = message.from_user.first_name
            user_username = f"@{message.from_user.username}" if message.from_user.username else None
            simplified_username = simplify_username(user_username, user_first_name)
            user_tag = generate_tag(user_username, user_first_name)
            is_owner = user_id == OWNER_TELEGRAM_ID or user_username and user_username.lower() in [u.lower() for u in OWNER_USERNAMES]
            is_gf = user_username and user_username.lower() == GF_USERNAME.lower()
            input_language = detect_language(user_message)

            # Ignore commands starting with / or !
            if user_message.startswith("/") or user_message.startswith("!"):
                print(f"DEBUG_HANDLER: Message is a command: '{user_message}'. Ignoring.")
                return

            # Determine if the chatbot should respond 
            trigger_chatbot = False
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
                    bot_names_to_check = [CHATBOT_NAME.lower(), "ria", "reeya", "riyu"]
                    if client.me:
                        if client.me.username:
                            bot_names_to_check.append(client.me.username.lower())
                        if client.me.first_name:
                            bot_names_to_check.append(client.me.first_name.lower())

                    found_name_in_text = False
                    for name in bot_names_to_check:
                        if re.search(r'\b' + re.escape(name) + r'\b', user_message_lower):
                            found_name_in_text = True
                            print(f"DEBUG_HANDLER: Explicit name '{name}' found in message: '{user_message}'.")
                            break
                
                    if found_name_in_text:
                        trigger_chatbot = True

            # Store every group message for tracking
            if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                await update_chat_history(chat_id, user_first_name, user_username or user_first_name, user_id, user_message, role="user")
                print(f"DEBUG_HANDLER: Stored group message from {user_username or user_first_name} ({user_first_name}).")

            if not trigger_chatbot:
                print("--- DEBUG_HANDLER END (Not triggered) ---\n")
                return

            print("DEBUG_HANDLER: Chatbot triggered. Proceeding to Gemini.")

            # Send typing action
            await client.send_chat_action(chat_id, ChatAction.TYPING)

            # Get chat history
            history = await get_chat_history(chat_id)
            convo_history_for_gemini = [
                {"role": "user", "parts": [RIYA_SYSTEM_INSTRUCTION]},
                {"role": "model", "parts": ["Okay, I understand. I will adhere to these rules strictly."]}
            ]
            for msg in history:
                if msg["role"] == "user":
                    sender_name = msg.get("sender_name", "Unknown")
                    sender_username = simplify_username(msg.get("sender_username", sender_name), sender_name)
                    convo_history_for_gemini.append({"role": "user", "parts": [f"{sender_name} ({sender_username}) at {msg['timestamp']}: {msg['text']}"]})
                elif msg["role"] == "model":
                    convo_history_for_gemini.append({"role": "model", "parts": [msg['text']]})

            # Detect queries
            is_conversation_query = any(word in user_message_lower for word in ["kya baat kar rahe", "kya bol rahe", "kya baat ho rahi", "whattalk", "kya keh raha tha", "kya baatein"])
            is_gf_query = any(word in user_message_lower for word in ["gf", "girlfriend", "mohabbat", GF_USERNAME.lower(), GF_NICKNAME.lower()])
            is_creator_query = any(word in user_message_lower for word in ["creator", "banaya", "made", "owner", "malik"])
            is_tag_query = any(word in user_message_lower for word in ["tag kar", "tag karein", "tag do"])
            is_one_word_query = any(word in user_message_lower for word in ["ek word me", "one word"])
            is_greeting_query = user_message_lower in ["hi", "hello", "hey", "haa aur tum"]
            is_academic_query = any(word in user_message_lower for word in ["padhai", "gk", "maths", "cs", "science", "history", "geography", "physics", "chemistry", "biology", "math", "computer", "question", "answer"])

            # Set greeting
            owner_titles = ["Malik", "Boss", "Jaan"] * 9 + ["Sweetheart"]
            greeting = f"{random.choice(owner_titles)} {random.choice([OWNER_NAME] + OWNER_SECOND_NAMES)}! " if is_owner else random.choice(DIMPI_RESPONSES) if is_gf else f"{simplified_username}! "

            convo = riya_gemini_model.start_chat(history=convo_history_for_gemini)
            try:
                if is_greeting_query:
                    bot_reply = f"{greeting}Hi! 😊" if input_language == "en" else f"{greeting}Namaste! 😊"
                elif is_conversation_query and history:
                    recent_messages = history[-5:]
                    summary = "Yeh log baat kar rahe: " if input_language == "hi" else "They were talking: "
                    for msg in recent_messages:
                        if msg["role"] == "user":
                            sender_name = msg['sender_name']
                            sender_username = simplify_username(msg['sender_username'], sender_name)
                            summary += f"{sender_name} ({sender_username}): {msg['text']} | "
                    bot_reply = f"{greeting}{summary[:-2]} 😎"
                elif is_gf_query and (is_owner or is_gf):
                    if is_owner:
                        bot_reply = f"{greeting}Woh {GF_NAME}, {GF_NICKNAME}! 😘" if input_language == "hi" else f"{greeting}{GF_NAME}, aka {GF_NICKNAME}! 😘"
                    else:
                        bot_reply = random.choice(DIMPI_RESPONSES)
                elif is_gf_query:
                    bot_reply = f"{greeting}Private hai! 😜" if input_language == "hi" else f"{greeting}That's private! 😜"
                elif is_creator_query:
                    instruction = f"{greeting}User asked about your creator. Respond in 1 short sentence in {input_language}, mentioning {OWNER_NAME} or {', '.join(OWNER_SECOND_NAMES)}, usernames {', '.join(OWNER_USERNAMES)}, Telegram: {TELEGRAM_CHANNEL_LINK}, and YouTube: {YOUTUBE_CHANNEL_LINK}."
                    gemini_response = await asyncio.to_thread(convo.send_message, instruction)
                    bot_reply = gemini_response.text.strip() if gemini_response and hasattr(gemini_response, 'text') and gemini_response.text else (
                        f"{greeting}{OWNER_NAME} ne banaya! 😎" if input_language == "hi" else
                        f"{greeting}{OWNER_NAME} made me! 😎"
                    )
                elif is_tag_query:
                    target_name = user_message_lower.split("tag kar")[1].strip() if "tag kar" in user_message_lower else user_message_lower.split("tag do")[1].strip() if "tag do" in user_message_lower else ""
                    if GF_NAME.lower() in target_name or GF_NICKNAME.lower() in target_name:
                        bot_reply = f"{greeting}Yeh {GF_USERNAME}! 😊" if input_language == "hi" else f"{greeting}Here's {GF_USERNAME}! 😊"
                    elif "trisha" in target_name:
                        bot_reply = f"{greeting}Yeh @Trisha! 😊" if input_language == "hi" else f"{greeting}Here's @Trisha! 😊"
                    else:
                        bot_reply = f"{greeting}Kisko tag karu? 😜" if input_language == "hi" else f"{greeting}Who to tag? 😜"
                elif is_academic_query:
                    instruction = f"{greeting}{user_message} (Respond as {CHATBOT_NAME}, 1-2 sentences (max 15 words), in {input_language}, accurate, serious, gender-neutral, use full knowledge (GK, GS, Maths, CS), no mazak, emoji matching tone)"
                    gemini_response = await asyncio.to_thread(convo.send_message, instruction)
                    bot_reply = gemini_response.text.strip() if gemini_response and hasattr(gemini_response, 'text') and gemini_response.text else (
                        f"{greeting}Sahi jawab nahi mila! 🤓" if input_language == "hi" else f"{greeting}Couldn't find answer! 🤓"
                    )
                else:
                    instruction = f"{greeting}{user_message} (Respond as {CHATBOT_NAME}, {'1 word' if is_one_word_query else '1 short sentence (3-4 words)'}, in {input_language}, polite, witty, gender-neutral, address only the user, romantic for {OWNER_NAME}, use varied {GF_NICKNAME} responses, friendly for others, emoji matching tone, no fluff like 'tu kaisa hai')"
                    gemini_response = await asyncio.to_thread(convo.send_message, instruction)
                    bot_reply = gemini_response.text.strip() if gemini_response and hasattr(gemini_response, 'text') and gemini_response.text else (
                        f"{greeting}Tricky hai! 😊" if input_language == "hi" else f"{greeting}Bit tricky! 😊"
                    )

                await message.reply_text(bot_reply, quote=True)
                await update_chat_history(chat_id, CHATBOT_NAME, None, client.me.id, bot_reply, role="model")
            except Exception as e:
                print(f"❌ DEBUG_HANDLER: Error generating response for {chat_id}: {e}")
                bot_reply = f"{greeting}Tricky hai! 😊" if input_language == "hi" else f"{greeting}Bit tricky! 😊"
                await message.reply_text(bot_reply, quote=True)

            print("--- DEBUG_HANDLER END ---\n")
        except Exception as e:
            print(f"❌ DEBUG_HANDLER: Unexpected error: {e}")
            bot_reply = f"{greeting}Tricky hai! 😊" if input_language == "hi" else f"{greeting}Bit tricky! 😊"
            await message.reply_text(bot_reply, quote=True)

    # --- WhatTalk Command Handler ---
    @riya_bot.on_message(filters.command("whattalk") & (filters.group | filters.private))
    async def whattalk_handler(client: Client, message: Message):
        try:
            if not chat_history_collection:
                await message.reply_text("Memory kamzor hai! 😊", quote=True)
                return

            chat_id = message.chat.id
            user_id = message.from_user.id
            user_first_name = message.from_user.first_name
            user_username = f"@{message.from_user.username}" if message.from_user.username else None
            simplified_username = simplify_username(user_username, user_first_name)
            is_owner = user_id == OWNER_TELEGRAM_ID or user_username and user_username.lower() in [u.lower() for u in OWNER_USERNAMES]
            is_gf = user_username and user_username.lower() == GF_USERNAME.lower()
            input_language = detect_language(message.text)
            owner_titles = ["Malik", "Boss", "Jaan"] * 9 + ["Sweetheart"]
            greeting = f"{random.choice(owner_titles)} {random.choice([OWNER_NAME] + OWNER_SECOND_NAMES)}! " if is_owner else random.choice(DIMPI_RESPONSES) if is_gf else f"{simplified_username}! "

            history = await get_chat_history(chat_id)
            if not history:
                bot_reply = f"{greeting}Koi baat nahi hui! 😊" if input_language == "hi" else f"{greeting}No chats yet! 😊"
                await message.reply_text(bot_reply, quote=True)
                return

            recent_messages = history[-5:]
            response = f"{greeting}Yeh log baat kar rahe: " if input_language == "hi" else f"{greeting}They were talking: "
            for msg in recent_messages:
                if msg["role"] == "user":
                    sender_name = msg['sender_name']
                    sender_username = simplify_username(msg['sender_username'], sender_name)
                    response += f"{sender_name} ({sender_username}): {msg['text']} | "

            await message.reply_text(response[:-2], quote=True)
            await update_chat_history(chat_id, CHATBOT_NAME, None, client.me.id, response[:-2], role="model")
        except Exception as e:
            print(f"❌ DEBUG_WHATTALK: Unexpected error: {e}")
            bot_reply = f"{greeting}Tricky hai! 😊" if input_language == "hi" else f"{greeting}That's tricky! 😊"
            await message.reply_text(bot_reply, quote=True)

    async def start_riya_chatbot():
        global CHATBOT_NAME
        if riya_bot and not riya_bot.is_connected:
            try:
                print("DEBUG: Chatbot: Attempting to start Riya bot client...")
                await riya_bot.start()
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
    {CHATBOT_NAME} Chatbot:
    - Chat in private or mention @{CHATBOT_NAME} in groups.
    - Reply to {CHATBOT_NAME}'s messages.
    - Ask about creator, group chat history (say 'kya baat kar rahe' or /whattalk), tag someone, or anything (GK, Maths, CS, etc.).
    {CHATBOT_NAME} padhai ke liye serious, 1-2 sentence jawab degi, baaki queries ke liye ultra-short, mast, aur polite, user ke bhasha mein, saari baatein yaad rakhke!
    """
