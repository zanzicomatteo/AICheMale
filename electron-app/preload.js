// 3. preload.js - Secure bridge between renderer and main process
const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld(
  'api', {
    exportData: (data) => {
      ipcRenderer.send('export-data', data);
    },
    onExportRequest: (callback) => {
      ipcRenderer.on('export-data', (event, path) => callback(path));
    }
  }
);

// 4. renderer/index.html - Your existing HTML file with slight modifications
// See the next file section for the complete HTML content