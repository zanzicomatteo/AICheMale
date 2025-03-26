// Put this file in renderer/js/app.js

// Configuration
const CONFIG = {
    wsServer: 'ws://127.0.0.1:8765',  // The WebSocket server address
    updateInterval: 100, // Update frequency in ms
    emotionColors: {
        'happy': 'var(--happy-color)',
        'sad': 'var(--sad-color)',
        'angry': 'var(--angry-color)',
        'surprise': 'var(--surprised-color)',
        'disgust': 'var(--disgusted-color)',
        'fear': 'var(--fearful-color)',
        'neutral': 'var(--neutral-color)',
        'contempt': 'var(--contempt-color)',
        'bored': 'var(--bored-color)',
        'confused': 'var(--confused-color)',
        'anxious': 'var(--anxious-color)',
        'excited': 'var(--excited-color)',
        'proud': 'var(--proud-color)',
        'shame': 'var(--shameful-color)',
        'guilt': 'var(--guilty-color)'
    }
};

// DOM elements
const elements = {
    video: document.getElementById('video'),
    canvas: document.getElementById('canvas'),
    gazeX: document.getElementById('gaze-x'),
    gazeY: document.getElementById('gaze-y'),
    primaryEmotion: document.getElementById('primary-emotion'),
    emotionConfidence: document.getElementById('emotion-confidence'),
    emotionBars: document.getElementById('emotion-bars'),
    logContainer: document.getElementById('log-container'),
    startBtn: document.getElementById('start-btn'),
    stopBtn: document.getElementById('stop-btn'),
    calibrateBtn: document.getElementById('calibrate-btn'),
    exportBtn: document.getElementById('export-btn')
};

// Application state
const state = {
    isTracking: false,
    wsConnection: null,
    currentEmotions: {},
    gazeData: { x: 0.5, y: 0.5 },
    sessionData: {
        startTime: null,
        emotions: [],
        gazePoints: []
    }
};

// Initialize emotion bars
function initEmotionBars() {
    // Clear existing bars
    elements.emotionBars.innerHTML = '';
    
    // Create a bar for each emotion
    for (const emotion in CONFIG.emotionColors) {
        const barContainer = document.createElement('div');
        barContainer.className = 'emotion-bar';
        barContainer.id = `emotion-bar-${emotion}`;
        
        const barFill = document.createElement('div');
        barFill.className = 'emotion-bar-fill';
        barFill.style.backgroundColor = CONFIG.emotionColors[emotion];
        barFill.style.width = '0%';
        
        const barLabel = document.createElement('div');
        barLabel.className = 'emotion-bar-label';
        barLabel.textContent = emotion.charAt(0).toUpperCase() + emotion.slice(1);
        
        const barValue = document.createElement('div');
        barValue.className = 'emotion-bar-value';
        barValue.textContent = '0%';
        
        barContainer.appendChild(barFill);
        barContainer.appendChild(barLabel);
        barContainer.appendChild(barValue);
        
        elements.emotionBars.appendChild(barContainer);
    }
}

// Update emotion bars with new data
function updateEmotionBars(emotionScores) {
    for (const emotion in emotionScores) {
        const barElement = document.getElementById(`emotion-bar-${emotion}`);
        if (barElement) {
            const value = emotionScores[emotion];
            const percentage = Math.round(value * 100);
            
            const barFill = barElement.querySelector('.emotion-bar-fill');
            const barValue = barElement.querySelector('.emotion-bar-value');
            
            barFill.style.width = `${percentage}%`;
            barValue.textContent = `${percentage}%`;
        }
    }
}

// Add a log entry
function addLogEntry(text) {
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.textContent = text;
    
    elements.logContainer.appendChild(entry);
    elements.logContainer.scrollTop = elements.logContainer.scrollHeight;
    
    // Limit log entries to keep performance good
    while (elements.logContainer.children.length > 100) {
        elements.logContainer.removeChild(elements.logContainer.firstChild);
    }
}

