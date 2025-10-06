"""
ChatGPT-powered FAQ system for natural language responses using KB facts
"""
import os
import openai
from typing import Optional

class ChatGPTFAQ:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.system_prompt = """あなたは美容室「サロンAI」の親切なスタッフです。

重要なルール：
1. 提供されたKB事実のみを使用して回答してください
2. 推測や憶測は絶対に禁止です
3. KBにない情報は「分かりません」と答えてください
4. 医療・薬剤に関する質問は人手誘導してください
5. 数値の推測は禁止です

回答スタイル：
- 丁寧で親しみやすい口調
- KB事実を自然な日本語で説明
- 必要に応じて確認質問を追加
- 不明な点は素直に「分かりません」と伝える
"""
    
    def get_response(self, user_message: str, kb_facts: Optional[dict] = None) -> str:
        """
        Get ChatGPT-powered natural language response using KB facts
        """
        try:
            # Build context from KB facts
            context = ""
            if kb_facts and kb_facts.get('kb_facts'):
                context = f"\n\n利用可能な事実情報：\n"
                for key, value in kb_facts['kb_facts'].items():
                    context += f"- {key}: {value}\n"
                context += "\n上記の事実情報のみを使用して回答してください。"
            
            # Check for dangerous queries
            if self._is_dangerous_query(user_message):
                return "申し訳ございませんが、その質問については分かりません。スタッフにお繋ぎします。"
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt + context},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.3  # Lower temperature for more consistent responses
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"ChatGPT API error: {e}")
            return "申し訳ございませんが、現在システムの調子が悪いようです。しばらくしてから再度お試しください。"
    
    def _is_dangerous_query(self, message: str) -> bool:
        """Check if query is in dangerous areas that need human guidance"""
        dangerous_keywords = [
            "薬", "薬剤", "治療", "診断", "病気", "症状", "副作用",
            "アレルギー", "妊娠", "授乳", "医療", "医師", "病院"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in dangerous_keywords)
