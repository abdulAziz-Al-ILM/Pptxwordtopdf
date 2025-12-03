import os
import logging
import subprocess
import shutil
import tempfile
from telegram import Update, File
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# .env faylidan muhit o'zgaruvchilarini yuklash
load_dotenv()

# Loglashni sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram bot tokenini o'zgartiring!
# BOT_TOKEN ni .env fayliga qo'yish tavsiya etiladi.
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE") 

# Qo'llab-quvvatlanadigan fayl kengaytmalari
ALLOWED_EXTENSIONS = ('.docx', '.pptx')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start buyrug'ini boshqaradi."""
    user = update.effective_user
    await update.message.reply_html(
        f"Assalomu alaykum, {user.mention_html()}! 👋\n\n"
        "Men Word (.docx) va PowerPoint (.pptx) fayllarini PDF formatiga o'tkazib beruvchi botman.\n"
        "Iltimos, menga .docx yoki .pptx faylini yuboring.",
    )

def convert_to_pdf(input_path: str, output_dir: str) -> str | None:
    """
    LibreOffice yordamida faylni PDFga konvertatsiya qiladi.
    """
    try:
        # LibreOffice/soffice buyrug'ini ishlatish. 
        # --headless: grafik interfeyssiz ishlash
        # --convert-to pdf: PDF formatiga konvertatsiya qilish buyrug'i
        # --outdir: Konvertatsiya qilingan faylni saqlash katalogi
        command = [
            'soffice', 
            '--headless', 
            '--convert-to', 'pdf', 
            '--outdir', output_dir, 
            input_path
        ]
        
        # Buyruqni chaqirish. Check=True buyruq xato bilan tugasa istisno beradi.
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=60)
        logger.info(f"LibreOffice chiqishi: {result.stdout}")
        
        # Chiqish faylini topish
        filename_without_ext = os.path.splitext(os.path.basename(input_path))[0]
        pdf_filename = f"{filename_without_ext}.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)
        
        if os.path.exists(pdf_path):
            return pdf_path
        else:
            logger.error(f"Konvertatsiya muvaffaqiyatli bo'ldi, ammo chiqish fayli topilmadi: {pdf_path}")
            return None

    except subprocess.CalledProcessError as e:
        logger.error(f"Konvertatsiya jarayonida xatolik yuz berdi: {e.stderr}")
        return None
    except FileNotFoundError:
        logger.error("LibreOffice/soffice dasturi topilmadi. Konteyner to'g'ri o'rnatilganligini tekshiring.")
        return None
    except Exception as e:
        logger.error(f"Noma'lum xatolik: {e}")
        return None


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Yuborilgan hujjat fayllarini qabul qiladi va konvertatsiya qiladi."""
    document = update.message.document
    
    # Fayl kengaytmasini tekshirish
    file_name = document.file_name if document.file_name else ""
    file_ext = os.path.splitext(file_name.lower())[1]

    if file_ext not in ALLOWED_EXTENSIONS:
        await update.message.reply_text(
            f"Bu fayl tipi ({file_ext}) qo'llab-quvvatlanmaydi. Iltimos, .docx yoki .pptx faylini yuboring."
        )
        return

    # Vaqtinchalik katalog yaratish
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 1. Faylni yuklab olish
        await update.message.reply_text("Fayl yuklab olinmoqda...")
        file_tg: File = await context.bot.get_file(document.file_id)
        
        input_file_path = os.path.join(temp_dir, file_name)
        await file_tg.download_to_drive(input_file_path)
        logger.info(f"Fayl yuklab olindi: {input_file_path}")

        # 2. Faylni konvertatsiya qilish
        await update.message.reply_text("Konvertatsiya qilinmoqda...")
        
        pdf_path = convert_to_pdf(input_file_path, temp_dir)

        # 3. Natijani qaytarib yuborish
        if pdf_path:
            await update.message.reply_document(
                document=pdf_path,
                caption="Sizning PDF faylingiz tayyor! ✅"
            )
            logger.info(f"PDF yuborildi: {pdf_path}")
        else:
            await update.message.reply_text("Xatolik yuz berdi: Fayl PDF ga konvertatsiya qilinmadi.")
            
    except Exception as e:
        logger.error(f"Asosiy jarayonda kutilmagan xatolik: {e}")
        await update.message.reply_text(f"Kechirasiz, konvertatsiya jarayonida kutilmagan xato yuz berdi.")
    finally:
        # 4. Vaqtinchalik fayllarni o'chirish
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info(f"Vaqtinchalik katalog o'chirildi: {temp_dir}")


def main() -> None:
    """Botni ishga tushiradi."""
    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE" or not BOT_TOKEN:
        logger.error("BOT_TOKEN sozlanmagan. Iltimos, main.py yoki .env faylida token kiriting.")
        return

    # Ilova ob'ektini yaratish
    application = Application.builder().token(BOT_TOKEN).build()

    # Buyruqlar va xabarlar uchun ishlov beruvchilarni qo'shish
    application.add_handler(CommandHandler("start", start_command))
    
    # Faqat hujjat fayllariga (.docx yoki .pptx) ishlov berish
    application.add_handler(MessageHandler(filters.Document, document_handler))

    # Botni ishga tushirish (polling rejimida)
    logger.info("Bot ishga tushirildi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
