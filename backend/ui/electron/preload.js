const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  moveWindow: (delta) => ipcRenderer.send('move-window', delta)
});
