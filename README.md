# 西电广研院体育馆自动预约

自动预约西电广研院笃行体育馆健身房。

## 功能

- 🏋️ 自动预约健身房指定时间段
- 🔄 轮询等待 8:00 开放预约
- 📧 邮件通知预约结果

## GitHub Actions 使用

### 1. Fork 本仓库

### 2. 设置 Secret

Settings → Secrets and variables → Actions → New repository secret

**名称：** `BOOK_CONFIG`

**值：** JSON 格式配置
```json
{
  "COOKIE": "你的登录Cookie",
  "TARGET_TIMES": ["13:00", "14:00"],
  "SMTP_USER": "你的QQ邮箱@qq.com",
  "SMTP_PASS": "QQ邮箱授权码",
  "NOTIFY_EMAIL": "收件邮箱"
}
```

### 3. 手动触发

Actions → 体育馆预约 → Run workflow

每天 **7:55** 手动触发，脚本会轮询等待 8:00 开放预约。

## 本地使用

1. 复制 `config.example.json` 为 `config.json`
2. 填入你的配置
3. 运行 `python auto_book.py`

## 配置说明

| 字段 | 说明 |
|------|------|
| COOKIE | 登录 Cookie（从浏览器 F12 获取） |
| TARGET_TIMES | 目标时间段，如 `["13:00", "14:00"]` |
| SMTP_USER | QQ 邮箱地址 |
| SMTP_PASS | QQ 邮箱授权码（设置-账户-生成授权码） |
| NOTIFY_EMAIL | 收件邮箱，留空则发给自己 |

## Cookie 获取

1. 微信打开体育馆预约小程序
2. 用抓包工具获取 Cookie
3. 或者浏览器打开 https://gyytygyy.xidian.edu.cn 登录后 F12 获取

## 注意

- Cookie 有效期约 7 天，需定期更新
- 每人每天限预约 2 个时段
- 可提前 2 天预约
