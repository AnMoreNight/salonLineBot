"""
RAG-FAQ system that only uses KB data as the source of truth
Lightweight version for Vercel deployment
"""
import json
import os
import re
from typing import List, Dict, Any, Optional

class RAGFAQ:
    def __init__(self, faq_data_path: str = "api/data/faq_data.json", kb_data_path: str = "api/data/kb.json"):
        self.faq_data = self._load_faq_data(faq_data_path)
        self.kb_data = self._load_kb_data(kb_data_path)
        self._build_keyword_index()
    
    def _load_faq_data(self, path: str) -> List[Dict[str, Any]]:
        """Load FAQ data from JSON file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading FAQ data: {e}")
            return []
    
    def _load_kb_data(self, path: str) -> Dict[str, str]:
        """Load KB data from JSON file and convert to key-value mapping"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                kb_list = json.load(f)
            
            # Convert list of dicts to key-value mapping
            kb_dict = {}
            for item in kb_list:
                key = item.get('キー', '')
                value = item.get('例（置換値）', '')
                if key and value:
                    kb_dict[key] = value
            
            return kb_dict
        except Exception as e:
            print(f"Error loading KB data: {e}")
            return {}
    
    def _build_keyword_index(self):
        """Build lightweight keyword index for FAQ questions"""
        if not self.faq_data:
            return
        
        self.keyword_index = []
        for item in self.faq_data:
            question = item.get('question', '').lower()
            answer_template = item.get('answer_template', '').lower()
            
            # Extract keywords from question and answer
            keywords = self._extract_keywords(question + ' ' + answer_template)
            
            self.keyword_index.append({
                'item': item,
                'keywords': keywords,
                'question': question,
                'answer_template': answer_template
            })
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for matching"""
        # Remove common Japanese particles and words
        stop_words = ['は', 'が', 'を', 'に', 'で', 'と', 'の', 'です', 'ます', 'です', 'か', 'の', 'を', 'に', 'で', 'と', 'は', 'が']
        
        # Simple keyword extraction
        words = re.findall(r'[a-zA-Z\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+', text)
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        
        return keywords
    
    def search(self, query: str, threshold: float = 0.3) -> Optional[Dict[str, Any]]:
        """
        Search for KB facts using lightweight keyword matching
        Returns None if no good match found (KB only approach)
        """
        if not self.faq_data or not hasattr(self, 'keyword_index'):
            return None
        
        query_lower = query.lower()
        query_keywords = self._extract_keywords(query_lower)
        
        best_match = None
        best_score = 0
        
        for index_item in self.keyword_index:
            # Calculate keyword overlap score
            overlap = len(set(query_keywords) & set(index_item['keywords']))
            total_keywords = len(set(query_keywords) | set(index_item['keywords']))
            
            if total_keywords > 0:
                score = overlap / total_keywords
                
                # Also check for direct text matches
                if any(keyword in index_item['question'] for keyword in query_keywords):
                    score += 0.2
                
                if score > best_score:
                    best_score = score
                    best_match = index_item
        
        # Only return if similarity is above threshold
        if best_match and best_score >= threshold:
            faq_item = best_match['item']
            
            # Extract KB facts (replace placeholders with actual data)
            kb_facts = self._extract_kb_facts(faq_item)
            
            return {
                'faq_item': faq_item,
                'similarity_score': float(best_score),
                'kb_facts': kb_facts,
                'category': faq_item.get('category', ''),
                'question': faq_item.get('question', '')
            }
        
        return None

    def _extract_kb_facts(self, faq_item: Dict[str, Any]) -> Dict[str, str]:
        """Extract KB facts from FAQ item with actual salon data"""
        answer_template = faq_item.get('answer_template', '')
        
        # Replace placeholders with actual KB data
        kb_facts = {}
        for key, value in self.kb_data.items():
            if f'{{{key}}}' in answer_template:
                kb_facts[key] = value
        
        return kb_facts

    def get_kb_facts(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Get KB facts only - for use by ChatGPT
        Returns None if not found in KB
        """
        return self.search(user_message)
