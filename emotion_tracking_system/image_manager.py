"""
Manages loading and serving image pairs with their associated emotions.
"""

import os
import random
import logging
from PIL import Image, ImageTk
import tkinter as tk
from config import IMAGE_DIR, EMOTION_CATEGORIES, IMAGE_WIDTH, IMAGE_HEIGHT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageManager:
    """
    Manages loading and serving images with their associated emotions.
    """
    
    def __init__(self):
        """Initialize the image manager."""
        self.images = {}  # Dictionary to store images by category
        self.image_pairs = []  # List of image pairs to display
        self.current_pair_index = -1  # Index of current image pair
        
    def load_images(self):
        """Load images from the image directory."""
        try:
            # Check if image directory exists
            if not os.path.exists(IMAGE_DIR):
                logger.warning(f"Image directory {IMAGE_DIR} does not exist. Creating it.")
                os.makedirs(IMAGE_DIR)
                
                # Create subdirectories for each emotion category
                for category in EMOTION_CATEGORIES:
                    category_dir = os.path.join(IMAGE_DIR, category)
                    if not os.path.exists(category_dir):
                        os.makedirs(category_dir)
                
                logger.info(f"Please add images to the {IMAGE_DIR} directory and restart the application.")
                return False
            
            # Load images from each category
            for category in EMOTION_CATEGORIES:
                category_dir = os.path.join(IMAGE_DIR, category)
                
                # Skip if category directory doesn't exist
                if not os.path.exists(category_dir):
                    logger.warning(f"Category directory {category_dir} does not exist")
                    continue
                
                # Load images from this category
                self.images[category] = []
                
                for filename in os.listdir(category_dir):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        image_path = os.path.join(category_dir, filename)
                        
                        # Store image path and metadata
                        self.images[category].append({
                            'path': image_path,
                            'category': category,
                            'filename': filename
                        })
                        
                logger.info(f"Loaded {len(self.images[category])} images for category '{category}'")
            
            # Check if we have enough images
            total_images = sum(len(images) for images in self.images.values())
            if total_images < 2:
                logger.warning(f"Not enough images loaded (only {total_images}). Please add more images.")
                return False
                
            # Create image pairs (choosing images from different categories)
            self._create_image_pairs()
            
            return True
                
        except Exception as e:
            logger.error(f"Error loading images: {e}")
            return False
    
    def _create_image_pairs(self):
        """Create exactly 5 pairs of images from different categories, all unique."""
        self.image_pairs = []
        
        # Get categories that have images
        categories_with_images = [cat for cat in self.images if len(self.images[cat]) > 0]
        
        if len(categories_with_images) < 2:
            logger.warning("Not enough categories with images to create pairs")
            return
        
        # Set the fixed number of pairs to create
        num_pairs = 5
        
        # Keep track of pairs we've already created to avoid duplicates
        created_pairs = set()
        
        # Try to create exactly 5 unique pairs
        attempts = 0
        max_attempts = 50  # Prevent infinite loop
        
        while len(self.image_pairs) < num_pairs and attempts < max_attempts:
            attempts += 1
            
            # Choose two different categories
            if len(categories_with_images) >= 2:
                pair_categories = random.sample(categories_with_images, 2)
            else:
                # If only one category has images, use it twice
                pair_categories = [categories_with_images[0], categories_with_images[0]]
            
            # Choose a random image from each category
            left_image = random.choice(self.images[pair_categories[0]])
            right_image = random.choice(self.images[pair_categories[1]])
            
            # Create a unique identifier for this pair to check for duplicates
            pair_id = (left_image['path'], right_image['path'])
            
            # Only add if we haven't already created this exact pair
            if pair_id not in created_pairs:
                self.image_pairs.append({
                    'left': left_image,
                    'right': right_image
                })
                created_pairs.add(pair_id)
        
        # If we couldn't create 5 unique pairs, log a warning
        if len(self.image_pairs) < num_pairs:
            logger.warning(f"Could only create {len(self.image_pairs)} unique pairs instead of {num_pairs}")
        
        logger.info(f"Created {len(self.image_pairs)} image pairs")
    
    def get_next_pair(self):
        """Get the next pair of images to display.
        Note: This method is maintained for compatibility,
        but the UI now accesses image_pairs directly."""
        if not self.image_pairs:
            logger.warning("No image pairs available")
            return None
            
        self.current_pair_index = (self.current_pair_index + 1) % len(self.image_pairs)
        return self.image_pairs[self.current_pair_index]
    
    def get_current_pair(self):
        """Get the current pair of images being displayed."""
        if not self.image_pairs or self.current_pair_index < 0:
            return None
        return self.image_pairs[self.current_pair_index]
    
    def load_image_for_tk(self, image_path):
        """Load an image and resize it for Tkinter display."""
        try:
            img = Image.open(image_path)
            img = img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None
    
    def has_more_pairs(self):
        """Check if there are more image pairs to display."""
        return len(self.image_pairs) > 0 and self.current_pair_index < len(self.image_pairs) - 1