import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import feedparser
import os
import re
# 用稳定版googletrans做翻译（解决语法错误+翻译失败问题）
from googletrans import Translator

# 从GitHub Secrets读取配置
SENDER_EMAIL = os.getenv("SMTP_EMAIL")
SENDER_PASS = os.getenv("SMTP_PASSWORD")
RECEIVER_EMAIL = os.getenv("TO_EMAIL")

# 初始化翻译器（设置超时，避免卡住）
translator = Translator(timeout=10)

def clean_text(text):
    """彻底清理链接和多余格式"""
    # 移除所有网址
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    # 移除多余空格和换行
    text = re.sub(r'\s+', ' ', text).strip()
    # 只保留前200字，避免内容过长
    return text[:200]

def get_english_news():
    """抓取英文AI新闻（只取前3条，避免内容过多）"""
    news_sources = [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.technologyreview.com/feed/"
    ]
    english_news = []
    for url in news_sources:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            title = clean_text(entry.title)
            summary = clean_text(entry.summary)
            english_news.append(f"标题：{title}\n摘要：{summary}")
    return "\n\n".join(english_news)

def translate_to_chinese(english_text):
    """将英文新闻翻译成简洁中文小结"""
    try:
        # 分段翻译，避免单次翻译过长
        chinese_parts = []
        for part in english_text.split("\n\n"):
            if part.strip() and "标题：" in part:
                # 拆分标题和摘要分别翻译
                en_title = part.split("标题：")[1].split("摘要：")[0].strip()
                en_summary = part.split("摘要：")[1].strip()
                
                # 翻译标题和摘要
                zh_title = translator.translate(en_title, dest='zh-CN').text
                zh_summary = translator.translate(en_summary, dest='zh-CN').text
                
                # 生成精简小结
                chinese_parts.append(f"🔹 {zh_title}\n  {zh_summary}")
        
        # 合并成最终中文内容
        return "\n\n".join(chinese_parts)
    except Exception as e:
        # 翻译失败时返回英文原文（保证脚本不崩溃）
        return f"⚠️ 翻译服务临时不可用，以下是英文原文：\n{english_text}"

def send_email(content):
    """发送纯中文日报到指定邮箱"""
    # 组装邮件内容
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['Subject'] = f"📰 全球AI日报 | {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    # 自动适配邮箱SMTP服务器（QQ/163通用）
    if "qq.com" in SENDER_EMAIL:
        smtp_server = "smtp.qq.com"
    else:
        smtp_server = "smtp.163.com"

    # 发送邮件（带异常处理，避免登录失败崩溃）
    try:
        with smtplib.SMTP_SSL(smtp_server, 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.send_message(msg)
        print("邮件发送成功！")
    except Exception as e:
        raise Exception(f"邮件发送失败：{str(e)}")

if __name__ == "__main__":
    # 核心执行流程（全程带异常处理，保证不崩溃）
    try:
        # 1. 抓取英文新闻（去链接）
        en_news = get_english_news()
        # 2. 翻译成中文小结
        zh_news = translate_to_chinese(en_news)
        # 3. 组装最终日报
        final_report = f"""📰 全球AI日报 | {datetime.now().strftime('%Y-%m-%d')}

{zh_news}

---
✅ 自动生成（纯中文无链接版）
🕒 每日北京时间8点更新"""
        # 4. 发送邮件
        send_email(final_report)
    except Exception as e:
        # 捕获所有异常并抛出，让GitHub Actions显示具体错误
        raise Exception(f"脚本执行失败：{str(e)}")
