'use strict';

const { app, BrowserWindow, Menu, Tray, dialog, ipcMain, nativeImage } = require('electron');
const { autoUpdater } = require('electron-updater');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const http = require('node:http');
const net = require('node:net');
const path = require('node:path');

const PRODUCT_NAME = 'Configuration Portal';
const STREAMLIT_HOST = '127.0.0.1';
const STREAMLIT_PORT = 8501;
const STREAMLIT_URL = `http://localhost:${STREAMLIT_PORT}`;
const SERVER_READY_TIMEOUT_MS = 90_000;
const SERVER_POLL_INTERVAL_MS = 500;
const MAX_RESTARTS = 3;

let mainWindow;
let splashWindow;
let tray;
let backendProcess;
let isQuitting = false;
let serverStatus = 'starting';
let restartAttempts = 0;
let startupFailed = false;
let appLogStream;

const gotSingleInstanceLock = app.requestSingleInstanceLock();
if (!gotSingleInstanceLock) {
  app.quit();
}

function getIconPath() {
  const iconPath = path.join(__dirname, 'assets', 'icon.ico');
  return fs.existsSync(iconPath) ? iconPath : undefined;
}

function getUserLogDir() {
  return path.join(app.getPath('userData'), 'logs');
}

function writeLog(message) {
  const line = `[${new Date().toISOString()}] ${message}\n`;
  process.stdout.write(line);
  if (appLogStream) {
    appLogStream.write(line);
  }
}

function initialiseLogging() {
  fs.mkdirSync(getUserLogDir(), { recursive: true });
  appLogStream = fs.createWriteStream(path.join(getUserLogDir(), 'electron.log'), { flags: 'a' });
  writeLog(`${PRODUCT_NAME} starting. Electron ${process.versions.electron}. Packaged=${app.isPackaged}`);
}

function sendServerStatus(status) {
  serverStatus = status;
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('server:status', status);
  }
}

function getBackendCommand() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend', 'app.exe');
  }

  return process.platform === 'win32' ? 'python.exe' : 'python3';
}

function getBackendArgs() {
  if (app.isPackaged) {
    return [];
  }

  return [path.join(__dirname, 'desktop_backend.py')];
}

function getBackendWorkingDirectory() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend');
  }

  return path.join(__dirname, '..');
}

function isPortFree(host, port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', () => resolve(false));
    server.once('listening', () => {
      server.close(() => resolve(true));
    });
    server.listen(port, host);
  });
}

function waitForBackend(url, timeoutMs = SERVER_READY_TIMEOUT_MS) {
  const startedAt = Date.now();

  return new Promise((resolve, reject) => {
    const poll = () => {
      const request = http.get(url, (response) => {
        response.resume();
        if (response.statusCode && response.statusCode >= 200 && response.statusCode < 500) {
          resolve();
          return;
        }
        scheduleNextPoll();
      });

      request.on('error', scheduleNextPoll);
      request.setTimeout(2_000, () => {
        request.destroy();
        scheduleNextPoll();
      });
    };

    const scheduleNextPoll = () => {
      if (startupFailed || isQuitting) {
        reject(new Error('Backend startup stopped before the server became ready.'));
        return;
      }

      if (Date.now() - startedAt > timeoutMs) {
        reject(new Error(`Timed out waiting for ${url}. See logs in ${getUserLogDir()}.`));
        return;
      }

      setTimeout(poll, SERVER_POLL_INTERVAL_MS);
    };

    poll();
  });
}

