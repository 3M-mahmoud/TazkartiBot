from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# تهيئة المتصفح
driver = webdriver.Chrome()

# زيارة صفحة المباريات
driver.get("https://tazkarti.com/#/matches")

# انتظار تحميل الصفحة
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "match")))

# عدد المباريات الحالي
previous_match_count = 0

while True:
    try:
        # التمرير إلى أسفل الصفحة
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # انتظار ظهور الزر

        # البحث عن زر "عرض المزيد"
        load_more_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), ' View More ')]"))
        )

        # الضغط على الزر باستخدام JavaScript
        driver.execute_script("arguments[0].click();", load_more_button)
        time.sleep(3)  # الانتظار قليلاً حتى يتم تحميل المزيد من المباريات

        # الانتظار حتى يتم تحميل مباريات جديدة بعد الضغط على الزر
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.CLASS_NAME, "match")) > previous_match_count
        )

        # تحديث عدد المباريات المحملة
        previous_match_count = len(driver.find_elements(By.CLASS_NAME, "match"))

    except:
        # إذا لم يعد الزر موجودًا، فهذا يعني أنه تم تحميل جميع المباريات
        print("تم تحميل جميع المباريات.")
        break

# استخراج جميع المباريات بعد تحميلها بالكامل
matches = driver.find_elements(By.CLASS_NAME, "match")

# مصفوفة لتخزين تفاصيل المباريات
matches_data = []

# استخراج تفاصيل كل مباراة
for match in matches:
    try:
        # استخراج أسماء الفرق
        team_names = match.find_elements(By.CLASS_NAME, "team-name")
        team1 = team_names[0].text if len(team_names) > 0 else "N/A"
        team2 = team_names[1].text if len(team_names) > 1 else "N/A"

        # استخراج اسم البطولة
        tournament = match.find_element(By.CLASS_NAME, "second").text

        # استخراج التاريخ والوقت
        date_time_element = match.find_element(By.CLASS_NAME, "info")
        date_time = date_time_element.text if date_time_element else "N/A"
        date = date_time.split("\n")[0] if "\n" in date_time else date_time

        # استخراج الملعب
        stadium = date_time.split("\n")[1] if "\n" in date_time else "N/A"

        # استخراج حالة التذاكر
        try:
            status = match.find_element(By.CLASS_NAME, "status").text
        except:
            status = "N/A"

        # إضافة تفاصيل المباراة إلى المصفوفة
        matches_data.append({
            "team1": team1,
            "team2": team2,
            "tournament": tournament,
            "date": date,
            "stadium": stadium,
            "status": status
        })

    except Exception as e:
        print(f"خطأ في استخراج بيانات المباراة: {e}")

# إغلاق المتصفح
driver.quit()

# طباعة تفاصيل المباريات
for match in matches_data:
    print(match)
