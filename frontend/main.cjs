const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');
require('electron-reload')(path.join(__dirname), {
  electron: path.join(__dirname, 'node_modules', '.bin', 'electron')
});
let mainWindow; // Declare a global variable for the window
const isDev = process.env.NODE_ENV === 'development';

function createWindow() {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 1024,
    height: 768,
    frame: false,
    webPreferences: {
      nodeIntegration: false,  // For security
      contextIsolation: true,  // Use a preload script for communication
      resizable: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  //Menu.setApplicationMenu(null);
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173/');
  } else {
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));
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
