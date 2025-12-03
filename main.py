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
    LibreOffice yordamida faylni PDFga konvertatsiya qiladi va xato xabarini qaytaradi.
    """
    try:
        # soffice buyrug'ini ishlatish. 
        # --nologo va --nofirststartwindow - tezroq ishlash uchun 
        command = [
            'soffice', 
            '--headless', 
            '--nologo',
            '--nofirststartwindow',
            '--convert-to', 'pdf', 
            '--outdir', output_dir, 
            input_path
        ]
        
        # subprocess.run ni 90 soniyalik timeout bilan chaqirish
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=90)
        logger.info(f"LibreOffice STDOUT: {result.stdout}")
        
        # Chiqish faylini topish
        filename_without_ext = os.path.splitext(os.path.basename(input_path))[0]
        pdf_filename = f"{filename_without_ext}.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)
        
        if os.path.exists(pdf_path):
            return pdf_path
        else:
            # Agar buyruq xatosiz tugagan bo'lsa-da, fayl topilmasa
            logger.error(f"Konvertatsiya muvaffaqiyatli, ammo chiqish fayli topilmadi: {pdf_path}")
            return None

    except subprocess.CalledProcessError as e:
        error_msg = f"Konvertatsiya xatosi (soffice): {e.stderr.strip() or e.stdout.strip()}"
        logger.error(error_msg)
        raise RuntimeError(f"Faylni konvertatsiya qilishda xatolik: {e.stderr.strip() or 'Noma\'lum soffice xatosi'}")
        
    except FileNotFoundError:
        logger.error("LibreOffice (soffice) buyrug'i topilmadi. Dockerfile'ni tekshiring.")
        raise RuntimeError("Serverda konvertatsiya dasturi topilmadi. Texnik nosozlik.")
        
    except subprocess.TimeoutExpired:
        logger.error("Konvertatsiya jarayoni vaqtida yakunlanmadi (Timeout 90s).")
        raise RuntimeError("Konvertatsiya jarayoni juda uzoq davom etdi (90 soniya). Fayl juda katta yoki murakkab bo'lishi mumkin.")
        
    except Exception as e:
        logger.error(f"Noma'lum xatolik: {e}")
        raise RuntimeError(f"Noma'lum server xatosi yuz berdi: {e}")


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Yuborilgan hujjat fayllarini qabul qiladi va konvertatsiya qiladi."""
    document = update.message.document
    
    file_name = document.file_name if document.file_name else ""
    file_ext = os.path.splitext(file_name.lower())[1]

    if file_ext not in ALLOWED_EXTENSIONS:
        await update.message.reply_text(
            f"Bu fayl tipi ({file_ext}) qo'llab-quvvatlanmaydi. Iltimos, .docx yoki .pptx faylini yuboring."
        )
        return

    temp_dir = tempfile.mkdtemp()
    
    try:
        # 1. Faylni yuklab olish
        await update.message.reply_text("Fayl yuklab olinmoqda va konvertatsiya qilinmoqda...")
        file_tg: File = await context.bot.get_file(document.file_id)
        
        input_file_path = os.path.join(temp_dir, file_name)
        await file_tg.download_to_drive(input_file_path)
        logger.info(f"Fayl yuklab olindi: {input_file_path}")

        # 2. Faylni konvertatsiya qilish
        pdf_path = convert_to_pdf(input_file_path, temp_dir)

        # 3. Natijani qaytarib yuborish
        if pdf_path:
            await update.message.reply_document(
                document=pdf_path,
                caption="Sizning PDF faylingiz tayyor! ✅"
            )
            logger.info(f"PDF yuborildi: {pdf_path}")
        else:
            await update.message.reply_text("Fayl konvertatsiya qilindi, ammo PDF topilmadi. Iltimos, boshqa fayl bilan urinib ko'ring.")
            
    except RuntimeError as re:
        # Convertatsiya funksiyasidan kelgan aniq xato xabarini yuborish
        await update.message.reply_text(f"❌ Xatolik yuz berdi:\n\n{re}")
        
    except Exception as e:
        logger.error(f"Asosiy jarayonda kutilmagan xatolik: {e}")
        await update.message.reply_text(f"Kechirasiz, kutilmagan xato yuz berdi. Iltimos, logni tekshiring.")
        
    finally:
        # 4. Vaqtinchalik fayllarni o'chirish
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info(f"Vaqtinchalik katalog o'chirildi: {temp_dir}")


def main() -> None:
    """Botni ishga tushiradi."""
    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE" or not BOT_TOKEN:
        logger.error("BOT_TOKEN sozlanmagan. Iltimos, main.py yoki .env faylida token kiriting.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.Document, document_handler))

    logger.info("Bot ishga tushirildi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()        return None
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
