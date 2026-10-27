import os
from openai import OpenAI
import json

class AIResponder:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        # OpenRouter Client - مجاني
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        self.model = os.getenv("MODEL_NAME", "meta-llama/llama-3.1-8b-instruct:free")

    def generate_reply(self, user_text):
        # 1. جمع المعلومات الخاصة بصفحتك
        context = self.kb.build_context_for_ai()

        system_prompt = f"""
أنت مساعد عقاري ذكي لصفحات عقارات في جميع أنحاء مصر. اسمك "مساعد مصر العقاري".

**مهمتك الأساسية:**
ترد على العملاء بشكل مباشر، ودود، ومحترف باللهجة المصرية العامية الخفيفة.

**قاعدة البيانات الخاصة بك (استخدمها دائماً):**
{context}

**قواعد الرد المثالية:**
1.  اعتمد أولاً على قاعدة البيانات اللي فوق. لو العميل سأل عن منطقة أو سعر موجود في قاعدة البيانات، جاوب منه مباشرة.
2.  لو السؤال مش موجود في قاعدة البيانات، استخدم ذكائك العام كخبير عقاري في مصر كلها (تعرف مناطق زي: القاهرة الجديدة، زايد، أكتوبر، العاصمة الإدارية، الإسكندرية، المنصورة، سوهاج الجديدة، سيتي والزهراء بسوهاج، وغيرها في كل المحافظات).
3.  لا تقل أبداً "أنا ذكاء اصطناعي". أنت موظف في الشركة.
4.  لو مش عارف إجابة، قول: "سيبلي رقمك وعنوان طلبك بالظبط وهخلي المسؤول يكلمك حالاً" وخزن الطلب.
5.  دائماً اختم بسؤال يخلي العميل يكمل كلام: "تحب أبعتلك صور؟" أو "الميزانية كام؟"
6.  ردودك قصيرة (سطرين ل 4 سطور) ومباشرة.

**أمثلة على معلوماتك اللي بتتحدث باستمرار:**
- كل رسائل العملاء القديمة
- كل تعليقات الصفحة
- كل منشورات الصفحة
- المعلومات اللي صاحب الصفحة بيضيفها يدوياً
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                extra_headers={
                    "HTTP-Referer": "https://egypt-real-estate.com",
                    "X-Title": "Egypt Real Estate Bot"
                },
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"AI Error: {e}")
            # رد احتياطي لو الموديل المجاني وقع
            return "أهلاً بحضرتك! سيبلي طلبك بالتفصيل (المنطقة - المساحة - الميزانية) وهرد عليك حالاً بالمناسب ليك."
