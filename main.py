import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import feedparser
import os

# 从 GitHub Secrets 读取配置
SENDER_EMAIL = os.getenv("SMTP_EMAIL")
SENDER_PASS = os.getenv("SMTP_PASSWORD")
RECEIVER_EMAIL = os.getenv("TO_EMAIL")

def get_ai_news():
    news_sources = [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.technologyreview.com/feed/"
    ]
    news = []
    for url in news_sources:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            news.append(f"📌 {entry.title}\n{entry.link}\n")
    return "\n".join(news)

def summarize_news(raw_news):
    return f"📰 全球AI日报 | {datetime.now().strftime('%Y-%m-%d')}\n\n{raw_news}\n\n---\n自动生成，仅供参考"

def send_email(content):
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['Subject'] = f"📰 全球AI日报 | {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    # 163邮箱SMTP配置，QQ邮箱请改为 smtp.qq.com，端口465
    with smtplib.SMTP_SSL('smtp.163.com', 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.send_message(msg)

if __name__ == "__main__":
    raw_news = get_ai_news()
    report = summarize_news(raw_news)
    send_email(report)
