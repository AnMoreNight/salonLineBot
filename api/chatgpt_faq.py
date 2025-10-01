"""
ChatGPT-powered FAQ system for natural language responses
"""
import os
import openai
from typing import Optional

class ChatGPTFAQ:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.system_prompt = """あなたは美容室「サロンAI」の親切なスタッフです。
お客様の質問に対して、丁寧で親しみやすい口調で回答してください。
美容室に関する一般的な質問には専門的な知識を交えて回答し、
予約やサービスに関する質問には具体的な案内をしてください。
"""
    
    def get_response(self, user_message: str) -> str:
        """
        Get ChatGPT-powered natural language response
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"ChatGPT API error: {e}")
            return "申し訳ございませんが、現在システムの調子が悪いようです。しばらくしてから再度お試しください。"
