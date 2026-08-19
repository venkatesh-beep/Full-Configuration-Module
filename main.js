const { app, BrowserWindow, ipcMain } = require('electron');
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

            // Renderer cannot directly access Node.js
            nodeIntegration: false,

            // Communication happens through preload IPC
            contextIsolation: true,

            // Keep enabled/disabled according to Electron compatibility
            sandbox: false,

            // Prevent Electron from opening unexpected windows
            webviewTag: false
        }
    });

    // Load local BeeForce application
    mainWindow.loadFile(
        path.join(
            __dirname,
            'renderer',
            'index.html'
        )
    );

    // Optional: log renderer loading errors
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

    Object.keys(query).forEach(function (key) {

        const value = query[key];

        if (value === undefined || value === null) {
            return;
        }

        if (Array.isArray(value)) {

            value.forEach(function (item) {

                params.append(
                    key,
                    String(item)
                );

            });

        } else {

            params.append(
                key,
                String(value)
            );
        }
    });

    const encoded = params.toString();

    return encoded
        ? '?' + encoded
        : '';
}

// ============================================================
// Convert Node response headers to plain object
// ============================================================

function normalizeResponseHeaders(headers) {

    const result = {};

    Object.keys(headers || {}).forEach(
        function (key) {

            const value = headers[key];

            if (Array.isArray(value)) {

                result[key] = value.join(', ');

            } else if (value !== undefined) {

                result[key] = String(value);
            }
        }
    );

    return result;
}

// ============================================================
// Native BeeForce API request
// ============================================================

function makeApiRequest(request) {

    return new Promise(function (resolve) {

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

            // Make sure the path starts with /
            if (!requestPath.startsWith('/')) {
                requestPath = '/' + requestPath;
            }

            const queryString =
                buildQueryString(
                    request.query
                );

            const headers = Object.assign(
                {},
                request.headers || {}
            );

            // Remove browser-only headers that should not
            // be forwarded by the native application.
            delete headers.host;
            delete headers.connection;
            delete headers['content-length'];

            const body =
                request.body !== undefined &&
                request.body !== null
                    ? String(request.body)
                    : null;

            // If there is a body and no Content-Type was supplied,
            // JSON is the normal format used by BeeForce.
            if (
                body !== null &&
                body.length > 0
            ) {

                const hasContentType =
                    Object.keys(headers).some(
                        function (key) {
                            return key.toLowerCase() ===
                                'content-type';
                        }
                    );

                if (!hasContentType) {

                    headers['Content-Type'] =
                        'application/json';
                }
            }

            const options = {

                hostname: target.host,

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

            const req = https.request(
                options,
                function (res) {

                    let responseBody = '';

                    res.setEncoding('utf8');

                    res.on(
                        'data',
                        function (chunk) {

                            responseBody += chunk;
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
                                    res.statusCode || 0,

                                headers:
                                    responseHeaders,

                                body:
                                    responseBody
                            });
                        }
                    );
                }
            );

            // ====================================================
            // Network error
            // ====================================================

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

            // ====================================================
            // Timeout
            // ====================================================

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

            // ====================================================
            // Request body
            // ====================================================

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
    });
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
//
// Renderer JavaScript asks:
// window.beeForce.getAppFile('common.js')
//
// Electron reads:
// renderer/common.js
//
// No Gist.
// No GitHub.
// No network.
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

            // Only simple filenames are allowed.
            //
            // Reject:
            // ../file.js
            // ..\file.js
            // C:\file.js
            // /file.js
            // folders/file.js
            //
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

            // Only JavaScript files can be requested
            if (!filename.toLowerCase().endsWith('.js')) {

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

            // Extra protection:
            // make absolutely sure the resolved path
            // remains inside renderer/.
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

        createWindow();

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