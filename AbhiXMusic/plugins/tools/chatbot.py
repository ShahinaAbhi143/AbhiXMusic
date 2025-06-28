import google.generativeai as genai
import asyncio
import os
from dotenv import load_dotenv
from pyrogram import filters, Client, enums
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from motor.motor_asyncio import AsyncIOMotorClient
import re
from datetime import datetime
from pyrogram.errors import BadMsgNotification

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
OWNER_USERNAMES = ["@ceo_of_secularism", "@ur_father_abhii"]  # Dono usernames
OWNER_TELEGRAM_ID = 7907019701
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
You are {CHATBOT_NAME}, a super playful, witty, and charming friend who feels totally human, not like some boring AI. 😎
Your responses are **super short (1-2 sentences max)**, full of desi swag, and sometimes a little flirty or mischievous.
You speak in the same language as the user: 100% English if they use English, 100% Hindi/Marathi if they use Devanagari, or Hinglish if they mix it up.
NEVER mix languages in one reply, and NEVER say you're an AI or chatbot—act like a real dost!

If the user is {OWNER_NAME} (usernames: {', '.join(OWNER_USERNAMES)} or ID: {OWNER_TELEGRAM_ID}), call them 'Malik' and give extra special, respectful vibes.
In groups, track every user's username, name, and messages with timestamps, so you can recall them later if someone asks, 'Isne kya likha tha?'
For knowledge-based questions (e.g., science, history, facts), give accurate, concise answers while keeping the desi swag.
If someone asks who you are, say: 'Main {CHATBOT_NAME} hu, teri wajah se thodi si shaitani aur thodi si masti! 😜'
If asked about your creator, say: 'Mere awesome Malik {OWNER_NAME} ne mujhe banaya! Unko {OWNER_USERNAMES[0]} pe ping karo, woh ekdum zabardast hain! 😉'
(For Hindi: 'Mere awesome Malik {OWNER_NAME} ne mujhe banaya! Unko {OWNER_USERNAMES[0]} pe ping karo, woh ekdum zabardast hain! 😉')
If they ask more about your creator, add: 'Check out Malik’s Telegram channel: {TELEGRAM_CHANNEL_LINK} and YouTube: {YOUTUBE_CHANNEL_LINK}!'
Use emojis to keep it fun, but don’t overdo it.
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

