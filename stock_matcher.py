import pandas as pd
import re
from typing import List, Dict
from difflib import SequenceMatcher
import unicodedata
from collections import defaultdict
from rapidfuzz import fuzz, process
import jellyfish  # For phonetic matching

class StockMatcher:
    """
    Advanced stock name matcher using multiple strategies for optimal performance
    """
    
    def __init__(self, csv_or_map):
        """
        Initialize with NSE stock data.
        `csv_or_map` can be a CSV filename or a dict mapping names to tickers.
        """
        if isinstance(csv_or_map, str):  # CSV file path
            df = pd.read_csv(csv_or_map)
            df = df.dropna(subset=['SYMBOL', 'NAME OF COMPANY'])
            self.df = df
        elif isinstance(csv_or_map, dict):  # Direct name->ticker map
            data = [{'SYMBOL': v.replace('.NS', ''), 'NAME OF COMPANY': k} for k, v in csv_or_map.items()]
            self.df = pd.DataFrame(data)
        else:
            raise ValueError("Input must be a CSV file path or a dict mapping company name to ticker.")

        # Create clean datasets
        self.stock_data = self._prepare_data()
        
        # Build indices for fast lookup
        self._build_indices()
        
    def _prepare_data(self) -> List[Dict]:
        """Prepare and clean stock data"""
        stock_data = []
        for _, row in self.df.iterrows():
            symbol = str(row['SYMBOL']).strip()
            name = str(row['NAME OF COMPANY']).strip()
            
            stock_data.append({
                'symbol': symbol,
                'name': name,
                'clean_name': self._clean_text(name),
                'ticker': symbol + '.NS'
            })
        return stock_data
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        text = unicodedata.normalize('NFKD', text)
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        text = ' '.join(text.split())
        return text
    
    def _build_indices(self):
        """Build various indices for fast matching"""
        self.prefix_index = defaultdict(list)
        self.word_index = defaultdict(list)
        self.trigram_index = defaultdict(list)
        self.phonetic_index = defaultdict(list)
        
        for i, stock in enumerate(self.stock_data):
            clean_name = stock['clean_name']
            symbol = stock['symbol'].lower()
            
            # Prefix index
            for prefix_len in range(2, min(len(clean_name) + 1, 5)):
                self.prefix_index[clean_name[:prefix_len]].append(i)
            for prefix_len in range(2, min(len(symbol) + 1, 5)):
                self.prefix_index[symbol[:prefix_len]].append(i)
            
            # Word index
            for word in clean_name.split():
                if len(word) >= 2:
                    self.word_index[word].append(i)
            
            # Trigram index
            for trigram in self._get_trigrams(clean_name):
                self.trigram_index[trigram].append(i)
                
            # Phonetic index
            phonetic = jellyfish.metaphone(clean_name.replace(' ', ''))
            if phonetic:
                self.phonetic_index[phonetic].append(i)
    
    def _get_trigrams(self, text: str) -> List[str]:
        """Generate trigrams"""
        text = f"  {text} "
        return [text[i:i+3] for i in range(len(text) - 2)]
    
    def match_stock(self, query: str, max_results: int = 5) -> List[Dict]:
        """Main matching function"""
        query_clean = self._clean_text(query)
        
        exact_matches = self._exact_match(query, query_clean)
        if exact_matches:
            return exact_matches[:max_results]
        
        prefix_matches = self._prefix_match(query_clean)
        if prefix_matches:
            return self._rank_matches(prefix_matches, query_clean)[:max_results]
        
        word_matches = self._word_match(query_clean)
        if word_matches:
            return self._rank_matches(word_matches, query_clean)[:max_results]
        
        trigram_matches = self._trigram_match(query_clean)
        if trigram_matches:
            return self._rank_matches(trigram_matches, query_clean)[:max_results]
        
        phonetic_matches = self._phonetic_match(query_clean)
        if phonetic_matches:
            return self._rank_matches(phonetic_matches, query_clean)[:max_results]
        
        return self._fuzzy_fallback(query_clean, max_results)
    
    def _exact_match(self, query: str, query_clean: str) -> List[Dict]:
        """Exact matching for symbols and names"""
        matches = []
        query_upper = query.upper()
        
        for stock in self.stock_data:
            if (stock['symbol'] == query_upper or 
                stock['clean_name'] == query_clean or
                query_clean in stock['clean_name']):
                matches.append({
                    'stock': stock,
                    'score': 100,
                    'match_type': 'exact'
                })
        return matches
    
    def _prefix_match(self, query_clean: str) -> List[int]:
        candidates = set()
        for prefix_len in range(2, min(len(query_clean) + 1, 5)):
            prefix = query_clean[:prefix_len]
            if prefix in self.prefix_index:
                candidates.update(self.prefix_index[prefix])
        return list(candidates)
    
    def _word_match(self, query_clean: str) -> List[int]:
        candidates = set()
        for word in query_clean.split():
            if len(word) >= 2 and word in self.word_index:
                candidates.update(self.word_index[word])
        return list(candidates)
    
    def _trigram_match(self, query_clean: str) -> List[int]:
        query_trigrams = set(self._get_trigrams(query_clean))
        candidate_scores = defaultdict(int)
        for trigram in query_trigrams:
            if trigram in self.trigram_index:
                for idx in self.trigram_index[trigram]:
                    candidate_scores[idx] += 1
        min_score = max(1, len(query_trigrams) * 0.3)
        return [idx for idx, score in candidate_scores.items() if score >= min_score]
    
    def _phonetic_match(self, query_clean: str) -> List[int]:
        query_phonetic = jellyfish.metaphone(query_clean.replace(' ', ''))
        if query_phonetic and query_phonetic in self.phonetic_index:
            return self.phonetic_index[query_phonetic]
        return []
    
    def _rank_matches(self, candidate_indices: List[int], query_clean: str) -> List[Dict]:
        matches = []
        for idx in candidate_indices:
            stock = self.stock_data[idx]
            name_similarity = SequenceMatcher(None, query_clean, stock['clean_name']).ratio()
            symbol_similarity = SequenceMatcher(None, query_clean, stock['symbol'].lower()).ratio()
            final_score = max(name_similarity * 0.7 + symbol_similarity * 0.3, 
                              name_similarity, symbol_similarity) * 100
            if final_score >= 30:
                matches.append({
                    'stock': stock,
                    'score': final_score,
                    'match_type': 'similarity'
                })
        return sorted(matches, key=lambda x: x['score'], reverse=True)
    
    def _fuzzy_fallback(self, query_clean: str, max_results: int) -> List[Dict]:
        sample_stocks = self.stock_data
        stock_names = [stock['clean_name'] for stock in sample_stocks]
        fuzzy_results = process.extract(
            query_clean, 
            stock_names, 
            scorer=fuzz.ratio, 
            limit=max_results,
            score_cutoff=60
        )
        matches = []
        for name, score, idx in fuzzy_results:
            matches.append({
                'stock': sample_stocks[idx],
                'score': score,
                'match_type': 'fuzzy'
            })
        return matches