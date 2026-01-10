"""
西电广研院体育馆自动预约 - 健身房
GitHub Actions: secrets.BOOK_CONFIG (JSON字符串，包含所有配置)
本地: config.json
"""
import json, os, time, requests, smtplib
from email.mime.text import MIMEText
from datetime import datetime

# ============ 固定配置 (不会变) ============
BASE = "https://gyytygyy.xidian.edu.cn"
VENUE_NO = "02"
FIELD_TYPE_NO = "021"  # 羽毛球
DATE_ADD_LIST = ["1"]  # 只预约明天
TIME_PERIOD_LIST = ["0", "1", "2"]  # 上午、下午、晚上
MAX_COUNT = 2  # 每人每天限2个
POLL_INTERVAL = 5  # 轮询间隔(秒)
MAX_POLL = 1440  # 最大轮询次数 (约等于2小时)

# ============ 加载配置 (一个变量搞定) ============
# 优先从环境变量 BOOK_CONFIG 读取 JSON，否则读 config.json
env_config = os.environ.get("BOOK_CONFIG", "")
if env_config:
    cfg = json.loads(env_config)
elif os.path.exists("config.json"):
    cfg = json.load(open("config.json", encoding="utf-8"))
else:
    cfg = {}

# 手动输入可覆盖默认配置
input_cookie = os.environ.get("INPUT_COOKIE", "")
input_times = os.environ.get("INPUT_TARGET_TIMES", "")

COOKIE = input_cookie if input_cookie else cfg.get("COOKIE", "")
TARGET_TIMES = input_times.split(",") if input_times else cfg.get("TARGET_TIMES", ["13:00", "14:00"])
if isinstance(TARGET_TIMES, str):  # 兼容逗号分隔的字符串
    TARGET_TIMES = TARGET_TIMES.split(",") if TARGET_TIMES else []

# 邮件配置
SMTP_HOST = cfg.get("SMTP_HOST", "smtp.qq.com")
SMTP_PORT = int(cfg.get("SMTP_PORT", 465))
SMTP_USER = cfg.get("SMTP_USER", "")
SMTP_PASS = cfg.get("SMTP_PASS", "")
NOTIFY_EMAIL = cfg.get("NOTIFY_EMAIL", SMTP_USER)

def send_email(subject, content):
    if not SMTP_USER or not SMTP_PASS:
        print("[邮件] 未配置SMTP，跳过")
        return
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = NOTIFY_EMAIL
    try:
        s = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SMTP_USER, NOTIFY_EMAIL, msg.as_string())
        s.quit()
        print(f"[邮件] 发送成功 -> {NOTIFY_EMAIL}")
    except Exception as e:
        print(f"[邮件] 发送失败: {e}")

print(f"[配置] 目标时间: {TARGET_TIMES if TARGET_TIMES else '任意'}")

# ============ 创建会话 ============
session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 MicroMessenger/8.0"
session.headers["Referer"] = f"{BASE}/Views/Field/FieldOrder.html?VenueNo={VENUE_NO}&FieldTypeNo={FIELD_TYPE_NO}"
for seg in COOKIE.split(";"):
    if "=" in seg:
        k, v = seg.strip().split("=", 1)
        session.cookies.set(k, v)

# ============ 轮询获取可预约时段 ============
chosen = []
chosen_times = set()  # 已选的时间段

for poll in range(MAX_POLL):
    if poll > 0:
        print(f"[轮询] 第{poll+1}次，等待{POLL_INTERVAL}秒...")
        time.sleep(POLL_INTERVAL)
    
    # 收集所有可用时段
    all_available = []
    for dateadd in DATE_ADD_LIST:
        for tp in TIME_PERIOD_LIST:
            resp = session.get(f"{BASE}/Field/GetVenueStateNew", params={
                "dateadd": dateadd, "TimePeriod": tp, "VenueNo": VENUE_NO, "FieldTypeNo": FIELD_TYPE_NO
            }, timeout=10)
            data = json.loads(resp.text)
            if str(data.get("type")) != "1":
                continue
            
            slots = json.loads(data["resultdata"])
            for s in slots:
                if s.get("FieldState") != "0" or s.get("TimeStatus") != "1":
                    continue
                if TARGET_TIMES and s["BeginTime"] not in TARGET_TIMES:
                    continue
                s["_DateAdd"] = dateadd
                all_available.append(s)
    
    # 按 TARGET_TIMES 顺序排序（优先级）
    if TARGET_TIMES:
        all_available.sort(key=lambda x: TARGET_TIMES.index(x["BeginTime"]) if x["BeginTime"] in TARGET_TIMES else 999)
    
    # 第一轮：优先选不同时间段
    for s in all_available:
        if s["BeginTime"] in chosen_times:
            continue
        chosen.append(s)
        chosen_times.add(s["BeginTime"])
        print(f"[选中] {s['FieldName']} {s['BeginTime']}-{s['EndTime']}")
        if len(chosen) >= MAX_COUNT:
            break
    
    # 第二轮：如果不够，允许同一时间段的不同场地
    if len(chosen) < MAX_COUNT:
        chosen_fields = {(c["FieldNo"], c["BeginTime"]) for c in chosen}
        for s in all_available:
            key = (s["FieldNo"], s["BeginTime"])
            if key in chosen_fields:
                continue
            chosen.append(s)
            chosen_fields.add(key)
            print(f"[选中-补充] {s['FieldName']} {s['BeginTime']}-{s['EndTime']}")
            if len(chosen) >= MAX_COUNT:
                break
    
    if len(chosen) >= MAX_COUNT:
        break

# ============ 提交预约 ============
if not chosen:
    msg = "[失败] 没有可预约的场地"
    print(msg)
    send_email("❌ 体育馆预约失败", msg)
    exit(1)

checkdata = json.dumps([{
    "FieldNo": it["FieldNo"], "FieldTypeNo": it["FieldTypeNo"], "FieldName": it["FieldName"],
    "BeginTime": it["BeginTime"], "Endtime": it["EndTime"], "Price": it["FinalPrice"],
} for it in chosen])

api = "OrderFieldFree" if all(float(it["FinalPrice"]) == 0 for it in chosen) else "OrderField"
result = session.post(f"{BASE}/Field/{api}", data={
    "checkdata": checkdata, "dateadd": chosen[0]["_DateAdd"], "VenueNo": VENUE_NO
}, timeout=10)
print(f"[结果] {result.text}")

# 解析结果判断是否成功
result_data = json.loads(result.text)
is_success = str(result_data.get("type")) == "1"

# 发送邮件通知
slots_info = "\n".join([f"  {s['FieldName']} {s['BeginTime']}-{s['EndTime']}" for s in chosen])
if is_success:
    email_subject = "✅ 体育馆预约成功"
    email_body = f"""预约时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

预约场地:
{slots_info}

接口返回: {result.text}
"""
else:
    email_subject = "❌ 体育馆预约失败"
    email_body = f"""预约时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

尝试预约:
{slots_info}

失败原因: {result_data.get('message', '未知')}
接口返回: {result.text}
"""

send_email(email_subject, email_body)

# 不管成功失败都正常退出，避免 Actions 显示红色
# if not is_success:
#     exit(1)
