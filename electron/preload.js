'use strict';

const { contextBridge, ipcRenderer } = require('electron');

// Expose a deliberately tiny, read-only API to the Streamlit web page.
// Do not expose Node.js primitives, environment variables, tokens, or secrets.
contextBridge.exposeInMainWorld('desktopApp', {
  platform: process.platform,
  versions: Object.freeze({
    electron: process.versions.electron,
    chrome: process.versions.chrome,
  }),
  getStatus: () => ipcRenderer.invoke('app:get-status'),
  onServerStatus: (callback) => {
    if (typeof callback !== 'function') {
      return () => {};
    }

    const listener = (_event, status) => callback(status);
    ipcRenderer.on('server:status', listener);
    return () => ipcRenderer.removeListener('server:status', listener);
  },
});
