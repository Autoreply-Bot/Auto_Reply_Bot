import os
import requests

class FacebookAPI:
    def __init__(self):
        self.page_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
        self.graph_url = "https://graph.facebook.com/v20.0"

    def send_message(self, recipient_id, message_text):
        if not self.page_token:
            print("FB_PAGE_ACCESS_TOKEN not set, skipping send")
            return
        url = f"{self.graph_url}/me/messages"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text},
            "access_token": self.page_token
        }
        try:
            r = requests.post(url, json=payload, timeout=10)
            print(f"Send Message Status: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"Send Error: {e}")

    def reply_to_comment(self, comment_id, message_text):
        if not self.page_token:
            print("FB_PAGE_ACCESS_TOKEN not set, skipping comment reply")
            return
        url = f"{self.graph_url}/{comment_id}/comments"
        payload = {
            "message": message_text,
            "access_token": self.page_token
        }
        try:
            r = requests.post(url, data=payload, timeout=10)
            print(f"Reply Comment Status: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"Comment Reply Error: {e}")

    def get_page_posts(self, limit=20):
        """يسحب منشورات الصفحة عشان يحدث قاعدة البيانات"""
        if not self.page_token:
            return []
        url = f"{self.graph_url}/me/posts?fields=message,created_time&limit={limit}&access_token={self.page_token}"
        try:
            r = requests.get(url, timeout=10)
            return r.json().get('data', [])
        except:
            return []
