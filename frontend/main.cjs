const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');

let mainWindow; // Declare a global variable for the window


function createWindow() {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      nodeIntegration: false,  // For security
      contextIsolation: true,  // Use a preload script for communication
      resizable: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  //Menu.setApplicationMenu(null);

  // Load the React build's index.html file.
  mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));

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

// Quit the app when all windows are closed (except on macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
