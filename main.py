import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import feedparser
import os
from translate import Translator  # 免费翻译库，无需 API Key

# 从 GitHub Secrets 读取配置
SENDER_EMAIL = os.getenv("SMTP_EMAIL")
SENDER_PASS = os.getenv("SMTP_PASSWORD")
RECEIVER_EMAIL = os.getenv("TO_EMAIL")

# 配置免费翻译（英文→中文）
translator = Translator(from_lang="english", to_lang="chinese")

def clean_text(text):
    """清理文本：去掉链接、多余空格和特殊符号"""
    import re
    # 移除所有网址链接
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    # 移除多余空格和换行
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_ai_news():
    """抓取英文 AI 新闻，只保留标题和摘要"""
    news_sources = [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.technologyreview.com/feed/"
    ]
    news_list = []
    for url in news_sources:
        feed = feedparser.parse(url)
        # 只取前3条新闻，避免内容过多
        for entry in feed.entries[:3]:
            # 清理标题和摘要（去链接）
            clean_title = clean_text(entry.title)
            clean_summary = clean_text(entry.summary)
            news_list.append(f"标题：{clean_title}\n摘要：{clean_summary}")
    return "\n\n".join(news_list)

def translate_to_chinese(text):
    """免费翻译英文到中文，生成简洁小结"""
    try:
        # 分段翻译，避免过长
        translated_parts = []
        for part in text.split("\n\n"):
            if part.strip():
                # 翻译+精简小结
                trans_part = translator.translate(part)
                # 提取核心信息，生成一句话小结
                if "标题：" in trans_part and "摘要：" in trans_part:
                    title = trans_part.split("标题：")[1].split("摘要：")[0].strip()
                    summary = trans_part.split("摘要：")[1].strip()
                    translated_parts.append(f"🔹 {title}\n  {summary[:100]}...")  # 摘要限制100字
        return "\n\n".join(translated_parts)
    except Exception as e:
        return f"⚠️ 翻译失败（原因：{str(e)}），以下是原文：\n{text}"

def send_email(content):
    """发送中文日报到指定邮箱"""
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['Subject'] = f"📰 全球AI日报 | {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    # 适配不同邮箱的 SMTP 配置
    if "163.com" in SENDER_EMAIL:
        smtp_server = "smtp.163.com"
    elif "qq.com" in SENDER_EMAIL:
        smtp_server = "smtp.qq.com"
    else:
        smtp_server = "smtp.163.com"  # 默认163

    with smtplib.SMTP_SSL(smtp_server, 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.send_message(msg)

if __name__ == "__main__":
    # 1. 抓取英文新闻（去链接）
    raw_news = get_ai_news()
    # 2. 翻译为中文并生成小结
    chinese_summary = translate_to_chinese(raw_news)
    # 3. 组装日报内容
    report = f"""📰 全球AI日报 | {datetime.now().strftime('%Y-%m-%d')}

{chinese_summary}
   
