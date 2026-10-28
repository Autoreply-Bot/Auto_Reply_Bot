
from flask import Flask, request, jsonify
import os, json, shutil

app = Flask(__name__)

# Simple in-memory knowledge for Egypt
KNOWLEDGE = {
  "custom_knowledge": ["نغطي جميع محافظات مصر: القاهرة، الجيزة، الإسكندرية، الدلتا، الصعيد، والمدن الجديدة"],
  "properties": ["شقة 120م في القاهرة الجديدة - التجمع الخامس - 1,800,000 جنيه"]
}

@app.route('/')
def home():
    return "Egypt Real Estate Bot is Running ✅ - Powered by OpenRouter Free - Covers All Egypt - Vercel Free"

@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    verify_token = os.getenv("FB_VERIFY_TOKEN","egypt_verify_123")
    if mode == 'subscribe' and token == verify_token:
        return challenge, 200
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(f"Incoming: {data}")
    # For now just acknowledge - we will add AI later after base works
    if data and data.get('object') == 'page':
        # Try to reply if token exists
        try:
            from openai import OpenAI
            import requests
            kb_context = "\n".join(KNOWLEDGE["custom_knowledge"])
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
            model = os.getenv("MODEL_NAME","meta-llama/llama-3.1-8b-instruct:free")
            for entry in data.get('entry',[]):
                for msg_event in entry.get('messaging',[]):
                    if 'message' in msg_event and 'text' in msg_event['message']:
                        user_text = msg_event['message']['text']
                        sender_id = msg_event['sender']['id']
                        if sender_id == entry['id']: continue
                        try:
                            system_prompt = f"أنت مساعد عقاري ذكي لجميع أنحاء مصر، اسمك مساعد مصر العقاري. معلومات: {kb_context}. رد بالعامية المصرية قصير."
                            r = client.chat.completions.create(model=model, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_text}], temperature=0.7, max_tokens=200)
                            reply = r.choices[0].message.content.strip()
                        except Exception as e:
                            print("AI Error", e)
                            reply = "أهلا بحضرتك! سيبلي طلبك بالتفصيل (المنطقة - المساحة - الميزانية) وهرد عليك حالا."
                        token = os.getenv("FB_PAGE_ACCESS_TOKEN","")
                        if token:
                            try:
                                requests.post(f"https://graph.facebook.com/v18.0/me/messages?access_token={token}", json={"recipient":{"id":sender_id},"message":{"text":reply}})
                            except: pass
                for change in entry.get('changes',[]):
                    if change.get('field')=='feed':
                        value = change.get('value',{})
                        if value.get('item')=='comment' and value.get('verb')=='add':
                            comment_id = value.get('comment_id')
                            message = value.get('message','')
                            try:
                                system_prompt = f"أنت مساعد عقاري ذكي لجميع أنحاء مصر. معلومات: {kb_context}. رد بالعامية."
                                r = client.chat.completions.create(model=model, messages=[{"role":"system","content":system_prompt},{"role":"user","content":message}], temperature=0.7, max_tokens=200)
                                reply = r.choices[0].message.content.strip()
                            except:
                                reply = "شكرا لتواصلك! سيبلي تفاصيل طلبك وهرد عليك حالا."
                            token = os.getenv("FB_PAGE_ACCESS_TOKEN","")
                            if token:
                                try:
                                    requests.post(f"https://graph.facebook.com/v18.0/{comment_id}/comments?access_token={token}", data={"message":reply})
                                except: pass
        except Exception as e:
            print("Webhook error:", e)
    return "EVENT_RECEIVED", 200

@app.route('/add-info', methods=['POST'])
def add_info():
    return jsonify({"status":"ok"})

@app.route('/knowledge', methods=['GET'])
def knowledge():
    return jsonify(KNOWLEDGE)
