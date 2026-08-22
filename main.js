const {
    app,
    BrowserWindow,
    ipcMain,
    dialog
} = require('electron');

const { autoUpdater } = require('electron-updater');

const path = require('path');
const fs = require('fs');
const https = require('https');

let mainWindow = null;

// ============================================================
// BeeForce API configuration
// ============================================================

const API_TARGETS = {
    production: {
        host: 'esampark.beeforce.in'
    },

    uat: {
        host: 'esampark-uat.beeforce.in'
    }
};

// ============================================================
// Create Electron window
// ============================================================

function createWindow() {

    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,

        minWidth: 1100,
        minHeight: 700,

        title: 'BeeForce Configuration Portal',

        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),

            nodeIntegration: false,

            contextIsolation: true,

            sandbox: false,

            webviewTag: false
        }
    });

    mainWindow.loadFile(
        path.join(
            __dirname,
            'renderer',
            'index.html'
        )
    );

    mainWindow.webContents.on(
        'did-fail-load',
        function (event, errorCode, errorDescription) {

            console.error(
                '[BeeForce] Failed to load application:',
                errorCode,
                errorDescription
            );
        }
    );

    mainWindow.webContents.on(
        'did-finish-load',
        function () {

            console.log(
                '[BeeForce] Renderer loaded successfully.'
            );
        }
    );

    mainWindow.on(
        'closed',
        function () {

            mainWindow = null;
        }
    );
}

// ============================================================
// Validate API request
// ============================================================

function validateApiRequest(request) {

    if (!request || typeof request !== 'object') {

        return {
            valid: false,
            message: 'Invalid API request.'
        };
    }

    const env = request.env;

    if (
        typeof env !== 'string' ||
        !Object.prototype.hasOwnProperty.call(
            API_TARGETS,
            env
        )
    ) {

        return {
            valid: false,
            message: 'Invalid API environment.'
        };
    }

    const method = String(
        request.method || 'GET'
    ).toUpperCase();

    const allowedMethods = [
        'GET',
        'POST',
        'PUT',
        'PATCH',
        'DELETE',
        'HEAD',
        'OPTIONS'
    ];

    if (!allowedMethods.includes(method)) {

        return {
            valid: false,
            message: 'HTTP method is not allowed.'
        };
    }

    if (
        request.path !== undefined &&
        typeof request.path !== 'string'
    ) {

        return {
            valid: false,
            message: 'Invalid API path.'
        };
    }

    return {
        valid: true
    };
}

// ============================================================
// Convert query object to query string
// ============================================================

function buildQueryString(query) {

    if (
        !query ||
        typeof query !== 'object'
    ) {

        return '';
    }

    const params = new URLSearchParams();

    Object.keys(query).forEach(
        function (key) {

            const value = query[key];

            if (
                value === undefined ||
                value === null
            ) {

                return;
            }

            if (Array.isArray(value)) {

                value.forEach(
                    function (item) {

                        params.append(
                            key,
                            String(item)
                        );
                    }
                );

            } else {

                params.append(
                    key,
                    String(value)
                );
            }
        }
    );

    const encoded = params.toString();

    return encoded
        ? '?' + encoded
        : '';
}

// ============================================================
// Normalize response headers
// ============================================================

function normalizeResponseHeaders(headers) {

    const result = {};

    Object.keys(headers || {}).forEach(
        function (key) {

            const value = headers[key];

            if (Array.isArray(value)) {

                result[key] =
                    value.join(', ');

            } else if (
                value !== undefined
            ) {

                result[key] =
                    String(value);
            }
        }
    );

    return result;
}

// ============================================================
// Native BeeForce API request
// ============================================================

