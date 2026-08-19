const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('beeForce', {
    apiRequest: (request) => {
        return ipcRenderer.invoke('beeforce-api-request', request);
    },

    getAppFile: (filename) => {
        return ipcRenderer.invoke('beeforce-get-app-file', filename);
    }
});