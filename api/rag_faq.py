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
        Search for KB facts only - returns raw KB data, not formatted answers
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
            faq_item = self.faq_data[best_match_idx]
            
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
