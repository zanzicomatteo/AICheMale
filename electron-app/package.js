// Add this to your Electron project as package.js
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const builder = require('electron-builder');
const { Platform } = require('electron-builder');

// Configuration
const PYTHON_PROJECT_PATH = path.resolve(__dirname, '../emotion_tracking_system');
const PYTHON_DIST_PATH = path.resolve(__dirname, 'python_dist');
const PYTHON_EXECUTABLE_NAME = 'emotion_tracker_backend';

console.log('Starting the packaging process...');

// Step 1: Create PyInstaller spec file
const createSpecFile = () => {
  const specContent = `
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['${PYTHON_PROJECT_PATH.replace(/\\/g, '\\\\')}'],
    binaries=[],
    datas=[
        ('images', 'images'),
        ('*.py', '.'),
    ],
    hiddenimports=['websockets', 'asyncio', 'cv2', 'numpy', 'pandas', 'PIL'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='${PYTHON_EXECUTABLE_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
`;

  fs.writeFileSync(path.join(PYTHON_PROJECT_PATH, 'emotion_tracker.spec'), specContent);
  console.log('Created PyInstaller spec file');
};

// Step 2: Run PyInstaller to create a standalone executable
const buildPythonExecutable = () => {
  return new Promise((resolve, reject) => {
    console.log('Building Python executable with PyInstaller...');
    
    const pyInstallerCommand = `cd "${PYTHON_PROJECT_PATH}" && pyinstaller --clean emotion_tracker.spec`;
    
    exec(pyInstallerCommand, (error, stdout, stderr) => {
      if (error) {
        console.error(`PyInstaller error: ${error.message}`);
        return reject(error);
      }
      if (stderr) {
        console.error(`PyInstaller stderr: ${stderr}`);
      }
      console.log(`PyInstaller stdout: ${stdout}`);
      console.log('Python executable built successfully');
      resolve();
    });
  });
};

// Step 3: Copy the Python executable to the Electron project
const copyPythonExecutable = () => {
  return new Promise((resolve, reject) => {
    console.log('Copying Python executable to Electron project...');
    
    // Create destination directory if it doesn't exist
    if (!fs.existsSync(PYTHON_DIST_PATH)) {
      fs.mkdirSync(PYTHON_DIST_PATH, { recursive: true });
    }
    
    // Source path of the PyInstaller output
    const sourcePath = path.join(PYTHON_PROJECT_PATH, 'dist', PYTHON_EXECUTABLE_NAME);
    
    // Determine if it's a directory (MacOS/Linux) or file (Windows)
    const isDirectory = fs.existsSync(sourcePath) && fs.lstatSync(sourcePath).isDirectory();
    
    if (isDirectory) {
      // MacOS/Linux - copy directory
      const copyCommand = `cp -R "${sourcePath}" "${PYTHON_DIST_PATH}"`;
      exec(copyCommand, (error) => {
        if (error) {
          console.error(`Copy error: ${error.message}`);
          return reject(error);
        }
        console.log('Python executable copied successfully');
        resolve();
      });
    } else {
      // Windows - copy file
      const copyCommand = `copy "${sourcePath}.exe" "${PYTHON_DIST_PATH}"`;
      exec(copyCommand, (error) => {
        if (error) {
          console.error(`Copy error: ${error.message}`);
          return reject(error);
        }
        console.log('Python executable copied successfully');
        resolve();
      });
    }
  });
};

