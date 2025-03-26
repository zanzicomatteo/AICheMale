"""
Manages the UI for displaying image pairs and results.
"""

import tkinter as tk
from tkinter import ttk, font
import time
import threading
import logging
from PIL import Image, ImageTk
from config import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, 
    IMAGE_WIDTH, IMAGE_HEIGHT, DISPLAY_TIME_PER_PAIR,
    RESULT_DISPLAY_TIME
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UIManager:
    """
    Manages the UI for displaying image pairs and results.
    """
    
    def __init__(self, image_manager, data_collector):
        """Initialize the UI manager."""
        self.image_manager = image_manager
        self.data_collector = data_collector
        self.root = None
        self.main_frame = None
        self.left_image_label = None
        self.right_image_label = None
        self.info_label = None
        self.emotion_label = None
        self.gaze_label = None
        self.progress_bar = None
        
        self.current_pair = None
        self.current_pair_id = 0
        self.pair_start_time = 0
        self.is_running = False
        self.timer_thread = None
        
        # References to loaded images (to prevent garbage collection)
        self.image_refs = []
        
    def setup_ui(self):
        """Set up the UI components."""
        # Create root window
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg="black")  # Set background to black
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Try to load Poppins font
        try:
            # Check if Poppins font is available on the system
            poppins_font = font.Font(family="Poppins", size=36, weight="bold")
            countdown_font = poppins_font
        except:
            # Fall back to a system font if Poppins is not available
            countdown_font = font.Font(family="Arial", size=36, weight="bold")
            logger.warning("Poppins font not available, using Arial instead")
        
        # Create main frame with black background
        self.main_frame = ttk.Frame(self.root, padding=0)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Apply a custom style for black background
        style = ttk.Style()
        style.configure("Black.TFrame", background="black")
        self.main_frame.configure(style="Black.TFrame")
        
        # Add countdown timer at the top center
        self.countdown_label = tk.Label(
            self.main_frame,
            text="10",
            font=countdown_font,
            fg="white",
            bg="black"
        )
        self.countdown_label.pack(pady=(20, 0))
        
        # Create frame for images with black background
        images_frame = ttk.Frame(self.main_frame, style="Black.TFrame")
        images_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Configure grid to make columns of equal width
        images_frame.columnconfigure(0, weight=1)
        images_frame.columnconfigure(1, weight=1)
        
        # Left image (make it expand to fill space)
        self.left_image_label = tk.Label(
            images_frame,
            bg="black",
            bd=0
        )
        self.left_image_label.grid(row=0, column=0, sticky="nsew", padx=5)
        
        # Right image (make it expand to fill space)
        self.right_image_label = tk.Label(
            images_frame,
            bg="black",
            bd=0
        )
        self.right_image_label.grid(row=0, column=1, sticky="nsew", padx=5)
        
        # Set rowconfigure to make the image row expand
        images_frame.rowconfigure(0, weight=1)
        
        # Hide status labels for emotions
        self.emotion_label = None
        self.gaze_label = None
        
        # Invisible progress bar (we'll just use the countdown)
        self.progress_bar = ttk.Progressbar(
            self.main_frame, 
            length=1,
            mode='determinate'
        )
        
        logger.info("UI setup complete")
        return True
    
    def start(self):
        """Start the UI and begin displaying image pairs."""
        if not self.root:
            if not self.setup_ui():
                return False
                
        # Start with first pair
        self.is_running = True
        self.show_next_pair()
        
        # Start UI main loop
        self.root.mainloop()
        
        return True
    
    def show_next_pair(self):
        """Show the next pair of images."""
        # If we're out of pairs, show results
        if self.current_pair_id >= len(self.image_manager.image_pairs):
            self.show_results()
            return
            
        # Get next pair
        self.current_pair = self.image_manager.image_pairs[self.current_pair_id]
        self.current_pair_id += 1
        
        if not self.current_pair:
            self.show_results()
            return
            
        # Load images
        left_img_path = self.current_pair['left']['path']
        right_img_path = self.current_pair['right']['path']
        
        # Load images at larger size for fullscreen display
        left_tk_img = self.load_fullscreen_image(left_img_path)
        right_tk_img = self.load_fullscreen_image(right_img_path)
        
        # Keep references to images
        self.image_refs = [left_tk_img, right_tk_img]
        
        # Update labels
        self.left_image_label.configure(image=left_tk_img)
        self.right_image_label.configure(image=right_tk_img)
        
        # Reset progress bar
        self.progress_bar['value'] = 0
        
        # Reset countdown
        self.countdown_label.configure(text=str(DISPLAY_TIME_PER_PAIR))
        
        # Start data collection for this pair
        self.data_collector.start_pair(
            self.current_pair_id,
            self.current_pair['left'],
            self.current_pair['right']
        )
        
        # Start timer for this pair
        self.pair_start_time = time.time()
        self.start_pair_timer()
        
        logger.info(f"Showing pair {self.current_pair_id}: {left_img_path} vs {right_img_path}")
    
    def load_fullscreen_image(self, image_path):
        """Load an image at a size appropriate for fullscreen display."""
        try:
            # Calculate the size for each image (half screen width minus padding)
            img_width = (WINDOW_WIDTH // 2) - 20
            img_height = WINDOW_HEIGHT - 100  # Leave room for countdown
            
            img = Image.open(image_path)
            
            # Maintain aspect ratio
            original_width, original_height = img.size
            ratio = min(img_width/original_width, img_height/original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            
            img = img.resize((new_width, new_height), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None
    
    def start_pair_timer(self):
        """Start a timer for the current pair."""
        if self.timer_thread and self.timer_thread.is_alive():
            return
            
        self.timer_thread = threading.Thread(target=self._pair_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()
    
    def _pair_timer(self):
        """Timer function for tracking pair display time."""
        start_time = time.time()
        total_seconds = DISPLAY_TIME_PER_PAIR
        
        while self.is_running:
            elapsed = time.time() - start_time
            
            if elapsed >= total_seconds:
                # Time's up for this pair
                self.data_collector.end_pair()
                
                # Switch to next pair
                self.root.after(0, self.show_next_pair)
                break
                
            # Update countdown timer
            seconds_left = max(0, int(total_seconds - elapsed))
            self.root.after(0, lambda s=seconds_left: self.countdown_label.configure(text=str(s)))
            
            # Update progress bar (invisible but needed for functionality)
            progress = (elapsed / total_seconds) * 100
            self.root.after(0, lambda p=progress: self.progress_bar.configure(value=p))
            
            # Small sleep to prevent CPU hogging
            time.sleep(0.05)
    
    def update_emotion_display(self, emotion_data):
        """Update the displayed emotion information."""
        # No longer displaying emotion text
        pass
    
    def update_gaze_display(self, gaze_data):
        """Update the displayed gaze information."""
        # No longer displaying gaze text
        pass
    
    def show_results(self):
        """Show the results of the session."""
        logger.info("Showing results")
        
        # Clear images
        self.left_image_label.configure(image='')
        self.right_image_label.configure(image='')
        self.image_refs = []
        
        # Hide countdown
        self.countdown_label.configure(text="")
        
        # Analyze data
        results = self.data_collector.analyze_session()
        
        # Save results
        self.data_collector.save_results(results)
        
        # Clear the main frame for results display
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        # Create a results container with black background
        results_container = tk.Frame(self.main_frame, bg="black")
        results_container.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)
        
        # Add a "Session Complete" header
        header_label = tk.Label(
            results_container,
            text="Experience Complete",
            font=font.Font(family="Arial", size=32, weight="bold"),
            fg="white",
            bg="black"
        )
        header_label.pack(pady=(20, 40))
        
        # Extract dominant emotion and where the user looked the most
        dominant_emotion = results.get('overall_emotions', {}).get('dominant', 'neutral')
        favorite_category = results.get('favorite_categories', {}).get('favorite', 'unknown')
        
        # Calculate combined emotion based on gaze and detected emotions
        # Get the emotional response to the type of image they looked at the most
        pair_emotions = {}
        for pair in results.get('pairs', []):
            gaze_dist = pair.get('gaze_distribution', {})
            preferred = gaze_dist.get('preferred', 'none')
            if preferred in ('left', 'right'):
                category = pair.get(f'{preferred}_image', {}).get('category', 'unknown')
                emotion = pair.get('emotions', {}).get('dominant', 'neutral')
                if category not in pair_emotions:
                    pair_emotions[category] = []
                pair_emotions[category].append(emotion)
        
        # Create a meaningful insight about what they responded to
        insight_text = f"Dominant Emotion: {dominant_emotion.upper()}"
        if favorite_category != 'unknown':
            insight_text += f"\nPreferred Images: {favorite_category.upper()}"
            
            # If we have emotion data for the favorite category
            if favorite_category in pair_emotions and pair_emotions[favorite_category]:
                # Count emotions for this category
                emotion_counts = {}
                for emotion in pair_emotions[favorite_category]:
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                most_common_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
                insight_text += f"\nEmotional Response to {favorite_category.upper()}: {most_common_emotion.upper()}"
        
        # Display the minimal emotion result with larger font
        emotion_label = tk.Label(
            results_container,
            text=insight_text,
            font=font.Font(family="Arial", size=24),
            fg="white",
            bg="black",
            justify=tk.CENTER
        )
        emotion_label.pack(pady=30)
        
        # Add buttons container
        button_container = tk.Frame(results_container, bg="black")
        button_container.pack(pady=40)
        
        # Add a button to view detailed logs
        log_button = tk.Button(
            button_container,
            text="View Detailed Logs",
            font=font.Font(family="Arial", size=16),
            command=self.show_detailed_logs,
            bg="black",
            fg="white",
            activebackground="gray25",
            activeforeground="white",
            bd=1,
            relief=tk.RAISED,
            padx=20,
            pady=10
        )
        log_button.pack(side=tk.LEFT, padx=20)
        
        # Add a button to exit
        exit_button = tk.Button(
            button_container,
            text="Exit",
            font=font.Font(family="Arial", size=16),
            command=self.on_close,
            bg="black",
            fg="white",
            activebackground="gray25",
            activeforeground="white",
            bd=1,
            relief=tk.RAISED,
            padx=20,
            pady=10
        )
        exit_button.pack(side=tk.LEFT, padx=20)
        
        # Store results for detailed logs view
        self.session_results = results
        
        # Auto-close after timeout
        self.root.after(
            int(RESULT_DISPLAY_TIME * 1000),
            self.on_close
        )
        
    def show_detailed_logs(self):
        """Show detailed logs for each image pair."""
        # Create a new window for detailed logs
        log_window = tk.Toplevel(self.root)
        log_window.title("Detailed Session Logs")
        log_window.geometry("800x600")
        log_window.configure(bg="black")
        
        # Add a title
        title_label = tk.Label(
            log_window,
            text="Detailed Session Logs",
            font=font.Font(family="Arial", size=18, weight="bold"),
            fg="white",
            bg="black"
        )
        title_label.pack(pady=(20, 30))
        
        # Create a frame for the text widget
        text_frame = tk.Frame(log_window, bg="black")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Create a text widget with a dark theme
        log_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            height=25,
            width=80,
            font=font.Font(family="Courier", size=12),
            fg="white",
            bg="gray10",
            insertbackground="white"
        )
        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(text_frame, command=log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        log_text.configure(yscrollcommand=scrollbar.set)
        
        # Generate and insert detailed logs
        log_content = self.data_collector.get_summary_text(self.session_results)
        log_text.insert(tk.END, log_content)
        log_text.config(state=tk.DISABLED)  # Make read-only
        
        # Add a close button
        close_button = tk.Button(
            log_window,
            text="Close",
            font=font.Font(family="Arial", size=14),
            command=log_window.destroy,
            bg="black",
            fg="white",
            activebackground="gray25",
            activeforeground="white",
            bd=1,
            relief=tk.RAISED,
            padx=20,
            pady=5
        )
        close_button.pack(pady=20)
    
    def on_close(self):
        """Handle window close event."""
        logger.info("Closing application")
        self.is_running = False
        
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=1.0)
            
        # End current pair if one is active
        self.data_collector.end_pair()
        
        if self.root:
            self.root.destroy()