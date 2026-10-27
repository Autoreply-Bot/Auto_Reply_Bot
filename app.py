from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from ai_responder import AIResponder
from facebook_api import FacebookAPI
from database import KnowledgeBase

load_dotenv()

app = Flask(__name__)

# تحميل الأنظمة
kb = KnowledgeBase()
ai = AIResponder(kb)
fb_api = FacebookAPI()

VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "egypt_verify_123")

@app.route('/')
def home():
    return "Egypt Real Estate Bot is Running ✅ - Powered by OpenRouter Free"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """فيسبوك بيستخدمها للتأكد انك صاحب البوت"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    """هنا بيجي كل رسالة وتعليق"""
    data = request.get_json()
    print(f"Incoming: {data}")

    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            # 1. رسائل الماسنجر
            for msg_event in entry.get('messaging', []):
                sender_id = msg_event['sender']['id']
                if 'message' in msg_event and 'text' in msg_event['message']:
                    user_text = msg_event['message']['text']
                    # تجاهل رسائل الصفحة نفسها
                    if msg_event['sender']['id'] == entry['id']:
                        continue
                    
                    # التعلم: خزن سؤال العميل
                    kb.learn_from_interaction(user_text, source="message")
                    
                    # الرد الذكي
                    reply = ai.generate_reply(user_text)
                    
                    # ابعت الرد
                    fb_api.send_message(sender_id, reply)
                    
                    # التعلم: خزن رد البوت
                    kb.learn_from_interaction(reply, source="bot_reply")

            # 2. تعليقات الصفحة
            for change in entry.get('changes', []):
                if change.get('field') == 'feed':
                    value = change.get('value', {})
                    if value.get('item') == 'comment' and value.get('verb') == 'add':
                        comment_id = value.get('comment_id')
                        message = value.get('message', '')
                        
                        kb.learn_from_interaction(message, source="comment")
                        kb.add_post_content(value) # تحديث قاعدة البيانات من البوستات
                        
                        reply = ai.generate_reply(message)
                        fb_api.reply_to_comment(comment_id, reply)
                        kb.learn_from_interaction(reply, source="bot_reply")

    return "EVENT_RECEIVED", 200

@app.route('/add-info', methods=['POST'])
def add_custom_info():
    """انت تقدر تضيف معلومات للبوت يدوياً من هنا"""
    info = request.json.get('info')
    if info:
        kb.add_custom_knowledge(info)
        return jsonify({"status": "added", "info": info})
    return jsonify({"error": "no info"}), 400

@app.route('/knowledge', methods=['GET'])
def view_knowledge():
    return jsonify(kb.get_all_knowledge())

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