// Connect to WebSocket server
function connectWebSocket() {
    addLogEntry('Connecting to eye tracking and emotion detection server...');
    
    try {
        state.wsConnection = new WebSocket(CONFIG.wsServer);
        
        state.wsConnection.onopen = function() {
            addLogEntry('Connected to server successfully.');
            enableButton(elements.startBtn);
        };
        
        state.wsConnection.onmessage = function(event) {
            const message = JSON.parse(event.data);
            
            if (message.type === 'tracking_data') {
                handleTrackingData(message.data);
            } else if (message.type === 'command_response') {
                addLogEntry(`Server responded: ${message.command} - ${message.status}`);
            }
        };
        
        state.wsConnection.onclose = function() {
            addLogEntry('Connection to server closed.');
            disableButton(elements.startBtn);
            disableButton(elements.stopBtn);
            disableButton(elements.calibrateBtn);
            state.isTracking = false;
        };
        
        state.wsConnection.onerror = function(error) {
            addLogEntry('WebSocket error: Please make sure the Python server is running.');
            console.error('WebSocket error:', error);
        };
        
    } catch (error) {
        addLogEntry('Failed to connect: ' + error.message);
        console.error('WebSocket connection error:', error);
    }
}

// Handle incoming tracking data
function handleTrackingData(data) {
    if (!state.isTracking) return;
    
    // Update gaze data
    if (data.gaze) {
        const gazeX = data.gaze.GazeX;
        const gazeY = data.gaze.GazeY;
        
        state.gazeData = { x: gazeX, y: gazeY };
        
        // Update UI
        elements.gazeX.textContent = gazeX.toFixed(2);
        elements.gazeY.textContent = gazeY.toFixed(2);
        
        // Store data point
        state.sessionData.gazePoints.push({
            x: gazeX,
            y: gazeY,
            timestamp: Date.now()
        });
        
        // Draw gaze point on canvas
        drawGazePoint(gazeX, gazeY);
    }
    
    // Update emotion data
    if (data.emotion) {
        const emotion = data.emotion.emotion;
        const emotionScores = data.emotion.emotion_scores;
        const confidence = data.emotion.confidence || 0;
        
        state.currentEmotions = emotionScores;
        
        // Update UI
        elements.primaryEmotion.textContent = emotion.charAt(0).toUpperCase() + emotion.slice(1);
        elements.emotionConfidence.textContent = confidence;
        
        // Update emotion bars
        updateEmotionBars(emotionScores);
        
        // Store emotion data
        state.sessionData.emotions.push({
            emotion: emotion,
            scores: { ...emotionScores },
            timestamp: Date.now()
        });
        
        // Occasionally log the primary emotion
        if (Math.random() < 0.05) {  // Log roughly 5% of the time
            addLogEntry(`Detected: ${emotion} (${confidence}% confidence)`);
        }
    }
}

// Draw gaze point on canvas
function drawGazePoint(x, y) {
    const ctx = elements.canvas.getContext('2d');
    const width = elements.canvas.width;
    const height = elements.canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Calculate pixel coordinates from normalized coordinates
    const pixelX = x * width;
    const pixelY = y * height;
    
    // Draw gaze point
    ctx.beginPath();
    ctx.arc(pixelX, pixelY, 10, 0, 2 * Math.PI);
    ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
    ctx.fill();
    
    // Draw crosshair
    ctx.beginPath();
    ctx.moveTo(pixelX - 15, pixelY);
    ctx.lineTo(pixelX + 15, pixelY);
    ctx.moveTo(pixelX, pixelY - 15);
    ctx.lineTo(pixelX, pixelY + 15);
    ctx.strokeStyle = 'rgba(255, 0, 0, 0.8)';
    ctx.lineWidth = 2;
    ctx.stroke();
}

// Start tracking
function startTracking() {
    if (!state.wsConnection || state.wsConnection.readyState !== WebSocket.OPEN) {
        addLogEntry('Cannot start: No connection to server.');
        return;
    }
    
    addLogEntry('Starting tracking session...');
    
    // Reset session data
    state.sessionData = {
        startTime: Date.now(),
        emotions: [],
        gazePoints: []
    };
    
    // Send start command to server
    state.wsConnection.send(JSON.stringify({ command: 'start_tracking' }));
    
    // Update UI state
    state.isTracking = true;
    disableButton(elements.startBtn);
    enableButton(elements.stopBtn);
    enableButton(elements.calibrateBtn);
    
    // Start video if needed
    startVideo();
}

// Stop tracking
function stopTracking() {
    if (!state.isTracking) return;
    
    addLogEntry('Stopping tracking session...');
    
    // Send stop command to server
    if (state.wsConnection && state.wsConnection.readyState === WebSocket.OPEN) {
        state.wsConnection.send(JSON.stringify({ command: 'stop_tracking' }));
    }
    
    // Update UI state
    state.isTracking = false;
    enableButton(elements.startBtn);
    disableButton(elements.stopBtn);
    disableButton(elements.calibrateBtn);
    enableButton(elements.exportBtn);
    
    // Clear canvas
    const ctx = elements.canvas.getContext('2d');
    ctx.clearRect(0, 0, elements.canvas.width, elements.canvas.height);
    
    addLogEntry('Session stopped. Data can now be exported.');
}

