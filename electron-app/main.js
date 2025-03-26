// 2. main.js - Main Electron process
const { app, BrowserWindow, path, Menu, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

// Handle creating/removing shortcuts on Windows when installing/uninstalling
if (require('electron-squirrel-startup')) {
  app.quit();
}

let mainWindow;

function createWindow() {
  // Start the Python backend
  startPythonBackend();
 {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    icon: path.join(__dirname, 'renderer/icon.png')
  });

  // Load the index.html file
  mainWindow.loadFile(path.join(__dirname, 'renderer/index.html'));

  // Create application menu
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Export Data',
          click: () => {
            dialog.showSaveDialog({
              title: 'Export Emotion Data',
              defaultPath: path.join(app.getPath('documents'), 'emotion-data.json'),
              filters: [
                { name: 'JSON', extensions: ['json'] }
              ]
            }).then(result => {
              if (!result.canceled) {
                mainWindow.webContents.send('export-data', result.filePath);
              }
            }).catch(err => {
              console.error(err);
            });
          }
        },
        { type: 'separator' },
        { role: 'quit' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox({
              title: 'About Emotion Eye Tracker',
              message: 'Emotion Eye Tracker v1.0.0',
              detail: 'An AI-powered application for tracking eye movements and detecting emotions in real-time.',
              buttons: ['OK']
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// Quit when all windows are closed, except on macOS.
app.on('window-all-closed', function () {
  // Stop the Python backend
  stopPythonBackend();
 {
  if (process.platform !== 'darwin') app.quit();
});

// In this file you can include the rest of your app's specific main process code
// Python backend process launcher
const { spawn } = require('child_process');
let pythonProcess = null;

function startPythonBackend() {
  // Path to the Python executable - relative to the Electron app
  let pythonExecutablePath;
  
  if (process.platform === 'win32') {
    pythonExecutablePath = path.join(__dirname, 'python_dist', 'emotion_tracker_backend.exe');
  } else if (process.platform === 'darwin') {
    pythonExecutablePath = path.join(__dirname, 'python_dist', 'emotion_tracker_backend', 'emotion_tracker_backend');
  } else {
    pythonExecutablePath = path.join(__dirname, 'python_dist', 'emotion_tracker_backend');
  }
  
  console.log(`Starting Python backend from: ${pythonExecutablePath}`);
  
  try {
    // Start the Python process
    pythonProcess = spawn(pythonExecutablePath, [], {
      detached: false // Keep the Python process attached to the Electron process
    });
    
    // Log Python process output
    pythonProcess.stdout.on('data', (data) => {
      console.log(`Python Backend: ${data}`);
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error(`Python Backend Error: ${data}`);
    });
    
    pythonProcess.on('close', (code) => {
      console.log(`Python backend process exited with code ${code}`);
      pythonProcess = null;
    });
  } catch (error) {
    console.error('Failed to start Python backend:', error);
  }
}

// Ensure the Python process is terminated when Electron exits
function stopPythonBackend() {
  if (pythonProcess) {
    console.log('Stopping Python backend...');
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', pythonProcess.pid, '/f', '/t']);
    } else {
      pythonProcess.kill();
    }
  }
}


// Ensure the Python backend is stopped when the app is about to quit
app.on('will-quit', function () {
  stopPythonBackend();
});
