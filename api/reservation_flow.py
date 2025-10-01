"""
Reservation flow system with intent detection, candidate suggestions, and confirmation
"""
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

class ReservationFlow:
    def __init__(self):
        self.user_states = {}  # Store user reservation states
        self.available_slots = self._generate_sample_slots()
        self.services = {
            "カット": {"duration": 60, "price": 3000},
            "カラー": {"duration": 120, "price": 8000},
            "パーマ": {"duration": 150, "price": 12000},
            "トリートメント": {"duration": 90, "price": 5000}
        }
    
    def _generate_sample_slots(self) -> List[Dict[str, Any]]:
        """Generate sample available time slots"""
        slots = []
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for day in range(7):  # Next 7 days
            date = base_date + timedelta(days=day)
            if date.weekday() == 1:  # Skip Tuesday (holiday)
                continue
                
            for hour in range(10, 19):  # 10:00 to 18:00
                if hour == 12:  # Skip lunch break
                    continue
                slots.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "time": f"{hour:02d}:00",
                    "available": True
                })
        
        return slots
    
    def detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        message_lower = message.lower()
        
        # Reservation intent keywords
        reservation_keywords = [
            "予約", "予約したい", "予約お願い", "予約できますか",
            "空いてる", "空き", "時間", "いつ", "可能"
        ]
        
        # Service intent keywords
        service_keywords = [
            "カット", "カラー", "パーマ", "トリートメント",
            "髪", "美容", "スタイル"
        ]
        
        # Cancel intent keywords
        cancel_keywords = [
            "キャンセル", "取り消し", "予約変更", "変更"
        ]
        
        if any(keyword in message_lower for keyword in reservation_keywords):
            return "reservation"
        elif any(keyword in message_lower for keyword in service_keywords):
            return "service_inquiry"
        elif any(keyword in message_lower for keyword in cancel_keywords):
            return "cancel"
        else:
            return "general"
    
    def handle_reservation_flow(self, user_id: str, message: str) -> str:
        """Handle the complete reservation flow"""
        if user_id not in self.user_states:
            self.user_states[user_id] = {"step": "start", "data": {}}
        
        state = self.user_states[user_id]
        step = state["step"]
        
        if step == "start":
            return self._start_reservation(user_id)
        elif step == "service_selection":
            return self._handle_service_selection(user_id, message)
        elif step == "date_selection":
            return self._handle_date_selection(user_id, message)
        elif step == "time_selection":
            return self._handle_time_selection(user_id, message)
        elif step == "confirmation":
            return self._handle_confirmation(user_id, message)
        else:
            return "予約フローに問題が発生しました。最初からやり直してください。"
    
    def _start_reservation(self, user_id: str) -> str:
        """Start reservation process"""
        self.user_states[user_id]["step"] = "service_selection"
        return """ご予約ありがとうございます！
どのサービスをご希望ですか？

・カット（60分・3,000円）
・カラー（120分・8,000円）
・パーマ（150分・12,000円）
・トリートメント（90分・5,000円）

サービス名をお送りください。"""
    
    def _handle_service_selection(self, user_id: str, message: str) -> str:
        """Handle service selection"""
        selected_service = None
        for service_name in self.services.keys():
            if service_name in message:
                selected_service = service_name
                break
        
        if not selected_service:
            return "申し訳ございませんが、そのサービスは提供しておりません。上記のサービスからお選びください。"
        
        self.user_states[user_id]["data"]["service"] = selected_service
        self.user_states[user_id]["step"] = "date_selection"
        
        return f"""{selected_service}ですね！
ご希望の日付をお選びください。

今週の空いている日：
・明日
・明後日
・今週の土曜日

日付をお送りください。"""
    
    def _handle_date_selection(self, user_id: str, message: str) -> str:
        """Handle date selection"""
        # Simple date parsing (in real implementation, use proper date parsing)
        if "明日" in message:
            selected_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "明後日" in message:
            selected_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        elif "土曜日" in message or "土曜" in message:
            # Find next Saturday
            days_ahead = 5 - datetime.now().weekday()  # Saturday is 5
            if days_ahead <= 0:
                days_ahead += 7
            selected_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        else:
            return "申し訳ございませんが、その日付は選択できません。上記の日付からお選びください。"
        
        self.user_states[user_id]["data"]["date"] = selected_date
        self.user_states[user_id]["step"] = "time_selection"
        
        # Get available times for selected date
        available_times = [slot["time"] for slot in self.available_slots 
                          if slot["date"] == selected_date and slot["available"]]
        
        return f"""{selected_date}ですね！
空いている時間帯は以下の通りです：

{chr(10).join([f"・{time}" for time in available_times[:5]])}

ご希望の時間をお送りください。"""
    
    def _handle_time_selection(self, user_id: str, message: str) -> str:
        """Handle time selection"""
        # Extract time from message
        time_match = re.search(r'(\d{1,2}):?(\d{2})?', message)
        if not time_match:
            return "時間を正しく入力してください（例：14:00、15時など）"
        
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        selected_time = f"{hour:02d}:{minute:02d}"
        
        # Check if time is available
        selected_date = self.user_states[user_id]["data"]["date"]
        available_times = [slot["time"] for slot in self.available_slots 
                         if slot["date"] == selected_date and slot["available"]]
        
        if selected_time not in available_times:
            return "申し訳ございませんが、その時間は既に予約が入っています。他の時間をお選びください。"
        
        self.user_states[user_id]["data"]["time"] = selected_time
        self.user_states[user_id]["step"] = "confirmation"
        
        service = self.user_states[user_id]["data"]["service"]
        service_info = self.services[service]
        
        return f"""予約内容の確認です：

📅 日時：{selected_date} {selected_time}
💇 サービス：{service}
⏱️ 所要時間：{service_info['duration']}分
💰 料金：{service_info['price']:,}円

この内容で予約を確定しますか？
「はい」または「確定」とお送りください。"""
    
    def _handle_confirmation(self, user_id: str, message: str) -> str:
        """Handle final confirmation"""
        if "はい" in message or "確定" in message or "お願い" in message:
            # Complete the reservation
            reservation_data = self.user_states[user_id]["data"]
            del self.user_states[user_id]  # Clear user state
            
            return f"""✅ 予約が確定いたしました！

📅 日時：{reservation_data['date']} {reservation_data['time']}
💇 サービス：{reservation_data['service']}

当日はお時間までにお越しください。
ご予約ありがとうございました！"""
        else:
            return "予約をキャンセルいたします。またのご利用をお待ちしております。"
    
    def get_response(self, user_id: str, message: str) -> str:
        """Main entry point for reservation flow"""
        intent = self.detect_intent(message)
        
        if intent == "reservation":
            return self.handle_reservation_flow(user_id, message)
        elif intent == "service_inquiry":
            return "サービスについてのご質問ですね。どのサービスについてお聞きになりたいですか？"
        elif intent == "cancel":
            return "予約のキャンセルについてですね。お電話でお問い合わせください。"
        else:
            return None  # Let other systems handle this
