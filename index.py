
from flask import Flask, request, jsonify
import os, json, shutil
from dotenv import load_dotenv
load_dotenv()

DB_FILE = "/tmp/knowledge_base.json"
FALLBACK_FILE = "knowledge_base.json"

class KnowledgeBase:
    def __init__(self):
        for src in [FALLBACK_FILE, "../"+FALLBACK_FILE]:
            if not os.path.exists(DB_FILE) and os.path.exists(src):
                try: shutil.copy(src, DB_FILE)
                except: pass
        self.data = self._load()
    def _load(self):
        for p in [DB_FILE, FALLBACK_FILE, "../"+FALLBACK_FILE]:
            if os.path.exists(p):
                try:
                    with open(p,'r',encoding='utf-8') as f:
                        return json.load(f)
                except: pass
        return {"bot_replies":[],"client_messages":[],"comments":[],"custom_knowledge":["نغطي جميع محافظات مصر: القاهرة، الجيزة، الإسكندرية، الدلتا، الصعيد، والمدن الجديدة"],"posts":[],"properties":["شقة 120م في القاهرة الجديدة - التجمع الخامس - 1,800,000 جنيه"]}
    def _save(self):
        try:
            with open(DB_FILE,'w',encoding='utf-8') as f:
                json.dump(self.data,f,ensure_ascii=False,indent=2)
        except: pass
    def learn_from_interaction(self,text,source="message"):
        if not text or len(text.strip())<4: return
        key = "client_messages" if source=="message" else "comments" if source=="comment" else "bot_replies"
        self.data.setdefault(key,[]).append(text)
        if len(self.data[key])>200: self.data[key]=self.data[key][-200:]
        self._save()
    def add_post_content(self,value): pass
    def add_custom_knowledge(self,info):
        self.data.setdefault("custom_knowledge",[]).append(info); self._save()
    def get_all_knowledge(self): return self.data
    def build_context_for_ai(self):
        parts=[]
        if self.data.get("custom_knowledge"): parts.append("معلومات الشركة:\n" + "\n".join(self.data["custom_knowledge"][-20:]))
        if self.data.get("properties"): parts.append("عقارات متاحة:\n" + "\n".join(self.data["properties"][:20]))
        return "\n\n".join(parts) if parts else "نغطي جميع محافظات مصر"

from openai import OpenAI
class AIResponder:
    def __init__(self,kb):
        self.kb=kb
        self.client=OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
        self.model=os.getenv("MODEL_NAME","meta-llama/llama-3.1-8b-instruct:free")
    def generate_reply(self,user_text):
        context=self.kb.build_context_for_ai()
        system_prompt = "أنت مساعد عقاري ذكي لجميع أنحاء مصر، اسمك مساعد مصر العقاري. قاعدة البيانات:\n" + context + "\nقواعد: اعتمد على قاعدة البيانات أولا، لو مش موجود استخدم خبرتك كخبير عقاري في مصر (التجمع، زايد، اكتوبر، العاصمة، اسكندرية، منصورة، سوهاج الجديدة). لا تقل أبدا أنا ذكاء اصطناعي. لو مش عارف: سيبلي رقمك وطلبك بالظبط وهخلي المسؤول يكلمك حالا. اختم بسؤال: تحب أبعتلك صور؟ الميزانية كام؟ رد قصير سطرين ل 4 سطور بالعامية."
        try:
            r=self.client.chat.completions.create(model=self.model, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_text}], extra_headers={"HTTP-Referer":"https://egypt-real-estate.com","X-Title":"Egypt Real Estate Bot"}, temperature=0.7, max_tokens=300)
            return r.choices[0].message.content.strip()
        except Exception as e:
            print("AI Error:", e)
            return "أهلا بحضرتك! سيبلي طلبك بالتفصيل (المنطقة - المساحة - الميزانية) وهرد عليك حالا."

import requests
class FacebookAPI:
    def __init__(self):
        self.token=os.getenv("FB_PAGE_ACCESS_TOKEN","")
        self.base="https://graph.facebook.com/v18.0"
    def send_message(self,sender_id,text):
        if not self.token: return
        try: requests.post(self.base+"/me/messages?access_token="+self.token, json={"recipient":{"id":sender_id},"message":{"text":text}})
        except: pass
    def reply_to_comment(self,comment_id,text):
        if not self.token: return
        try: requests.post(self.base+"/"+comment_id+"/comments?access_token="+self.token, data={"message":text})
        except: pass

app = Flask(__name__)
kb = KnowledgeBase()
ai = AIResponder(kb)
fb_api = FacebookAPI()
VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN","egypt_verify_123")

@app.route('/')
def home():
    return "Egypt Real Estate Bot is Running ✅ - Powered by OpenRouter Free - Covers All Egypt"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode=request.args.get('hub.mode'); token=request.args.get('hub.verify_token'); challenge=request.args.get('hub.challenge')
    if mode=='subscribe' and token==VERIFY_TOKEN: return challenge,200
    return "Verification failed",403

@app.route('/webhook', methods=['POST'])
def webhook():
    data=request.get_json()
    if data and data.get('object')=='page':
        for entry in data.get('entry',[]):
            for msg_event in entry.get('messaging',[]):
                if 'message' in msg_event and 'text' in msg_event['message']:
                    user_text=msg_event['message']['text']
                    if msg_event['sender']['id']==entry['id']: continue
                    kb.learn_from_interaction(user_text,source="message")
                    reply=ai.generate_reply(user_text)
                    fb_api.send_message(msg_event['sender']['id'],reply)
            for change in entry.get('changes',[]):
                if change.get('field')=='feed':
                    value=change.get('value',{})
                    if value.get('item')=='comment' and value.get('verb')=='add':
                        comment_id=value.get('comment_id'); message=value.get('message','')
                        kb.learn_from_interaction(message,source="comment")
                        reply=ai.generate_reply(message)
                        fb_api.reply_to_comment(comment_id,reply)
    return "EVENT_RECEIVED",200

@app.route('/add-info', methods=['POST'])
def add_custom_info():
    info=request.json.get('info')
    if info:
        kb.add_custom_knowledge(info)
        return jsonify({"status":"added"})
    return jsonify({"error":"no info"}),400

@app.route('/knowledge', methods=['GET'])
def view_knowledge():
    return jsonify(kb.get_all_knowledge())
