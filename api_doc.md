# 西电广研院体育馆预约系统 API 文档

## 基础信息
- **BASE URL**: `https://gyytygyy.xidian.edu.cn`
- **认证方式**: Cookie (需要登录后获取)

---

## 用户相关 API

### 1. 检查用户状态
```
GET /User/CheckUserStatus
返回: "1" (已登录) 或 重定向到登录页
```

### 2. 获取用户信息
```
GET /User/GetUserInfo
返回: 用户基本信息 (UserId, UserName, Phone, MemberNo, MemberType等)
```

### 3. 获取会员详细信息
```
GET /User/GetMemberInfo
返回: 会员详细信息 (MemberNo, MemberName, Telphone, Integra积分, BreakCount爽约次数等)
```

### 4. 获取会员卡信息
```
GET /User/GetCardInfo
返回: 会员卡信息 (Balance余额, CardNo, CardType等)
```

### 5. 获取配置值
```
GET /User/GetConfigValue
返回: 配置值
```

### 6. 获取网页配置值
```
GET /User/GetWebConfigValue?SetID=258&VenueNo=02
返回: 预约规则说明文本
```

---

## 场馆相关 API

### 1. 获取场馆信息
```
GET /Field/GetVenue?VenueNo=02
返回: 场馆详细信息
- VenueName: 场馆名称
- Address: 地址
- BeginTime/EndTime: 营业时间 (9-22)
- ReserveDays: 可预约天数 (2天)
```

### 2. 获取登录场馆信息
```
GET /Venue/GetLoginVenueInfo?IsFirst=0
返回: 当前登录场馆的详细信息
```

### 3. 获取预约限制信息
```
GET /Field/GetOrderInfo?VenueNo=02
返回:
- limitcount: 每人限制预约数 (2)
- IsWXReserveNoPay: 微信预约免支付 (0/1)
```

---

## 场地类型相关 API

### 1. 获取场地类型信息
```
GET /Field/GetFieldType?FieldTypeNo=021
返回: 场地类型详细信息
- FieldTypeName: 名称
- MaxPeople: 最大人数
- SharePeople: 可分享人数
- DisplayName: 显示名称
```

### 2. 获取所有场地类型
```
GET /Field/GetFieldTypeInfoByT?VenueNo=02
返回: 所有场地类型列表
```

**场地类型编号对照:**
| 编号 | 名称 | 最大人数 | 分享人数 |
|------|------|----------|----------|
| 021 | 广研院羽毛球 | 6 | 5 |
| 022 | 广研院篮球 | 10 | 9 |
| 023 | 广研院健身房 | 1 | 0 |
| 024 | 广研院舞蹈室 | 15 | 0 |

---

## 场地状态/预约相关 API

### 1. 获取可预约日期
```
GET /Field/GetWeek?VenueNo=02&FieldTypeNo=021
返回: 可预约的日期列表 (Date, Week)
```

### 2. 获取场地状态 ⭐ (核心API)
```
GET /Field/GetVenueStateNew?dateadd=0&TimePeriod=2&VenueNo=02&FieldTypeNo=021
参数:
- dateadd: 日期偏移 (0=今天, 1=明天)
- TimePeriod: 时间段 (0=上午, 1=下午, 2=晚上)
- VenueNo: 场馆编号
- FieldTypeNo: 场地类型编号

返回: 
- type: 1=成功, 2=无数据, 3=其他错误
- resultdata: 场地状态列表 (JSON字符串)
  - FieldNo: 场地编号
  - FieldName: 场地名称
  - BeginTime/EndTime: 时间段
  - FieldState: 状态 (0=可预约, 1=已预约)
  - TimeStatus: 时间状态 (1=可预约时间)
  - FinalPrice: 价格
  - MembeName: 预约人姓名
```

### 3. 免费场地预约 ⭐
```
POST /Field/OrderFieldFree
参数:
- checkdata: JSON数组 [{"FieldNo":"...", "FieldTypeNo":"...", "FieldName":"...", "BeginTime":"...", "Endtime":"...", "Price":"0"}]
- dateadd: 日期偏移
- VenueNo: 场馆编号

返回:
- type: 1=成功
- message: 错误信息
```

### 4. 付费场地预约
```
POST /Field/OrderField
参数: 同上
返回:
- type: 1=成功
- resultdata: 订单ID (用于支付)
```

### 5. 隐藏/取消预约
```
POST /Field/hideOrder?OID=订单ID
```

---

## 其他有用信息

### 时间段对照
| TimePeriod | 含义 | 大致时间 |
|------------|------|----------|
| 0 | 上午 | 9:00-12:00 |
| 1 | 下午 | 12:00-18:00 |
| 2 | 晚上 | 18:00-22:00 |

### 场地状态对照
| FieldState | TimeStatus | 含义 |
|------------|------------|------|
| 0 | 1 | 可预约 |
| 0 | 0 | 时间已过 |
| 1 | - | 已被预约 |

### 预约规则
1. 每人每天最多预约 **2** 个时段
2. 可提前 **2** 天预约
3. 营业时间: **9:00 - 22:00**
4. 预约场地保留 **10分钟**，未支付自动取消记为爽约
5. 爽约 **3次** 将被加入黑名单 **2个月**

---

## 示例代码

```python
import requests
import json

COOKIE_STR = "你的Cookie"
BASE = "https://gyytygyy.xidian.edu.cn"

def cookie_to_dict(cookie_str):
    ck = {}
    for seg in cookie_str.split(";"):
        if "=" in seg:
            k, v = seg.strip().split("=", 1)
            ck[k] = v
    return ck

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 ...",
    "Referer": f"{BASE}/Views/Field/FieldOrder.html?VenueNo=02&FieldTypeNo=021",
})
session.cookies.update(cookie_to_dict(COOKIE_STR))

# 获取今天晚上羽毛球场地状态
r = session.get(f"{BASE}/Field/GetVenueStateNew", params={
    "dateadd": "0",
    "TimePeriod": "2",
    "VenueNo": "02",
    "FieldTypeNo": "021"
})
data = json.loads(r.text)
if data.get('type') == 1:
    slots = json.loads(data['resultdata'])
    for s in slots:
        if s.get('FieldState') == '0' and s.get('TimeStatus') == '1':
            print(f"可预约: {s['FieldName']} {s['BeginTime']}-{s['EndTime']}")
```