async function startBackend() {
  sendServerStatus('starting');
  startupFailed = false;

  const portFree = await isPortFree(STREAMLIT_HOST, STREAMLIT_PORT);
  if (!portFree) {
    throw new Error(`Port ${STREAMLIT_PORT} is already in use. Close the other application using this port and start ${PRODUCT_NAME} again.`);
  }

  const command = getBackendCommand();
  const args = getBackendArgs();
  const cwd = getBackendWorkingDirectory();

  if (app.isPackaged && !fs.existsSync(command)) {
    throw new Error(`Packaged backend executable was not found: ${command}`);
  }

  const logPath = path.join(getUserLogDir(), 'backend.log');
  const childLogStream = fs.createWriteStream(logPath, { flags: 'a' });

  writeLog(`Starting packaged backend: ${command} ${args.join(' ')} (cwd=${cwd})`);

  backendProcess = spawn(command, args, {
    cwd,
    windowsHide: true,
    shell: false,
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1',
      STREAMLIT_BROWSER_GATHER_USAGE_STATS: 'false',
      STREAMLIT_SERVER_HEADLESS: 'true',
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  backendProcess.stdout.on('data', (data) => childLogStream.write(data));
  backendProcess.stderr.on('data', (data) => childLogStream.write(data));

  backendProcess.once('error', (error) => {
    startupFailed = true;
    writeLog(`Failed to spawn packaged backend: ${error.message}`);
  });

  backendProcess.once('close', (code, signal) => {
    childLogStream.end();
    writeLog(`Packaged backend exited. code=${code} signal=${signal}`);
    backendProcess = undefined;

    if (!isQuitting && !startupFailed) {
      restartBackendAfterCrash();
    }
  });

  await waitForBackend(STREAMLIT_URL);
  restartAttempts = 0;
  sendServerStatus('running');
}

function restartBackendAfterCrash() {
  if (restartAttempts >= MAX_RESTARTS) {
    sendServerStatus('failed');
    showStartupError(new Error(`${PRODUCT_NAME} server stopped repeatedly. Please restart the application. Logs are available in ${getUserLogDir()}.`));
    return;
  }

  restartAttempts += 1;
  sendServerStatus('restarting');
  writeLog(`Restarting packaged backend after crash (${restartAttempts}/${MAX_RESTARTS}).`);
  setTimeout(() => {
    startBackend().catch(showStartupError);
  }, 1_500);
}

function stopBackend() {
  if (!backendProcess) {
    return;
  }

  writeLog('Stopping packaged backend process.');
  const child = backendProcess;
  backendProcess = undefined;

  if (process.platform === 'win32' && child.pid) {
    spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'], { windowsHide: true });
  } else {
    child.kill('SIGTERM');
  }
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 620,
    height: 430,
    frame: false,
    resizable: false,
    show: false,
    icon: getIconPath(),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
    },
  });

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
  splashWindow.once('ready-to-show', () => splashWindow.show());
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    title: PRODUCT_NAME,
    show: false,
    icon: getIconPath(),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      devTools: !app.isPackaged,
    },
  });

  mainWindow.maximize();
  mainWindow.setMenuBarVisibility(false);

  mainWindow.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));

  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith(STREAMLIT_URL)) {
      event.preventDefault();
      writeLog(`Blocked external navigation: ${url}`);
    }
  });

  if (app.isPackaged) {
    mainWindow.webContents.on('devtools-opened', () => mainWindow.webContents.closeDevTools());
  }

  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
      if (tray) {
        tray.displayBalloon({
          title: PRODUCT_NAME,
          content: 'The app is still running in the system tray.',
        });
      }
    }
  });

  return mainWindow;
}

function createTray() {
  const iconPath = getIconPath();
  const image = iconPath ? nativeImage.createFromPath(iconPath) : nativeImage.createEmpty();
  tray = new Tray(image);
  tray.setToolTip(PRODUCT_NAME);
  tray.setContextMenu(Menu.buildFromTemplate([
    {
      label: 'Restore',
      click: () => showMainWindow(),
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        isQuitting = true;
        app.quit();
      },
    },
  ]));
  tray.on('double-click', () => showMainWindow());
}

function showMainWindow() {
  if (!mainWindow) {
    return;
  }
  mainWindow.show();
  if (mainWindow.isMinimized()) {
    mainWindow.restore();
  }
  mainWindow.focus();
}

async function showApplication() {
  createMainWindow();
  await mainWindow.loadURL(STREAMLIT_URL);

  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.close();
  }

  showMainWindow();
}

function showStartupError(error) {
  startupFailed = true;
  sendServerStatus('failed');
  writeLog(`Startup error: ${error.stack || error.message}`);

  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.close();
  }

  dialog.showErrorBox(
    `${PRODUCT_NAME} could not start`,
    `${error.message}\n\nPlease try restarting the application. If the problem continues, review the log files in:\n${getUserLogDir()}`,
  );
}

function configureAutoUpdater() {
  if (!app.isPackaged) {
    return;
  }

  autoUpdater.autoDownload = false;
  autoUpdater.on('error', (error) => writeLog(`Auto-update error: ${error.message}`));
  autoUpdater.on('update-available', () => writeLog('Auto-update available.'));
  autoUpdater.on('update-not-available', () => writeLog('Auto-update not available.'));
  autoUpdater.checkForUpdates().catch((error) => writeLog(`Auto-update check failed: ${error.message}`));
}

app.on('second-instance', () => showMainWindow());

app.on('web-contents-created', (_event, contents) => {
  contents.on('will-attach-webview', (event) => event.preventDefault());
});

ipcMain.handle('app:get-status', () => ({
  serverStatus,
  url: STREAMLIT_URL,
  packaged: app.isPackaged,
}));

app.whenReady().then(async () => {
  initialiseLogging();
  Menu.setApplicationMenu(null);
  createTray();
  createSplashWindow();

  try {
    await startBackend();
    await showApplication();
    configureAutoUpdater();
  } catch (error) {
    showStartupError(error);
  }
});

app.on('before-quit', () => {
  isQuitting = true;
  stopBackend();
});

app.on('window-all-closed', () => {
  if (isQuitting) {
    app.quit();
  }
});

app.on('quit', () => {
  stopBackend();
  if (appLogStream) {
    appLogStream.end();
  }
});
