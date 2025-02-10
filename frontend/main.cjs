const { app, BrowserWindow, ipcMain, dialog } = require('electron');
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
      preload: path.join(__dirname, 'preload.js')  // Preload script path
    },
  });

  // Load the React build's index.html file.
  mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));

  // Open the DevTools if needed:
  // mainWindow.webContents.openDevTools();
}

app.whenReady().then(() => {
  createWindow();

  // Register the handler for the 'select-folder' channel
  ipcMain.handle('select-folder', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory']  // Allows selecting a folder
    });

    // If the user cancels the dialog, return null.
    if (result.canceled) {
      return null;
    }

    return result.filePaths[0]; // Return the selected folder path
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
