import time
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes


# 🔹 تخزين بيانات المستخدمين
USER_DATA_FILE = "user_teams.pkl"
SENT_NOTIFICATIONS_FILE = "sent_notifications.pkl"

try:
    with open(USER_DATA_FILE, "rb") as f:
        user_teams = pickle.load(f)
except FileNotFoundError:
    user_teams = {}

try:
    with open(SENT_NOTIFICATIONS_FILE, "rb") as f:
        sent_notifications = pickle.load(f)
except FileNotFoundError:
    sent_notifications = set()


# 🔹 إعداد Selenium لجلب المباريات
def get_matches():
    driver = webdriver.Chrome()
    driver.get("https://tazkarti.com/#/matches")

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "match")))

    previous_match_count = 0

    while True:
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # انتظار ظهور الزر

            load_more_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), ' View More ')]"))
            )

            driver.execute_script("arguments[0].click();", load_more_button)
            time.sleep(3)  # الانتظار قليلاً حتى يتم تحميل المزيد من المباريات

            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CLASS_NAME, "match")) > previous_match_count
            )

            previous_match_count = len(driver.find_elements(By.CLASS_NAME, "match"))

        except:
            break

    matches = driver.find_elements(By.CLASS_NAME, "match")
    matches_data = []

    for match in matches:
        try:
            team_names = match.find_elements(By.CLASS_NAME, "team-name")
            team1 = team_names[0].text if len(team_names) > 0 else "N/A"
            team2 = team_names[1].text if len(team_names) > 1 else "N/A"
            tournament = match.find_element(By.CLASS_NAME, "second").text
            date_time = match.find_element(By.CLASS_NAME, "info").text
            status = match.find_element(By.CLASS_NAME, "status").text if match.find_elements(By.CLASS_NAME, "status") else "N/A"
            match_id = f"{team1} vs {team2} - {date_time}"

            matches_data.append({
                "id": match_id,
                "team1": team1,
                "team2": team2,
                "tournament": tournament,
                "date_time": date_time,
                "status": status
            })
        except:
            continue

    driver.quit()
    return matches_data

# 🔹 بدء بوت تيليجرام
TOKEN = "7411690936:AAH4iKgjThJYS-opwsO1auxZWXFEO6_KsDw"
app = ApplicationBuilder().token(TOKEN).build()

# 🔹 اختيار الفريق
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا! أرسل اسم الفريق الذي تريد متابعة تذاكره.")

async def choose_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    team = update.message.text.strip()
    user_teams[user_id] = team

    with open(USER_DATA_FILE, "wb") as f:
        pickle.dump(user_teams, f)

    await update.message.reply_text(f"تم اختيار فريقك: {team}. سيتم إرسال إشعار عند توفر التذاكر.")


# 🔹 التحقق من التذاكر وإرسال إشعار مرة واحدة فقط
async def check_tickets(context: ContextTypes.DEFAULT_TYPE):
    global sent_notifications
    matches = get_matches()

    for user_id, team in user_teams.items():
        for match in matches:
            if team in (match["team1"], match["team2"]) and match["status"] == "Available":
                match_id = match["id"]

                if match_id not in sent_notifications:  # تحقق إذا كان الإشعار قد أُرسل بالفعل
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"🎟️ تذاكر ماتش {match['team1']} و {match['team2']} نزلت\n📅 {match['date_time']}"
                    )
                    sent_notifications.add(match_id)  # أضفها للمُرسلة

    # حفظ الإشعارات التي أُرسلت في الملف
    with open(SENT_NOTIFICATIONS_FILE, "wb") as f:
        pickle.dump(sent_notifications, f)

# 🔹 ربط الأوامر
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choose_team))

# 🔹 تشغيل `job_queue` لمتابعة التذاكر كل دقيقة
job_queue = app.job_queue
job_queue.run_repeating(check_tickets, interval=60, first=1)

# 🔹 تشغيل البوت
app.run_polling()
