"""
Conversation Manager for Knowledge Agent
Implements context-aware conversation memory and chat history tracking.

This module enables the agent to:
- Remember previous questions and answers
- Maintain conversation context for follow-up queries
- Track user preferences and interaction patterns
- Provide personalized responses based on history
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict


class ConversationManager:
    """
    Manages conversation history and context for the Knowledge Agent.
    
    Features:
    - Chat history tracking with timestamps
    - Context-aware query understanding
    - User preference learning
    - Conversation summarization
    - Memory retrieval for relevant past interactions
    """
    
    def __init__(self, max_history: int = 50):
        """
        Initialize the conversation manager.
        
        Args:
            max_history: Maximum number of conversation turns to keep
        """
        self.max_history = max_history
        self.conversation_history: List[Dict[str, Any]] = []
        self.user_preferences: Dict[str, Any] = {
            'preferred_viz_types': [],
            'topics_of_interest': [],
            'detail_level': 'medium',  # low, medium, high
            'technical_level': 'medium'  # beginner, medium, expert
        }
        self.topic_counts = defaultdict(int)
        self.session_start = datetime.now()
        self.total_queries = 0
        
    def add_interaction(
        self, 
        query: str, 
        response: Any, 
        query_type: str = 'general',
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Add a new interaction to conversation history.
        
        Args:
            query: User's question or request
            response: Agent's response
            query_type: Type of query (question, analysis, visualization, etc.)
            metadata: Additional metadata about the interaction
        """
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response,
            'query_type': query_type,
            'metadata': metadata or {}
        }
        
        self.conversation_history.append(interaction)
        self.total_queries += 1
        
        # Track topics
        self.topic_counts[query_type] += 1
        
        # Maintain max history limit
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)
    
    def get_conversation_context(self, n_recent: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent conversation context for LLM prompting.
        
        Args:
            n_recent: Number of recent interactions to retrieve
            
        Returns:
            List of recent interactions
        """
        return self.conversation_history[-n_recent:]
    
    def format_context_for_llm(self, n_recent: int = 3) -> str:
        """
        Format recent conversation context for LLM input.
        
        Args:
            n_recent: Number of recent interactions to include
            
        Returns:
            Formatted context string
        """
        recent = self.get_conversation_context(n_recent)
        
        if not recent:
            return "No previous conversation context."
        
        context_parts = ["Previous conversation:"]
        for i, interaction in enumerate(recent, 1):
            query = interaction['query']
            # Truncate long responses for context
            response_preview = str(interaction['response'])[:200]
            if len(str(interaction['response'])) > 200:
                response_preview += "..."
            
            context_parts.append(f"\n{i}. User: {query}")
            context_parts.append(f"   Agent: {response_preview}")
        
        return "\n".join(context_parts)
    
    def detect_follow_up(self, query: str) -> bool:
        """
        Detect if query is a follow-up to previous conversation.
        
        Args:
            query: User's query
            
        Returns:
            True if query appears to be a follow-up
        """
        if not self.conversation_history:
            return False
        
        # Follow-up indicators
        follow_up_words = [
            'also', 'additionally', 'furthermore', 'moreover',
            'what about', 'how about', 'and', 'but',
            'that', 'those', 'them', 'it', 'this', 'these',
            'more details', 'elaborate', 'explain further'
        ]
        
        query_lower = query.lower()
        return any(word in query_lower for word in follow_up_words)
    
    def get_related_history(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history related to current query.
        
        Args:
            query: Current user query
            limit: Maximum number of related interactions to return
            
        Returns:
            List of related past interactions
        """
        if not self.conversation_history:
            return []
        
        # Simple keyword-based relevance matching
        query_words = set(query.lower().split())
        related = []
        
        for interaction in reversed(self.conversation_history):
            past_query = interaction['query'].lower()
            past_words = set(past_query.split())
            
            # Calculate word overlap
            overlap = len(query_words & past_words)
            if overlap >= 2:  # At least 2 words in common
                related.append({
                    **interaction,
                    'relevance_score': overlap
                })
        
        # Sort by relevance and return top matches
        related.sort(key=lambda x: x['relevance_score'], reverse=True)
        return related[:limit]
    
    def update_preferences(self, preference_type: str, value: Any) -> None:
        """
        Update user preferences based on interactions.
        
        Args:
            preference_type: Type of preference (viz_type, topic, etc.)
            value: Preference value
        """
        if preference_type == 'viz_type':
            if value not in self.user_preferences['preferred_viz_types']:
                self.user_preferences['preferred_viz_types'].append(value)
        elif preference_type == 'topic':
            if value not in self.user_preferences['topics_of_interest']:
                self.user_preferences['topics_of_interest'].append(value)
        elif preference_type in self.user_preferences:
            self.user_preferences[preference_type] = value
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Generate summary of conversation session.
        
        Returns:
            Dictionary with conversation statistics and insights
        """
        if not self.conversation_history:
            return {
                'total_queries': 0,
                'session_duration': '0 minutes',
                'topics_discussed': [],
                'most_common_query_type': None
            }
        
        # Calculate session duration
        duration = datetime.now() - self.session_start
        duration_minutes = int(duration.total_seconds() / 60)
        
        # Find most common query type
        most_common = max(self.topic_counts.items(), key=lambda x: x[1])
        
        return {
            'total_queries': self.total_queries,
            'session_duration': f'{duration_minutes} minutes',
            'topics_discussed': list(self.topic_counts.keys()),
            'most_common_query_type': most_common[0],
            'query_distribution': dict(self.topic_counts),
            'user_preferences': self.user_preferences
        }
    
    def search_history(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search conversation history for specific keyword.
        
        Args:
            keyword: Keyword to search for
            
        Returns:
            List of matching interactions
        """
        keyword_lower = keyword.lower()
        matches = []
        
        for interaction in self.conversation_history:
            if keyword_lower in interaction['query'].lower():
                matches.append(interaction)
        
        return matches
    
    def export_history(self, filepath: str) -> None:
        """
        Export conversation history to JSON file.
        
        Args:
            filepath: Path to save conversation history
        """
        export_data = {
            'session_start': self.session_start.isoformat(),
            'total_queries': self.total_queries,
            'conversation_history': self.conversation_history,
            'user_preferences': self.user_preferences,
            'topic_counts': dict(self.topic_counts)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
    
    def import_history(self, filepath: str) -> None:
        """
        Import conversation history from JSON file.
        
        Args:
            filepath: Path to conversation history file
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.conversation_history = data.get('conversation_history', [])
        self.user_preferences = data.get('user_preferences', self.user_preferences)
        self.total_queries = data.get('total_queries', 0)
        
        # Rebuild topic counts
        self.topic_counts = defaultdict(int)
        for interaction in self.conversation_history:
            self.topic_counts[interaction.get('query_type', 'general')] += 1
    
    def clear_history(self) -> None:
        """Clear all conversation history."""
        self.conversation_history = []
        self.topic_counts = defaultdict(int)
        self.total_queries = 0
        self.session_start = datetime.now()
    
    def get_last_n_queries(self, n: int = 5) -> List[str]:
        """
        Get the last n user queries.
        
        Args:
            n: Number of queries to retrieve
            
        Returns:
            List of recent queries
        """
        return [
            interaction['query'] 
            for interaction in self.conversation_history[-n:]
        ]
    
    def get_response_for_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Find a previous response for an exact or similar query.
        
        Args:
            query: Query to search for
            
        Returns:
            Previous interaction if found, None otherwise
        """
        query_lower = query.lower().strip()
        
        # Check for exact match first
        for interaction in reversed(self.conversation_history):
            if interaction['query'].lower().strip() == query_lower:
                return interaction
        
        return None
    
    def __repr__(self) -> str:
        """String representation of conversation manager."""
        return (
            f"ConversationManager("
            f"queries={self.total_queries}, "
            f"history_length={len(self.conversation_history)}, "
            f"topics={len(self.topic_counts)})"
        )
