"""
Collects and analyzes data about gaze patterns and emotions.
"""

import time
import json
import logging
import pandas as pd
import numpy as np
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataCollector:
    """
    Collects and analyzes data about gaze patterns and emotions.
    """
    
    def __init__(self):
        """Initialize the data collector."""
        self.session_data = []
        self.current_pair_data = {
            'pair_id': None,
            'start_time': None,
            'end_time': None,
            'left_image': {},
            'right_image': {},
            'gaze_samples': [],
            'emotion_samples': []
        }
        
    def start_pair(self, pair_id, left_image, right_image):
        """Start data collection for a new image pair."""
        # Save previous pair data if it exists
        if self.current_pair_data['pair_id'] is not None:
            self.end_pair()
            
        # Initialize data for new pair
        self.current_pair_data = {
            'pair_id': pair_id,
            'start_time': time.time(),
            'end_time': None,
            'left_image': left_image,
            'right_image': right_image,
            'gaze_samples': [],
            'emotion_samples': []
        }
        
        logger.info(f"Started data collection for pair {pair_id}")
    
    def add_gaze_sample(self, gaze_data):
        """Add a gaze sample to the current pair data."""
        if self.current_pair_data['pair_id'] is None:
            return
            
        # Add timestamp to gaze data
        sample = gaze_data.copy()
        sample['timestamp'] = time.time()
        
        self.current_pair_data['gaze_samples'].append(sample)
    
    def add_emotion_sample(self, emotion_data):
        """Add an emotion sample to the current pair data."""
        if self.current_pair_data['pair_id'] is None:
            return
            
        # Add timestamp if not present
        sample = emotion_data.copy()
        if 'timestamp' not in sample:
            sample['timestamp'] = time.time()
            
        self.current_pair_data['emotion_samples'].append(sample)
    
    def end_pair(self):
        """End data collection for the current image pair."""
        if self.current_pair_data['pair_id'] is None:
            return
            
        # Record end time
        self.current_pair_data['end_time'] = time.time()
        
        # Add to session data
        self.session_data.append(self.current_pair_data.copy())
        
        logger.info(f"Ended data collection for pair {self.current_pair_data['pair_id']}")
        
        # Clear current pair data
        self.current_pair_data = {
            'pair_id': None,
            'start_time': None,
            'end_time': None,
            'left_image': {},
            'right_image': {},
            'gaze_samples': [],
            'emotion_samples': []
        }
    
    def analyze_session(self):
        """Analyze collected data for the entire session."""
        if not self.session_data:
            logger.warning("No session data to analyze")
            return {}
            
        results = {
            'pairs': [],
            'overall_emotions': self._analyze_overall_emotions(),
            'favorite_categories': self._analyze_favorite_categories(),
            'session_duration': self._calculate_session_duration()
        }
        
        # Analyze each pair
        for pair_data in self.session_data:
            pair_results = self._analyze_pair(pair_data)
            results['pairs'].append(pair_results)
            
        return results
    
    def _analyze_pair(self, pair_data):
        """Analyze data for a single image pair."""
        # Extract basic information
        pair_id = pair_data['pair_id']
        left_image = pair_data['left_image']
        right_image = pair_data['right_image']
        duration = pair_data['end_time'] - pair_data['start_time']
        
        # Calculate gaze distribution
        gaze_results = self._analyze_gaze_distribution(pair_data)
        
        # Analyze emotions for this pair
        emotion_results = self._analyze_emotions_for_pair(pair_data)
        
        return {
            'pair_id': pair_id,
            'duration': duration,
            'left_image': left_image,
            'right_image': right_image,
            'gaze_distribution': gaze_results,
            'emotions': emotion_results
        }
    
    def _analyze_gaze_distribution(self, pair_data):
        """Analyze where the user was looking during this pair."""
        gaze_samples = pair_data['gaze_samples']
        
        if not gaze_samples:
            return {'left': 0, 'right': 0, 'outside': 1.0}
            
        # Determine screen center and image boundaries
        # This is a simplification - in reality, you'd need the actual UI dimensions
        left_count = 0
        right_count = 0
        outside_count = 0
        
        for sample in gaze_samples:
            gaze_x = sample.get('GazeX', 0)
            
            # Simple logic: left half of screen = left image, right half = right image
            # This should be replaced with actual image boundaries in the UI
            if gaze_x < 0.4:  # Assuming GazeX is normalized 0-1
                left_count += 1
            elif gaze_x > 0.6:
                right_count += 1
            else:
                outside_count += 1
                
        total_samples = left_count + right_count + outside_count
        
        if total_samples == 0:
            return {'left': 0, 'right': 0, 'outside': 1.0}
            
        return {
            'left': left_count / total_samples,
            'right': right_count / total_samples,
            'outside': outside_count / total_samples,
            'preferred': 'left' if left_count > right_count else 'right',
            'left_count': left_count,
            'right_count': right_count,
            'outside_count': outside_count
        }
    
    def _analyze_emotions_for_pair(self, pair_data):
        """Analyze emotions detected during this pair."""
        emotion_samples = pair_data['emotion_samples']
        
        if not emotion_samples:
            return {'dominant': 'neutral', 'counts': {'neutral': 1}}
            
        # Count occurrences of each emotion
        emotion_counts = defaultdict(int)
        for sample in emotion_samples:
            emotion = sample.get('emotion', 'neutral')
            # Replace 'unknown' with 'neutral' to avoid showing unknown emotions
            if emotion == 'unknown':
                emotion = 'neutral'
            emotion_counts[emotion] += 1
            
        # If no valid emotions were detected, set a default
        if not emotion_counts:
            emotion_counts['neutral'] = 1
            
        # Find dominant emotion
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        
        # Calculate average emotion scores
        emotion_scores = defaultdict(list)
        for sample in emotion_samples:
            scores = sample.get('emotion_scores', {})
            for emotion, score in scores.items():
                emotion_scores[emotion].append(score)
                
        avg_scores = {emotion: np.mean(scores) for emotion, scores in emotion_scores.items()}
        
        return {
            'dominant': dominant_emotion,
            'counts': dict(emotion_counts),
            'average_scores': avg_scores
        }
    
    def _analyze_overall_emotions(self):
        """Analyze emotions across the entire session."""
        # Combine all emotion samples
        all_emotions = []
        for pair_data in self.session_data:
            all_emotions.extend(pair_data['emotion_samples'])
            
        if not all_emotions:
            return {'dominant': 'neutral', 'counts': {'neutral': 1}}
            
        # Count occurrences of each emotion
        emotion_counts = defaultdict(int)
        for sample in all_emotions:
            emotion = sample.get('emotion', 'neutral')
            # Replace 'unknown' with 'neutral' to avoid showing unknown emotions
            if emotion == 'unknown':
                emotion = 'neutral'
            emotion_counts[emotion] += 1
            
        # If no valid emotions were detected, set a default
        if not emotion_counts:
            emotion_counts['neutral'] = 1
            
        # Find dominant emotion
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        
        # Calculate average emotion scores
        emotion_scores = defaultdict(list)
        for sample in all_emotions:
            scores = sample.get('emotion_scores', {})
            for emotion, score in scores.items():
                emotion_scores[emotion].append(score)
                
        avg_scores = {emotion: np.mean(scores) for emotion, scores in emotion_scores.items()}
        
        return {
            'dominant': dominant_emotion,
            'counts': dict(emotion_counts),
            'average_scores': avg_scores
        }
    
    def _analyze_favorite_categories(self):
        """Determine which image categories the user preferred."""
        category_gaze_time = defaultdict(float)
        
        for pair_data in self.session_data:
            gaze_dist = self._analyze_gaze_distribution(pair_data)
            
            # Add gaze time to categories
            left_category = pair_data['left_image'].get('category', 'unknown')
            right_category = pair_data['right_image'].get('category', 'unknown')
            
            category_gaze_time[left_category] += gaze_dist['left']
            category_gaze_time[right_category] += gaze_dist['right']
            
        # Sort categories by gaze time
        sorted_categories = sorted(category_gaze_time.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'favorite': sorted_categories[0][0] if sorted_categories else 'unknown',
            'rankings': dict(sorted_categories)
        }
    
    def _calculate_session_duration(self):
        """Calculate total session duration."""
        if not self.session_data:
            return 0
            
        start_time = min(pair['start_time'] for pair in self.session_data)
        end_time = max(pair['end_time'] for pair in self.session_data)
        
        return end_time - start_time
    
    def get_summary_text(self, results):
        """Generate a user-friendly text summary of the results."""
        if not results:
            return "No data collected."
            
        summary = []
        
        # Overall session info
        duration = results.get('session_duration', 0)
        summary.append(f"Session Duration: {duration:.1f} seconds")
        
        # Overall emotions
        overall_emotions = results.get('overall_emotions', {})
        dominant_emotion = overall_emotions.get('dominant', 'unknown')
        summary.append(f"Dominant Emotion: {dominant_emotion}")
        
        # Emotion breakdown
        emotion_counts = overall_emotions.get('counts', {})
        if emotion_counts:
            summary.append("\nEmotion Breakdown:")
            total_emotions = sum(emotion_counts.values())
            for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_emotions) * 100
                summary.append(f"- {emotion}: {percentage:.1f}%")
                
        # Favorite categories
        favorite_categories = results.get('favorite_categories', {})
        favorite = favorite_categories.get('favorite', 'unknown')
        summary.append(f"\nFavorite Image Category: {favorite}")
        
        # Category rankings
        rankings = favorite_categories.get('rankings', {})
        if rankings:
            summary.append("\nCategory Preferences:")
            total = sum(rankings.values())
            for category, score in sorted(rankings.items(), key=lambda x: x[1], reverse=True):
                percentage = (score / total) * 100
                summary.append(f"- {category}: {percentage:.1f}%")
                
        # Image pair details
        pairs = results.get('pairs', [])
        if pairs:
            summary.append("\nImage Pair Details:")
            for i, pair in enumerate(pairs):
                left_image = pair.get('left_image', {})
                right_image = pair.get('right_image', {})
                left_category = left_image.get('category', 'unknown')
                right_category = right_image.get('category', 'unknown')
                
                gaze_dist = pair.get('gaze_distribution', {})
                preferred = gaze_dist.get('preferred', 'unknown')
                left_pct = gaze_dist.get('left', 0) * 100
                right_pct = gaze_dist.get('right', 0) * 100
                
                emotions = pair.get('emotions', {})
                pair_emotion = emotions.get('dominant', 'unknown')
                
                summary.append(f"\nPair {i+1}:")
                summary.append(f"- Left: {left_category} image ({left_pct:.1f}% of gaze)")
                summary.append(f"- Right: {right_category} image ({right_pct:.1f}% of gaze)")
                summary.append(f"- Preferred: {preferred} image")
                summary.append(f"- Dominant emotion: {pair_emotion}")
                
        return "\n".join(summary)
    
    def save_results(self, results, filename="emotion_tracking_results.json"):
        """Save results to a JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return False