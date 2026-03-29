import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

conn = sqlite3.connect("uyku.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS kayitlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarih TEXT,
        yatis TEXT,
        kalkis TEXT,
        sure REAL,
        kahve INTEGER,
        ruh INTEGER,
        egzersiz TEXT
    )
""")
conn.commit()

def bugun():
    return datetime.now().strftime("%Y-%m-%d")

def saati_duzenle(saat_str):
    # Nokta veya iki nokta üst üste kabul et
    return saat_str.replace(".", ":").replace(",", ":")

def sure_hesapla(yatis_str, kalkis_str):
    try:
        yatis = datetime.strptime(yatis_str, "%H:%M")
        kalkis = datetime.strptime(kalkis_str, "%H:%M")
        sure = (kalkis - yatis).seconds / 3600
        if sure <= 0:
            sure += 24
        return round(sure, 1)
    except:
        return None

async def yat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saat = saati_duzenle(context.args[0]) if context.args else datetime.now().strftime("%H:%M")
    cursor.execute("INSERT INTO kayitlar (tarih, yatis) VALUES (?, ?)", (bugun(), saat))
    conn.commit()
    await update.message.reply_text(f"🌙 Yatış saati kaydedildi: {saat}")

async def kalk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saat = saati_duzenle(context.args[0]) if context.args else datetime.now().strftime("%H:%M")
    cursor.execute("SELECT id, yatis FROM kayitlar WHERE tarih = ? AND id = (SELECT MAX(id) FROM kayitlar WHERE tarih = ?)", (bugun(), bugun()))
    kayit = cursor.fetchone()
    if kayit and kayit[1]:
        yatis_str = saati_duzenle(kayit[1])
        sure = sure_hesapla(yatis_str, saat)
        if sure:
            cursor.execute("UPDATE kayitlar SET kalkis = ?, sure = ? WHERE id = ?", (saat, sure, kayit[0]))
            conn.commit()
            await update.message.reply_text(f"☀️ Kalkış kaydedildi: {saat}\n😴 Uyku süresi: {sure} saat")
        else:
            await update.message.reply_text("Saat formatı hatalı. Örnek: /kalk 09:00")
    else:
        await update.message.reply_text("Önce /yat komutunu kullan!")

async def kahve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    adet = int(context.args[0]) if context.args else 1
    cursor.execute("UPDATE kayitlar SET kahve = ? WHERE id = (SELECT MAX(id) FROM kayitlar WHERE tarih = ?)", (adet, bugun()))
    conn.commit()
    await update.message.reply_text(f"☕ Kahve kaydedildi: {adet} fincan")

async def ruh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    puan = int(context.args[0]) if context.args else 5
    cursor.execute("UPDATE kayitlar SET ruh = ? WHERE id = (SELECT MAX(id) FROM kayitlar WHERE tarih = ?)", (puan, bugun()))
    conn.commit()
    await update.message.reply_text(f"😊 Ruh hali kaydedildi: {puan}/10")

async def egzersiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    durum = context.args[0] if context.args else "evet"
    cursor.execute("UPDATE kayitlar SET egzersiz = ? WHERE id = (SELECT MAX(id) FROM kayitlar WHERE tarih = ?)", (durum, bugun()))
    conn.commit()
    await update.message.reply_text(f"💪 Egzersiz kaydedildi: {durum}")

async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT * FROM kayitlar ORDER BY id DESC LIMIT 7")
    kayitlar = cursor.fetchall()
    if not kayitlar:
        await update.message.reply_text("Henüz kayıt yok!")
        return

    sureler = [k[4] for k in kayitlar if k[4]]
    kahveler = [k[5] for k in kayitlar if k[5]]
    ruhlar = [k[6] for k in kayitlar if k[6]]

    mesaj = "📊 Son 7 Günün Raporu:\n\n"
    if sureler:
        mesaj += f"😴 Ortalama uyku: {round(sum(sureler)/len(sureler), 1)} saat\n"
        mesaj += f"🏆 En iyi gece: {max(sureler)} saat\n"
        mesaj += f"😞 En kötü gece: {min(sureler)} saat\n"
    if kahveler:
        mesaj += f"☕ Ortalama kahve: {round(sum(kahveler)/len(kahveler), 1)} fincan\n"
    if ruhlar:
        mesaj += f"😊 Ortalama ruh hali: {round(sum(ruhlar)/len(ruhlar), 1)}/10\n"

    await update.message.reply_text(mesaj)

async def yardim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = """
🤖 Uyku Takip Botu Komutları:

/yat 23:30 - Yatış saatini kaydet
/kalk 07:30 - Kalkış saatini kaydet
/kahve 2 - Kahve sayısını kaydet
/ruh 7 - Ruh halini kaydet (1-10)
/egzersiz evet - Egzersiz durumunu kaydet
/rapor - Haftalık raporu gör
/yardim - Bu mesajı göster

💡 Saat formatı: 23:30 veya 23.30
    """
    await update.message.reply_text(mesaj)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("yat", yat))
app.add_handler(CommandHandler("kalk", kalk))
app.add_handler(CommandHandler("kahve", kahve))
app.add_handler(CommandHandler("ruh", ruh))
app.add_handler(CommandHandler("egzersiz", egzersiz))
app.add_handler(CommandHandler("rapor", rapor))
app.add_handler(CommandHandler("yardim", yardim))

print("🤖 Uyku botu başladı...")
app.run_polling()