// Calibrate gaze tracking
function calibrateGaze() {
    if (!state.isTracking) return;
    
    addLogEntry('Starting calibration process...');
    
    if (state.wsConnection && state.wsConnection.readyState === WebSocket.OPEN) {
        state.wsConnection.send(JSON.stringify({ command: 'calibrate' }));
    }
}

// Export session data
function exportData() {
    if (state.sessionData.emotions.length === 0 && state.sessionData.gazePoints.length === 0) {
        addLogEntry('No data to export.');
        return;
    }
    
    addLogEntry('Preparing data for export...');
    
    // Prepare data for export
    const exportData = {
        sessionId: state.sessionData.startTime,
        startTime: new Date(state.sessionData.startTime).toISOString(),
        endTime: new Date().toISOString(),
        emotions: state.sessionData.emotions,
        gazePoints: state.sessionData.gazePoints,
        summary: generateSummary()
    };
    
    // Use Electron's API bridge to request file save
    if (window.api) {
        window.api.exportData(exportData);
        addLogEntry('Data sent to be saved...');
    } else {
        // Fallback for browser testing
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportLink = document.createElement('a');
        exportLink.setAttribute('href', dataUri);
        exportLink.setAttribute('download', `eye-tracking-session-${Date.now()}.json`);
        document.body.appendChild(exportLink);
        exportLink.click();
        document.body.removeChild(exportLink);
        
        addLogEntry('Data exported successfully.');
    }
}

// Generate summary of session data
function generateSummary() {
    const emotions = state.sessionData.emotions;
    const gazePoints = state.sessionData.gazePoints;
    
    if (emotions.length === 0) {
        return { primaryEmotion: 'none', emotionCounts: {} };
    }
    
    // Count occurrences of each emotion
    const emotionCounts = {};
    emotions.forEach(entry => {
        const emotion = entry.emotion;
        emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
    });
    
    // Find the most common emotion
    let primaryEmotion = 'neutral';
    let maxCount = 0;
    
    for (const emotion in emotionCounts) {
        if (emotionCounts[emotion] > maxCount) {
            maxCount = emotionCounts[emotion];
            primaryEmotion = emotion;
        }
    }
    
    return {
        primaryEmotion,
        emotionCounts,
        totalEmotionSamples: emotions.length,
        totalGazeSamples: gazePoints.length,
        sessionDurationMs: Date.now() - state.sessionData.startTime
    };
}

// Start video feed
function startVideo() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                elements.video.srcObject = stream;
                
                // Set canvas size to match video
                elements.canvas.width = elements.video.clientWidth;
                elements.canvas.height = elements.video.clientHeight;
            })
            .catch(function(error) {
                addLogEntry('Camera access error: ' + error.message);
                console.error('getUserMedia error:', error);
            });
    } else {
        addLogEntry('getUserMedia is not supported by this browser');
    }
}

// Button utility functions
function enableButton(button) {
    button.disabled = false;
}

function disableButton(button) {
    button.disabled = true;
}

// Initialize the application
function initApp() {
    // Setup event listeners
    elements.startBtn.addEventListener('click', startTracking);
    elements.stopBtn.addEventListener('click', stopTracking);
    elements.calibrateBtn.addEventListener('click', calibrateGaze);
    elements.exportBtn.addEventListener('click', exportData);
    
    // Initialize emotion bars
    initEmotionBars();
    
    // Set up canvas
    elements.canvas.width = elements.video.clientWidth;
    elements.canvas.height = elements.video.clientHeight;
    
    // Connect to WebSocket server
    connectWebSocket();
    
    // Log initialization
    addLogEntry('Emotion Eye Tracker initialized');
    addLogEntry('Connecting to Python backend...');
    
    // Listen for export path from main process
    if (window.api) {
        window.api.onExportRequest((path) => {
            addLogEntry(`Data will be saved to: ${path}`);
        });
    }
}

// Start when the DOM is loaded
document.addEventListener('DOMContentLoaded', initApp);

// Handle window resize
window.addEventListener('resize', function() {
    if (elements.video.clientWidth > 0) {
        elements.canvas.width = elements.video.clientWidth;
        elements.canvas.height = elements.video.clientHeight;
    }
});