const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // We can expose IPC methods here if needed later
});