function makeApiRequest(request) {

    return new Promise(
        function (resolve) {

            const validation =
                validateApiRequest(request);

            if (!validation.valid) {

                resolve({
                    error: true,
                    message: validation.message
                });

                return;
            }

            try {

                const env = request.env;

                const target =
                    API_TARGETS[env];

                const method = String(
                    request.method || 'GET'
                ).toUpperCase();

                let requestPath =
                    request.path || '/';

                if (
                    !requestPath.startsWith('/')
                ) {

                    requestPath =
                        '/' + requestPath;
                }

                const queryString =
                    buildQueryString(
                        request.query
                    );

                const headers =
                    Object.assign(
                        {},
                        request.headers || {}
                    );

                delete headers.host;
                delete headers.connection;
                delete headers['content-length'];

                const body =
                    request.body !== undefined &&
                    request.body !== null
                        ? String(request.body)
                        : null;

                if (
                    body !== null &&
                    body.length > 0
                ) {

                    const hasContentType =
                        Object.keys(headers).some(
                            function (key) {

                                return (
                                    key.toLowerCase() ===
                                    'content-type'
                                );
                            }
                        );

                    if (!hasContentType) {

                        headers['Content-Type'] =
                            'application/json';
                    }
                }

                const options = {

                    hostname:
                        target.host,

                    port: 443,

                    path:
                        requestPath +
                        queryString,

                    method: method,

                    headers: headers,

                    timeout: 60000
                };

                console.log(
                    '[BeeForce API]',
                    method,
                    env,
                    requestPath
                );

                const req =
                    https.request(
                        options,
                        function (res) {

                            let responseBody = '';

                            res.setEncoding(
                                'utf8'
                            );

                            res.on(
                                'data',
                                function (chunk) {

                                    responseBody +=
                                        chunk;
                                }
                            );

                            res.on(
                                'end',
                                function () {

                                    const responseHeaders =
                                        normalizeResponseHeaders(
                                            res.headers
                                        );

                                    console.log(
                                        '[BeeForce API]',
                                        method,
                                        requestPath,
                                        'Status:',
                                        res.statusCode
                                    );

                                    resolve({

                                        error: false,

                                        status:
                                            res.statusCode ||
                                            0,

                                        headers:
                                            responseHeaders,

                                        body:
                                            responseBody
                                    });
                                }
                            );
                        }
                    );

                req.on(
                    'error',
                    function (error) {

                        console.error(
                            '[BeeForce API] Request failed:',
                            error.message
                        );

                        resolve({

                            error: true,

                            message:
                                error.message
                        });
                    }
                );

                req.on(
                    'timeout',
                    function () {

                        console.error(
                            '[BeeForce API] Request timeout.'
                        );

                        req.destroy(
                            new Error(
                                'BeeForce API request timed out.'
                            )
                        );
                    }
                );

                if (
                    body !== null &&
                    method !== 'GET' &&
                    method !== 'HEAD'
                ) {

                    req.write(body);
                }

                req.end();

            } catch (error) {

                console.error(
                    '[BeeForce API] Unexpected error:',
                    error
                );

                resolve({

                    error: true,

                    message:
                        error.message ||
                        String(error)
                });
            }
        }
    );
}

// ============================================================
// API IPC handler
// ============================================================

ipcMain.handle(
    'beeforce-api-request',
    async function (event, request) {

        return makeApiRequest(request);
    }
);

// ============================================================
// Local renderer file access
// ============================================================

ipcMain.handle(
    'beeforce-get-app-file',
    async function (event, filename) {

        try {

            if (
                typeof filename !== 'string' ||
                filename.length === 0
            ) {

                return {
                    ok: false,
                    error: 'Invalid filename.'
                };
            }

            if (
                filename.includes('/') ||
                filename.includes('\\') ||
                filename.includes('..') ||
                path.isAbsolute(filename)
            ) {

                return {
                    ok: false,
                    error: 'Invalid filename.'
                };
            }

            if (
                !filename
                    .toLowerCase()
                    .endsWith('.js')
            ) {

                return {
                    ok: false,
                    error:
                        'Only JavaScript files are allowed.'
                };
            }

            const rendererDirectory =
                path.resolve(
                    __dirname,
                    'renderer'
                );

            const filePath =
                path.resolve(
                    rendererDirectory,
                    filename
                );

            const rendererPrefix =
                rendererDirectory.endsWith(
                    path.sep
                )
                    ? rendererDirectory
                    : rendererDirectory +
                      path.sep;

            if (
                filePath !== rendererDirectory &&
                !filePath.startsWith(
                    rendererPrefix
                )
            ) {

                return {
                    ok: false,
                    error: 'Invalid file path.'
                };
            }

            if (!fs.existsSync(filePath)) {

                return {
                    ok: false,
                    error:
                        'File not found: ' +
                        filename
                };
            }

            const stat =
                fs.statSync(filePath);

            if (!stat.isFile()) {

                return {
                    ok: false,
                    error:
                        'Requested path is not a file.'
                };
            }

            const content =
                fs.readFileSync(
                    filePath,
                    'utf8'
                );

            console.log(
                '[BeeForce] Loaded local file:',
                filename
            );

            return {

                ok: true,

                content: content
            };

        } catch (error) {

            console.error(
                '[BeeForce] Failed to read local file:',
                error
            );

            return {

                ok: false,

                error:
                    error.message ||
                    String(error)
            };
        }
    }
);

// ============================================================
// BeeForce Auto Update
// ============================================================

