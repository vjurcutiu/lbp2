const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    selectFolderOrFile: () => ipcRenderer.invoke('select-folder-or-file')
});