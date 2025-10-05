"""
RAG-FAQ system that only uses KB data as the source of truth
"""
import json
import os
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class RAGFAQ:
    def __init__(self, faq_data_path: str = "api/data/faq_data.json", kb_data_path: str = "api/data/kb.json"):
        self.faq_data = self._load_faq_data(faq_data_path)
        self.kb_data = self._load_kb_data(kb_data_path)
        self.vectorizer = TfidfVectorizer()
        self._build_search_index()
    
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
    
    def _build_search_index(self):
        """Build TF-IDF search index for FAQ questions"""
        if not self.faq_data:
            return
        
        # Combine question and answer for better matching
        documents = []
        for item in self.faq_data:
            doc = f"{item.get('question', '')} {item.get('answer_template', '')}"
            documents.append(doc)
        
        if documents:
            self.tfidf_matrix = self.vectorizer.fit_transform(documents)
    
    def search(self, query: str, threshold: float = 0.3) -> Optional[Dict[str, Any]]:
        """
        Search for the best matching FAQ entry
        Returns None if no good match found (KB only approach)
        """
        if not self.faq_data or not hasattr(self, 'tfidf_matrix'):
            return None
        
        # Vectorize the query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Find the best match
        best_match_idx = np.argmax(similarity_scores)
        best_score = similarity_scores[best_match_idx]
        
        # Only return if similarity is above threshold
        if best_score >= threshold:
            return {
                'faq_item': self.faq_data[best_match_idx],
                'similarity_score': float(best_score),
                'answer': self._format_answer(self.faq_data[best_match_idx])
            }
        
        return None
    
    def _format_answer(self, faq_item: Dict[str, Any]) -> str:
        """Format the answer with actual salon information from KB data"""
        answer_template = faq_item.get('answer_template', '')
        
        # Use actual KB data for replacements
        formatted_answer = answer_template
        for key, value in self.kb_data.items():
            formatted_answer = formatted_answer.replace(f'{{{key}}}', value)
        
        return formatted_answer
    
    def get_response(self, user_message: str) -> str:
        """
        Get RAG-based response
        Returns "分かりません" if not found in KB
        """
        result = self.search(user_message)
        
        if result:
            return result['answer']
        else:
            return "申し訳ございませんが、その質問については分かりません。お電話でお問い合わせください。"
