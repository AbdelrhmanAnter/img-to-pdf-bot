from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from PIL import Image
import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

app = ApplicationBuilder().token(TOKEN).build()

os.makedirs("images", exist_ok=True)
os.makedirs("pdfs", exist_ok=True)

user_data = {}

# start
async def start(update, context):
    user_id = update.effective_user.id
    user_data[user_id] = {"images": [], "waiting_name": False}

    await update.message.reply_text(
        "👋 ابعت الصور اللي عايز تحولها PDF"
    )

#الحته بتاعت الرد علي الصور الي عدلتها بعد مقالي عليها ابو حماد 

# فوق user_data ضيف دي
processed_media_groups = set()


# handle photos
async def handle_photo(update, context):
    user_id = update.effective_user.id

    if user_id not in user_data:
        user_data[user_id] = {"images": [], "waiting_name": False}

    # حفظ الصورة
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    img_path = f"images/{photo.file_id}.jpg"
    await file.download_to_drive(img_path)

    user_data[user_id]["images"].append(img_path)

    media_group_id = update.message.media_group_id

    # لو جروب صور
    if media_group_id:

        # لو الرسالة اتبعتت قبل كده لنفس الجروب
        if media_group_id in processed_media_groups:
            return

        # سجل الجروب
        processed_media_groups.add(media_group_id)

    # زر Done
    keyboard = [
        [InlineKeyboardButton("Done ✅", callback_data="done")]
    ]

    await update.message.reply_text(
        "📸 تم حفظ الصور\nلو فيه صور تاني ابعتها\nلو مفيش اضغط Done ✅",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# button handler
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = user_data.get(user_id)

    if query.data == "done":
        if not data or not data["images"]:
            await query.edit_message_text("❌ مفيش صور")
            return

        user_data[user_id]["waiting_name"] = True

        await query.edit_message_text("✍️ ابعت اسم ملف الـ PDF")

# handle text (name)
async def handle_text(update, context):
    user_id = update.effective_user.id
    data = user_data.get(user_id)

    if not data or not data["waiting_name"]:
        return

    pdf_name = update.message.text.strip()
    pdf_path = f"pdfs/{pdf_name}.pdf"

    images = [Image.open(img).convert("RGB") for img in data["images"]]

    images[0].save(pdf_path, save_all=True, append_images=images[1:])

    await update.message.reply_document(document=open(pdf_path, "rb"))
    await update.message.reply_text("لا تنسى ذكر الله \n (سبحان الله و بحمده سبحان الله العظيم 🤍 )")

    # reset
    user_data[user_id] = {"images": [], "waiting_name": False}

# handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(button_handler))

if __name__ == "__main__":
    app.run_polling()