// Step 4: Update main.js to launch the Python backend
const updateMainJs = () => {
  console.log('Updating main.js to launch Python backend...');
  
  const mainJsPath = path.join(__dirname, 'main.js');
  let mainJsContent = fs.readFileSync(mainJsPath, 'utf8');
  
  // Check if we've already updated the file
  if (mainJsContent.includes('startPythonBackend')) {
    console.log('main.js already updated');
    return;
  }
  
  // Add the Python backend launcher code
  const pythonLauncherCode = `
// Python backend process launcher
const { spawn } = require('child_process');
let pythonProcess = null;

function startPythonBackend() {
  // Path to the Python executable - relative to the Electron app
  let pythonExecutablePath;
  
  if (process.platform === 'win32') {
    pythonExecutablePath = path.join(__dirname, 'python_dist', '${PYTHON_EXECUTABLE_NAME}.exe');
  } else if (process.platform === 'darwin') {
    pythonExecutablePath = path.join(__dirname, 'python_dist', '${PYTHON_EXECUTABLE_NAME}', '${PYTHON_EXECUTABLE_NAME}');
  } else {
    pythonExecutablePath = path.join(__dirname, 'python_dist', '${PYTHON_EXECUTABLE_NAME}');
  }
  
  console.log(\`Starting Python backend from: \${pythonExecutablePath}\`);
  
  try {
    // Start the Python process
    pythonProcess = spawn(pythonExecutablePath, [], {
      detached: false // Keep the Python process attached to the Electron process
    });
    
    // Log Python process output
    pythonProcess.stdout.on('data', (data) => {
      console.log(\`Python Backend: \${data}\`);
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error(\`Python Backend Error: \${data}\`);
    });
    
    pythonProcess.on('close', (code) => {
      console.log(\`Python backend process exited with code \${code}\`);
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
`;
  
  // Insert the code right after the required modules
  const insertPosition = mainJsContent.indexOf('const { app, BrowserWindow') + 'const { app, BrowserWindow'.length;
  mainJsContent = mainJsContent.slice(0, insertPosition) + 
                 ', path' + 
                 mainJsContent.slice(insertPosition) +
                 pythonLauncherCode;
  
  // Add calls to start and stop the Python backend
  mainJsContent = mainJsContent.replace(
    'function createWindow()',
    'function createWindow() {\n  // Start the Python backend\n  startPythonBackend();\n'
  ).replace(
    'app.on(\'window-all-closed\', function ()',
    'app.on(\'window-all-closed\', function () {\n  // Stop the Python backend\n  stopPythonBackend();\n'
  ).replace(
    'app.on(\'will-quit\', function ()',
    'app.on(\'will-quit\', function () {\n  // Ensure the Python backend is stopped\n  stopPythonBackend();\n'
  );
  
  // If will-quit event isn't defined, add it
  if (!mainJsContent.includes('app.on(\'will-quit\'')) {
    mainJsContent += `\n\n// Ensure the Python backend is stopped when the app is about to quit
app.on('will-quit', function () {
  stopPythonBackend();
});\n`;
  }
  
  fs.writeFileSync(mainJsPath, mainJsContent);
  console.log('main.js updated successfully');
};

// Step 5: Update electron-builder configuration
const updateBuilderConfig = () => {
  console.log('Updating electron-builder configuration...');
  
  const packageJsonPath = path.join(__dirname, 'package.json');
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  
  // Update the build configuration
  packageJson.build = packageJson.build || {};
  packageJson.build.extraResources = packageJson.build.extraResources || [];
  
  // Add the Python executable to extraResources if not already there
  const pythonResource = {
    from: 'python_dist/',
    to: 'python_dist'
  };
  
  // Check if the resource is already in the configuration
  const resourceExists = packageJson.build.extraResources.some(
    resource => typeof resource === 'object' && resource.from === pythonResource.from
  );
  
  if (!resourceExists) {
    packageJson.build.extraResources.push(pythonResource);
  }
  
  // Add a new script for the combined build
  packageJson.scripts = packageJson.scripts || {};
  packageJson.scripts['build-full'] = 'node package.js';
  
  fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
  console.log('package.json updated successfully');
};

// Step 6: Build the Electron app
const buildElectronApp = () => {
  console.log('Building Electron application...');
  
  return builder.build({
    targets: Platform.current().createTarget(),
    config: {
      appId: 'com.emotion.eyetracker',
      productName: 'Emotion Eye Tracker',
      directories: {
        output: 'dist'
      }
    }
  }).then(() => {
    console.log('Electron application built successfully');
  }).catch(err => {
    console.error('Error building Electron application:', err);
    throw err;
  });
};

// Main execution
async function main() {
  try {
    // Create PyInstaller spec file
    createSpecFile();
    
    // Build Python executable
    await buildPythonExecutable();
    
    // Copy Python executable to Electron project
    await copyPythonExecutable();
    
    // Update main.js
    updateMainJs();
    
    // Update electron-builder configuration
    updateBuilderConfig();
    
    // Build Electron app
    await buildElectronApp();
    
    console.log('All done! The packaged application is in the dist folder.');
  } catch (error) {
    console.error('Packaging failed:', error);
    process.exit(1);
  }
}

main();