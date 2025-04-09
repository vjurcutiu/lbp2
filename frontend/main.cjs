const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');
if (process.env.NODE_ENV === 'development') {
  require('electron-reload')(path.join(__dirname), {
    electron: path.join(__dirname, 'node_modules', '.bin', 'electron')
  });
}

let mainWindow; // Declare a global variable for the window
let flaskProcess; // declare at a higher scope


const { spawn } = require('child_process');

const isDev = process.env.NODE_ENV === 'development';
const isProd = process.env.NODE_ENV === 'production';

global.flaskPort = null;

console.log("NODE_ENV:", process.env.NODE_ENV);

function createWindow() {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 1024,
    height: 768,
    frame: false,
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      nodeIntegration: false,  // For security
      contextIsolation: true,  // Use a preload script for communication
      resizable: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  if (isProd) {
    const exePath = path.join(process.resourcesPath, 'flask', 'server.exe');
  
    // Spawn the Flask process with stdout piped
    flaskProcess = spawn(exePath, [], {
      cwd: __dirname,
      stdio: ['inherit', 'pipe', 'inherit']  // Pipe stdout for listening
    });
  
    flaskProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log(output);
  
      const match = output.match(/Starting Flask app on port (\d+)/);
      if (match && match[1]) {
        global.flaskPort = match[1];
        console.log('Detected Flask server running on port:', global.flaskPort);
        mainWindow.webContents.send('flask-port', global.flaskPort);
      }
    });
  
    flaskProcess.on('error', (err) => {
      console.error('Failed to start server.exe:', err);
    });
  
    flaskProcess.on('close', (code) => {
      console.log(`server.exe exited with code ${code}`);
    });
  } else {
    console.log('Development mode - server.exe is not started.');
  }

  //Menu.setApplicationMenu(null);
  if (isDev) {
    console.log('running in dev')
    mainWindow.loadURL('http://localhost:5173/');
    mainWindow.webContents.openDevTools(); 

  } else {
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));
    mainWindow.webContents.openDevTools(); 

  }
  // Load the React build's index.html file.
  // Open the DevTools if needed:
  // mainWindow.webContents.openDevTools();
}

app.whenReady().then(() => {
  createWindow();

  // Register the handler for the 'select-folder' channel
  ipcMain.handle('select-files', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openFile', 'multiSelections']
    });
    if (result.canceled) {
      return null;
    }
    console.log('results in electron:' +result.filePaths)
    return result.filePaths;  // An array containing both file and folder paths
  });

  // On macOS, recreate a window if none exist
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});
  // IPC handler for minimizing the window
  ipcMain.handle('minimize-window', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) win.minimize();
  });

  // IPC handler for maximizing/restoring the window
  ipcMain.handle('maximize-window', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) {
      if (win.isMaximized()) {
        win.unmaximize();
      } else {
        win.maximize();
      }
    }
  });

  // IPC handler for closing the window
  ipcMain.handle('close-window', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) win.close();
  });

// Quit the app when all windows are closed (except on macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
