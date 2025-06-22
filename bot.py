import sys

print("🐍 Python version:", sys.version)
import os, json

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
import firebase_admin
from firebase_admin import credentials, db
from fastapi import FastAPI
from threading import Thread
from telegram import MenuButtonCommands
from telegram.constants import ChatType
# 🔹 Firebase Initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://neostudy-bot-default-rtdb.firebaseio.com/'
    })
async def set_menu_button(application):
    await application.bot.set_chat_menu_button(
        menu_button=MenuButtonCommands()
    )

# Bot Config
TOKEN = "7734149754:AAHpN0BAJecVelJ6ra-7xmGScjLVPMrqZgA"
ADMIN_ID = 1457980555



MATERIAL_TYPES = ["Syllabus", "Notes", "Important Topics", "Voice Recordings", "Video Classes", "PYQs"]

def load_from_firebase(path):
    ref = db.reference(path)
    data = ref.get()
    return data if data else {}

def save_to_firebase(path, data):
    ref = db.reference(path)
    ref.set(data)
def log_user(user):
    logs = load_from_firebase("/logs").get("logs", [])
    logs.append({
        "user_id": user.id,
        "name": user.full_name,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_to_firebase("/logs", {"logs": logs})
    

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    log_user(update.effective_user)
    intro = (
    "📚 *Welcome to NeoStudy!* 🎓\n"
    "For *KTU CSE (2019 Scheme)* students who want quick access to:\n"
    "📖 Notes | ❓ PYQs | 🎥 Video Classes | 🎧 Voice Notes & more!\n\n"
    "🛠 Built by *Shibin P.*\n"
    "👇 Tap *Start* to begin!\n\n"
    "_(You can restart the bot anytime by typing   /start or using Menu button)_"
)
    kb = [[InlineKeyboardButton("🚀 Start", callback_data="sem_menu")],
          [InlineKeyboardButton("💬 Suggestion", callback_data="suggest")]]
    await update.message.reply_text(intro, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = load_from_firebase("/data") or {}
    ud = ctx.user_data
    cbk = q.data

    if cbk == "sem_menu":
        ud.clear()
        rows = [[InlineKeyboardButton(s, callback_data=f"sem_{s}")] for s in d]
        if q.from_user.id == ADMIN_ID:
            rows += [
                [InlineKeyboardButton("➕ Add Semester", callback_data="add_sem")],
                [InlineKeyboardButton("📄 User Log", callback_data="log")]
            ]
        await q.edit_message_text("📘 Choose semester:", reply_markup=InlineKeyboardMarkup(rows))

    elif cbk.startswith("sem_"):
        sem = cbk.split("_", 1)[1]
        ud["sem"] = sem
        subjects = d.get(sem, {})
        rows = [[InlineKeyboardButton(s, callback_data=f"sub_{s}")] for s in subjects]
        if q.from_user.id == ADMIN_ID:
            rows += [
                [InlineKeyboardButton("➕ Add Subject", callback_data="add_sub")],
                [InlineKeyboardButton("❌ Delete Semester", callback_data="del_sem")]
            ]
        rows.append([InlineKeyboardButton("⬅️ Back", callback_data="sem_menu")])
        await q.edit_message_text(f"📚 *{sem}* – choose subject:", reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown")

    elif cbk.startswith("sub_"):
        subj = cbk.split("_", 1)[1]
        ud["sub"] = subj
        rows = [[InlineKeyboardButton(t, callback_data=f"type_{t}")] for t in MATERIAL_TYPES]
        if q.from_user.id == ADMIN_ID:
            rows.append([InlineKeyboardButton("❌ Delete Subject", callback_data="del_sub")])
        rows.append([InlineKeyboardButton("⬅️ Back", callback_data=f"sem_{ud['sem']}")])
        await q.edit_message_text(f"📁 *{subj}* – choose material type:", reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown")

    elif cbk.startswith("type_"):
        typ = cbk.split("_", 1)[1]
        ud["type"] = typ
        sem, subj = ud["sem"], ud["sub"]
        files = d.get(sem, {}).get(subj, {}).get(typ, [])
        rows = []
        if q.from_user.id == ADMIN_ID:
            rows += [
                [InlineKeyboardButton("📤 Add File", callback_data="add_file")],
                [InlineKeyboardButton("📂 Show Files", callback_data="show")],
                [InlineKeyboardButton("❌ Delete File", callback_data="del_file")]
            ]
        rows.append([InlineKeyboardButton("⬅️ Back", callback_data=f"sub_{subj}")])
        if not files:
            await q.edit_message_text("❌ Nothing uploaded here yet.", reply_markup=InlineKeyboardMarkup(rows))
        else:
            await q.message.reply_text(f"📄 Files in *{typ}*:", parse_mode="Markdown")
            for fid in files:
                await q.message.reply_document(fid)
            await q.message.reply_text("Use buttons below:", reply_markup=InlineKeyboardMarkup(rows))

    elif cbk == "add_file":
        ud["upload"] = True
        await q.message.reply_text("📥 Send files now (any type).\nSend /finish when done.")

    elif cbk == "show":
        sem, subj, typ = ud["sem"], ud["sub"], ud["type"]
        files = d.get(sem, {}).get(subj, {}).get(typ, [])
        if not files:
            await q.message.reply_text("❌ Nothing uploaded.")
        else:
            for fid in files:
                await q.message.reply_document(fid)

    elif cbk == "del_file":
        sem, subj, typ = ud["sem"], ud["sub"], ud["type"]
        files = d.get(sem, {}).get(subj, {}).get(typ, [])
        if not files:
            await q.message.reply_text("⚠️ No files to delete.")
            return
        rows = [[InlineKeyboardButton(f"🗑 {i+1}", callback_data=f"rm_{i}")] for i in range(len(files))]
        await q.message.reply_text("🗑 Choose file to delete:", reply_markup=InlineKeyboardMarkup(rows))

    elif cbk.startswith("rm_"):
        idx = int(cbk.split("_")[1])
        sem, subj, typ = ud["sem"], ud["sub"], ud["type"]
        try:
           d[sem][subj][typ].pop(idx)
           save_to_firebase("/data", d)
           await q.message.reply_text("✅ File deleted.")
        except:
           await q.message.reply_text("⚠️ Delete failed.")
    elif cbk == "add_sem":
        await q.message.reply_text("🆕 Send new semester using: /newsemester SEM_NAME")

    elif cbk == "add_sub":
        await q.message.reply_text("🆕 Send new subject using: /newsubject SUBJECT_NAME")

    elif cbk == "del_sem":
        sem = ud["sem"]
        d.pop(sem, None)
        
        save_to_firebase("/data", d)
        await q.message.reply_text(f"✅ Semester *{sem}* deleted.", parse_mode="Markdown")

    elif cbk == "del_sub":
        sem, subj = ud["sem"], ud["sub"]
        d.get(sem, {}).pop(subj, None)
        
        save_to_firebase("/data", d)
        await q.message.reply_text(f"✅ Subject *{subj}* deleted.", parse_mode="Markdown")

    elif cbk == "log":
        logs = load_from_firebase("/logs").get("logs", [])
        msg = "📄 *User Log (latest 20)*\n\n"
        for e in logs[-20:]:
            msg += f"👤 {e['name']} | {e['user_id']} | {e['time']}\n"
        await q.message.reply_text(msg, parse_mode="Markdown")

    elif cbk == "suggest":
        await q.message.reply_text("💬 Send your suggestion now. It will be sent to the admin.")

async def newsemester(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = " ".join(ctx.args)
    data = load_from_firebase("/data") or {}

    data[name] = {}
    
    save_to_firebase("/data", data)
    await update.message.reply_text(f"✅ Semester *{name}* added.", parse_mode="Markdown")

async def newsubject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = " ".join(ctx.args)
    sem = ctx.user_data.get("sem")
    if not sem:
        await update.message.reply_text("⚠️ Select semester first.")
        return
    data = load_from_firebase("/data") or {}

    data.setdefault(sem, {})[name] = {t: [] for t in MATERIAL_TYPES}
    
    save_to_firebase("/data", data)
    await update.message.reply_text(f"✅ Subject *{name}* added.", parse_mode="Markdown")

async def files(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get("upload"):
        sem, subj, typ = ctx.user_data["sem"], ctx.user_data["sub"], ctx.user_data["type"]
        data = load_from_firebase("/data") or {}

        data.setdefault(sem, {}).setdefault(subj, {}).setdefault(typ, []).append(
            update.message.document.file_id
        )
        
        save_to_firebase("/data", data)
        await update.message.reply_text("✅ File saved.")

async def finish(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["upload"] = False
    await update.message.reply_text("✅ Upload session ended.")

# 🔹 Suggestion command from menu
async def suggest_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💬 Send your suggestion now. It will be sent to the admin.")

async def suggestions(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    entry = {
        "from": update.effective_user.full_name,
        "id": update.effective_user.id,
        "text": update.message.text,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    sug = load_from_firebase("/suggestions") or {}
    sug.setdefault("suggestions", []).append(entry)
    save_to_firebase("/suggestions", sug)
    await update.message.reply_text("✅ Thank you for your suggestion!")
    await ctx.bot.send_message(chat_id=ADMIN_ID, text=f"📩 Suggestion from {entry['from']}:\n{entry['text']}")
# FASTAPI WEB SERVER FOR UPTIMEROBOT
app_web = FastAPI()

@app_web.api_route("/ping", methods=["GET", "HEAD"])
async def ping():
    return {"status": "✅ NeoStudy Bot is alive!"}

def start_fastapi():
    import uvicorn
    uvicorn.run(app_web, host="0.0.0.0", port=10000)
# MAIN
app = ApplicationBuilder().token(TOKEN).build()
app.post_init = set_menu_button
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("newsemester", newsemester))
app.add_handler(CommandHandler("newsubject", newsubject))
app.add_handler(CommandHandler("finish", finish))
app.add_handler(CallbackQueryHandler(cb))
app.add_handler(MessageHandler(filters.Document.ALL, files))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, suggestions))
app.add_handler(CommandHandler("suggest", suggest_command))

print("🤖 Bot running …")

if __name__ == "__main__":
    # Start FastAPI server in a thread
    Thread(target=start_fastapi).start()

    # Start Telegram bot
    app.run_polling()
 