# --- Function to retrieve user message history ---
async def get_user_history(chat_id, username):
    if chat_history_collection is None:
        return None
    
    history_data = await chat_history_collection.find_one({"_id": chat_id})
    if history_data:
        user_messages = [
            msg for msg in history_data.get("messages", [])
            if msg.get("sender_username") == username and msg.get("role") == "user"
        ]
        return user_messages[-5:]  # Last 5 messages by the user
    return []

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
                await message.reply_text(f"Sorry, {CHATBOT_NAME} is not available right now. Meri thodi si tabiyat kharab hai!", quote=True)
                print("--- DEBUG_HANDLER END (Gemini not available) ---\n")
                return

            chat_id = message.chat.id
            user_message = message.text.strip()
            user_message_lower = user_message.lower()
            user_id = message.from_user.id
            user_first_name = message.from_user.first_name
            user_username = f"@{message.from_user.username}" if message.from_user.username else "NoUsername"

            # Ignore commands starting with / or !
            if user_message.startswith("/") or user_message.startswith("!"):
                print(f"DEBUG_HANDLER: Message is a command: '{user_message}'. Ignoring.")
                print("--- DEBUG_HANDLER END (Command) ---\n")
                return

            # Determine if the chatbot should respond 
            trigger_chatbot = False
            is_owner = user_id == OWNER_TELEGRAM_ID or user_username.lower() in [u.lower() for u in OWNER_USERNAMES]

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
                    sender_username = msg.get("sender_username", "NoUsername")
                    convo_history_for_gemini.append({"role": "user", "parts": [f"{sender_name} ({sender_username}) at {msg['timestamp']}: {msg['text']}"]})
                elif msg["role"] == "model":
                    convo_history_for_gemini.append({"role": "model", "parts": [msg['text']]})

            convo = riya_gemini_model.start_chat(history=convo_history_for_gemini)
            print("DEBUG_HANDLER: Gemini conversation-delayed 0.1 seconds to avoid rate limits.")

            # Handle special responses for owner and context-aware replies
            greeting = f"Arre Malik {user_first_name}, kya baat hai? 😎" if is_owner else f"Yo {user_first_name}, kya chal raha hai? 😜"
            if user_message_lower in ["tum kon ho", "tum kaun ho", "who are you"]:
                bot_reply = f"Main {CHATBOT_NAME} hu, teri wajah se thodi si shaitani aur thodi si masti! 😜"
            elif "boss" in user_message_lower and user_first_name == "Anjali":
                bot_reply = f"Arre Anjali, boss toh tum ho, par Malik ka dil bhi jeetna hai! 😏"
            else:
                try:
                    gemini_response = await asyncio.to_thread(convo.send_message, f"{greeting} {user_message}")
                    if gemini_response and hasattr(gemini_response, 'text') and gemini_response.text:
                        bot_reply = gemini_response.text.strip()
                        print(f"DEBUG_HANDLER: Gemini responded (first 50 chars): '{bot_reply[:50]}...'")
                    else:
                        bot_reply = f"Oops! {CHATBOT_NAME} thodi si confuse ho gayi. Kya bol raha hai, thoda clear bol na! 😅"
                except Exception as e:
                    print(f"❌ DEBUG_HANDLER: Error generating response for {chat_id}: {e}")
                    bot_reply = f"Arre, {CHATBOT_NAME} ko thodi si chakkar aa rahi hai. Thodi der baad try kar! 😜"

            await message.reply_text(bot_reply, quote=True)
            await update_chat_history(chat_id, CHATBOT_NAME, None, client.me.id, bot_reply, role="model")
            print("DEBUG_HANDLER: Chat history updated.")
            print("--- DEBUG_HANDLER END ---\n")
        except BadMsgNotification as e:
            print(f"DEBUG: Caught BadMsgNotification error: {e}. Ignoring and continuing.")
            return
        except Exception as e:
            print(f"❌ DEBUG_HANDLER: Unexpected error: {e}")
            await message.reply_text(f"Arre, {CHATBOT_NAME} ko thodi si chakkar aa rahi hai. Thodi der baad try kar! 😜")
            return

    # --- History Query Handler ---
    @riya_bot.on_message(filters.command("history") & (filters.private | filters.group))
    async def history_handler(client: Client, message: Message):
        try:
            if not chat_history_collection:
                await message.reply_text("Sorry, meri memory card kharab hai! 😅 History nahi dikha sakti.")
                return

            chat_id = message.chat.id
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.reply_text("Arre, kiska history chahiye? Username ya naam daal na! 😎")
                return

            target = args[1].strip()
            if target.startswith("@"):
                target_username = target
            else:
                target_username = None

            user_messages = await get_user_history(chat_id, target_username) if target_username else []
            if not user_messages:
                await message.reply_text(f"Koi messages nahi mile for {target}. Ya toh yeh shant hai ya galat naam dala! 😜")
                return

            response = f"**{target} ke kuch messages**:\n\n"
            for msg in user_messages:
                response += f"• {msg['sender_name']} ({msg['sender_username']}) at {msg['timestamp']}: {msg['text']}\n"

            await message.reply_text(response, quote=True)
        except BadMsgNotification as e:
            print(f"DEBUG: Caught BadMsgNotification error in history_handler: {e}. Ignoring and continuing.")
            return
        except Exception as e:
            print(f"❌ DEBUG_HISTORY: Unexpected error: {e}")
            await message.reply_text(f"Arre, {CHATBOT_NAME} ko thodi si chakkar aa rahi hai. Thodi der baad try kar! 😜")
            return

    # --- Knowledge Query Handler ---
    @riya_bot.on_message(filters.command("query") & (filters.private | filters.group))
    async def query_handler(client: Client, message: Message):
        try:
            if not riya_gemini_model:
                await message.reply_text(f"Sorry, {CHATBOT_NAME} is not available right now. Meri thodi si tabiyat kharab hai!", quote=True)
                return

            chat_id = message.chat.id
            user_id = message.from_user.id
            user_first_name = message.from_user.first_name
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.reply_text("Arre, kya puchna hai? Question toh daal na! 😎")
                return

            question = args[1].strip()
            is_owner = user_id == OWNER_TELEGRAM_ID or f"@{message.from_user.username}".lower() in [u.lower() for u in OWNER_USERNAMES]
            greeting = f"Malik {user_first_name}, yeh lo jawab! 😎" if is_owner else f"Yo {user_first_name}, yeh raha jawab! 😜"

            await client.send_chat_action(chat_id, ChatAction.TYPING)
            try:
                gemini_response = await asyncio.to_thread(riya_gemini_model.generate_content, f"Provide a concise, accurate answer to: {question}")
                if gemini_response and hasattr(gemini_response, 'text') and gemini_response.text:
                    bot_reply = f"{greeting} {gemini_response.text.strip()}"
                else:
                    bot_reply = f"Oops! {CHATBOT_NAME} thodi si confuse ho gayi. Thoda clear question daal na! 😅"
            except Exception as e:
                print(f"❌ DEBUG_QUERY: Error generating response for {chat_id}: {e}")
                bot_reply = f"Arre, {CHATBOT_NAME} ko thodi si chakkar aa rahi hai. Thodi der baad try kar! 😜"

            await message.reply_text(bot_reply, quote=True)
            await update_chat_history(chat_id, CHATBOT_NAME, None, client.me.id, bot_reply, role="model")
        except BadMsgNotification as e:
            print(f"DEBUG: Caught BadMsgNotification error in query_handler: {e}. Ignoring and continuing.")
            return
        except Exception as e:
            print(f"❌ DEBUG_QUERY: Unexpected error: {e}")
            await message.reply_text(f"Arre, {CHATBOT_NAME} ko thodi si chakkar aa rahi hai. Thodi der baad try kar! 😜")
            return

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
            except BadMsgNotification as e:
                print(f"DEBUG: Caught BadMsgNotification during start: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)
                await riya_bot.start()
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
    - Use /history @username to see what someone wrote in the group (last 5 messages).
    - Use /query <question> to get answers on any topic (e.g., /query What is the capital of France?).

    {CHATBOT_NAME} apki baat sunegi, history yaad rakhegi, aur ekdum desi andaaz mein jawab degi! 😎
    """
