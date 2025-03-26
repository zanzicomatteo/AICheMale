"""
WebSocket bridge to connect the Python emotion tracking system with the Electron app.
"""

import asyncio
import json
import logging
import websockets
from websockets.server import serve  # Added this import
from gaze_tracker import GazeTracker
from emotion_detector import EmotionDetector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebSocketBridge:
    """
    Bridge to facilitate communication between Python emotion tracking and Electron app.
    """
    
    def __init__(self, host="127.0.0.1", port=8765):
        """Initialize the WebSocket bridge."""
        self.host = host
        self.port = port
        self.clients = set()
        self.gaze_tracker = None
        self.emotion_detector = None
        self.combined_data = {
            "gaze": {"GazeX": 0.5, "GazeY": 0.5},
            "emotion": {
                "emotion": "neutral",
                "emotion_scores": {
                    "happy": 0.1,
                    "sad": 0.1,
                    "neutral": 0.5,
                    "surprise": 0.1,
                    "angry": 0.1,
                    "fear": 0.05,
                    "disgust": 0.05
                },
                "face_detected": False
            }
        }
        self.running = False
        self.server = None
    
    async def ws_handler(self, websocket):
        """Handle WebSocket connections."""
        # Register client
        self.clients.add(websocket)
        logger.info(f"New client connected. Total clients: {len(self.clients)}")
        
        try:
            # Listen for client messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    # Handle client commands
                    if "command" in data:
                        if data["command"] == "start_tracking":
                            logger.info("Received start_tracking command")
                            # Any specific start logic can go here
                            
                        elif data["command"] == "stop_tracking":
                            logger.info("Received stop_tracking command")
                            # Any specific stop logic can go here
                            
                        elif data["command"] == "calibrate":
                            logger.info("Received calibrate command")
                            # Calibration logic would go here
                            
                        # Respond to client with acknowledgment
                        await websocket.send(json.dumps({
                            "type": "command_response",
                            "command": data["command"],
                            "status": "success"
                        }))
                    
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid JSON: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed")
        finally:
            # Unregister client
            self.clients.remove(websocket)
            logger.info(f"Client disconnected. Remaining clients: {len(self.clients)}")
    
    def update_data(self, gaze_data=None, emotion_data=None):
        """Update the combined data with new gaze and emotion information."""
        if gaze_data:
            self.combined_data["gaze"] = {
                "GazeX": gaze_data.get("GazeX", 0.5),
                "GazeY": gaze_data.get("GazeY", 0.5)
            }
        
        if emotion_data:
            self.combined_data["emotion"] = {
                "emotion": emotion_data.get("emotion", "neutral"),
                "emotion_scores": emotion_data.get("emotion_scores", {
                    "happy": 0.1,
                    "sad": 0.1,
                    "neutral": 0.5,
                    "surprise": 0.1,
                    "angry": 0.1,
                    "fear": 0.05,
                    "disgust": 0.05
                }),
                "face_detected": emotion_data.get("face_detected", False),
                "confidence": self._calculate_confidence(emotion_data.get("emotion_scores", {}))
            }
    
    def _calculate_confidence(self, emotion_scores):
        """Calculate confidence score for the primary emotion."""
        if not emotion_scores:
            return 0
            
        # Find the highest emotion score
        max_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        max_score = max_emotion[1]
        
        # Convert to percentage
        confidence = int(max_score * 100)
        
        return confidence
    
    async def broadcast_data(self):
        """Broadcast current data to all connected clients."""
        if not self.clients:
            return
            
        # Create a message with the combined data
        message = json.dumps({
            "type": "tracking_data",
            "data": self.combined_data
        })
        
        # Send to all connected clients
        for client in self.clients.copy():
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                # Client disconnected, will be removed on next message attempt
                pass
    
    def gaze_callback(self, gaze_data):
        """Callback function for GazeTracker."""
        self.update_data(gaze_data=gaze_data)
    
    def emotion_callback(self, emotion_data):
        """Callback function for EmotionDetector."""
        self.update_data(emotion_data=emotion_data)
    
    async def start_server(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        self.server = await serve(self.ws_handler, self.host, self.port)
        self.running = True
        
        # Start the periodic broadcast task
        asyncio.create_task(self._periodic_broadcast())
        
        logger.info("WebSocket server started")
    
    async def _periodic_broadcast(self):
        """Periodically broadcast data to all clients."""
        while self.running:
            await self.broadcast_data()
            await asyncio.sleep(0.1)  # 10 times per second
    
    async def stop_server(self):
        """Stop the WebSocket server."""
        if self.server:
            self.running = False
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")
    
    def setup_tracking_components(self, gaze_tracker, emotion_detector):
        """Set up the GazeTracker and EmotionDetector components."""
        self.gaze_tracker = gaze_tracker
        self.emotion_detector = emotion_detector
        
        # Register callbacks
        if self.gaze_tracker:
            self.gaze_tracker.register_callback(self.gaze_callback)
            
        if self.emotion_detector:
            self.emotion_detector.register_callback(self.emotion_callback)
        
        logger.info("Tracking components set up")

async def run_bridge(gaze_tracker, emotion_detector):
    """Run the WebSocket bridge server."""
    bridge = WebSocketBridge()
    bridge.setup_tracking_components(gaze_tracker, emotion_detector)
    
    await bridge.start_server()
    
    # Keep the server running
    try:
        await asyncio.Future()  # Run forever
    except asyncio.CancelledError:
        await bridge.stop_server()

def start_bridge_server(gaze_tracker, emotion_detector):
    """Start the bridge server in a separate thread."""
    async def _run():
        await run_bridge(gaze_tracker, emotion_detector)
    
    # Run the server in the event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(_run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        loop.close()