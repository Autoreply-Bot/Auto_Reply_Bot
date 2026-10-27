import json
import os
from datetime import datetime
import threading

DB_FILE = "knowledge_base.json"

class KnowledgeBase:
    def __init__(self):
        self.lock = threading.Lock()
        self.data = self._load()
        if not self.data:
            self.data = {
                "custom_knowledge": [],
                "client_messages": [],
                "comments": [],
                "posts": [],
                "bot_replies": [],
                "properties": [] # قاعدة بيانات الشقق
            }
            self._save()

    def _load(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None

    def _save(self):
        with self.lock:
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_custom_knowledge(self, info):
        """انت بتضيف معلومة يدوياً: مثلا شقة جديدة للبيع"""
        self.data["custom_knowledge"].append({
            "text": info,
            "time": datetime.now().isoformat()
        })
        # لو المعلومة فيها شقة، حاول تستخرجها كعقار
        if any(k in info for k in ["شقة", "بيت", "محل", "للبيع", "للايجار"]):
            self.data["properties"].append(info)
        self._save()

    def learn_from_interaction(self, text, source="message"):
        """يتعلم من كل رسالة وتعليق"""
        if len(text.strip()) < 3:
            return
        entry = {"text": text, "time": datetime.now().isoformat()}
        if source == "message":
            self.data["client_messages"].append(entry)
            # احتفظ بآخر 500 رسالة فقط
            self.data["client_messages"] = self.data["client_messages"][-500:]
        elif source == "comment":
            self.data["comments"].append(entry)
            self.data["comments"] = self.data["comments"][-500:]
        elif source == "bot_reply":
            self.data["bot_replies"].append(entry)
            self.data["bot_replies"] = self.data["bot_replies"][-500:]
        self._save()

    def add_post_content(self, post_value):
        """يضيف محتوى المنشورات الجديدة"""
        msg = post_value.get('message', '') or post_value.get('post', '')
        if msg:
            self.data["posts"].append({"text": msg, "time": datetime.now().isoformat()})
            self.data["posts"] = self.data["posts"][-200:]
            self._save()

    def build_context_for_ai(self):
        """يبني سياق ذكي للذكاء الاصطناعي"""
        context_parts = []
        
        # 1. المعلومات اللي انت ضفتها يدوياً (أهم حاجة)
        if self.data["custom_knowledge"]:
            context_parts.append("### معلومات صاحب الصفحة (مؤكدة):")
            for item in self.data["custom_knowledge"][-20:]: # آخر 20 معلومة
                context_parts.append(f"- {item['text']}")

        # 2. العقارات المتاحة
        if self.data["properties"]:
            context_parts.append("\n### العقارات المتاحة حالياً:")
            for prop in self.data["properties"][-20:]:
                context_parts.append(f"- {prop}")

        # 3. ملخص لاهتمامات العملاء من الرسائل
        if self.data["client_messages"]:
            recent_questions = [m['text'] for m in self.data["client_messages"][-10:]]
            context_parts.append(f"\n### أسئلة العملاء الأخيرة (عشان تفهم السوق): {', '.join(recent_questions[:5])}")

        return "\n".join(context_parts) if context_parts else "لا توجد معلومات مخصصة بعد، اعتمد على خبرتك العامة في عقارات سوهاج."

    def get_all_knowledge(self):
        return self.data