function setupAutoUpdater() {

    // --------------------------------------------------------
    // Development mode
    // --------------------------------------------------------

    if (!app.isPackaged) {

        console.log(
            '[BeeForce Updater] Development mode - updater disabled.'
        );

        return;
    }

    console.log(
        '[BeeForce Updater] Production mode.'
    );

    console.log(
        '[BeeForce Updater] Current version:',
        app.getVersion()
    );

    // Do not download automatically.
    // Ask the user first.
    autoUpdater.autoDownload = false;

    // Install downloaded update when application quits.
    autoUpdater.autoInstallOnAppQuit = true;

    // --------------------------------------------------------
    // Checking
    // --------------------------------------------------------

    autoUpdater.on(
        'checking-for-update',
        function () {

            console.log(
                '[BeeForce Updater] Checking for updates...'
            );
        }
    );

    // --------------------------------------------------------
    // Update available
    // --------------------------------------------------------

    autoUpdater.on(
        'update-available',
        async function (info) {

            console.log(
                '[BeeForce Updater] Update available:',
                info.version
            );

            if (!mainWindow) {

                return;
            }

            const result =
                await dialog.showMessageBox(
                    mainWindow,
                    {

                        type: 'info',

                        title:
                            'BeeForce Update Available',

                        message:
                            'A new version of BeeForce is available.',

                        detail:
                            'Current version: ' +
                            app.getVersion() +
                            '\nNew version: ' +
                            info.version +
                            '\n\nWould you like to download the update now?',

                        buttons: [
                            'Update Now',
                            'Later'
                        ],

                        defaultId: 0,

                        cancelId: 1
                    }
                );

            if (result.response === 0) {

                console.log(
                    '[BeeForce Updater] Downloading update...'
                );

                try {

                    await autoUpdater.downloadUpdate();

                } catch (error) {

                    console.error(
                        '[BeeForce Updater] Download failed:',
                        error
                    );

                    dialog.showErrorBox(
                        'BeeForce Update Failed',
                        'Unable to download the update.\n\n' +
                        (
                            error.message ||
                            String(error)
                        )
                    );
                }
            }
        }
    );

    // --------------------------------------------------------
    // No update
    // --------------------------------------------------------

    autoUpdater.on(
        'update-not-available',
        function () {

            console.log(
                '[BeeForce Updater] BeeForce is up to date.'
            );
        }
    );

    // --------------------------------------------------------
    // Download progress
    // --------------------------------------------------------

    autoUpdater.on(
        'download-progress',
        function (progress) {

            console.log(
                '[BeeForce Updater] Download:',
                Math.round(
                    progress.percent
                ) + '%'
            );
        }
    );

    // --------------------------------------------------------
    // Update downloaded
    // --------------------------------------------------------

    autoUpdater.on(
        'update-downloaded',
        async function (info) {

            console.log(
                '[BeeForce Updater] Update downloaded:',
                info.version
            );

            if (!mainWindow) {

                autoUpdater.quitAndInstall();

                return;
            }

            const result =
                await dialog.showMessageBox(
                    mainWindow,
                    {

                        type: 'info',

                        title:
                            'BeeForce Update Ready',

                        message:
                            'BeeForce ' +
                            info.version +
                            ' has been downloaded.',

                        detail:
                            'Restart BeeForce now to install the update.',

                        buttons: [
                            'Restart Now',
                            'Later'
                        ],

                        defaultId: 0,

                        cancelId: 1
                    }
                );

            if (result.response === 0) {

                console.log(
                    '[BeeForce Updater] Restarting for update...'
                );

                autoUpdater.quitAndInstall();
            }
        }
    );

    // --------------------------------------------------------
    // Update error
    // --------------------------------------------------------

    autoUpdater.on(
        'error',
        function (error) {

            console.error(
                '[BeeForce Updater] Error:',
                error
            );
        }
    );

    // --------------------------------------------------------
    // Check GitHub after application starts
    // --------------------------------------------------------

    setTimeout(
        function () {

            console.log(
                '[BeeForce Updater] Starting update check...'
            );

            autoUpdater
                .checkForUpdates()
                .then(
                    function (result) {

                        if (!result) {

                            console.log(
                                '[BeeForce Updater] No update result.'
                            );
                        }

                    }
                )
                .catch(
                    function (error) {

                        console.error(
                            '[BeeForce Updater] Update check failed:',
                            error.message
                        );
                    }
                );

        },
        5000
    );
}

// ============================================================
// Electron startup
// ============================================================

app.whenReady().then(
    function () {

        console.log(
            '============================================================'
        );

        console.log(
            '[BeeForce] Electron application starting...'
        );

        console.log(
            '[BeeForce] Application directory:',
            __dirname
        );

        console.log(
            '[BeeForce] Application version:',
            app.getVersion()
        );

        createWindow();

        // Start updater during normal application startup.
        setupAutoUpdater();

        app.on(
            'activate',
            function () {

                if (
                    BrowserWindow.getAllWindows()
                        .length === 0
                ) {

                    createWindow();
                }
            }
        );
    }
);

// ============================================================
// Application shutdown
// ============================================================

app.on(
    'window-all-closed',
    function () {

        if (
            process.platform !== 'darwin'
        ) {

            app.quit();
        }
    }
);