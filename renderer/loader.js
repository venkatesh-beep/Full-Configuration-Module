(function () {
    'use strict';

    var LOADER_VERSION = '5.0';

    if (window.__BF_LOADER_RUNNING__) {
        console.log('[BF Loader] Already running.');
        return;
    }

    window.__BF_LOADER_RUNNING__ = true;

    var isElectron =
        !!(
            window.beeForce &&
            typeof window.beeForce.getAppFile === 'function'
        );

    console.log(
        '[BF Loader] BeeForce Loader v' +
        LOADER_VERSION
    );

    console.log(
        '[BF Loader] Mode: ' +
        (isElectron ? 'Electron local files' : 'Browser')
    );

    function loadLocalFile(filename) {

        if (!isElectron) {
            return Promise.reject(
                new Error(
                    'BeeForce Electron bridge is not available.'
                )
            );
        }

        return window.beeForce
            .getAppFile(filename)
            .then(function (result) {

                if (!result || !result.ok) {
                    throw new Error(
                        result && result.error
                            ? result.error
                            : 'Unable to load ' + filename
                    );
                }

                return result.content;
            });
    }

    function executeFile(filename, code) {

        try {

            console.log(
                '[BF Loader] Executing ' + filename
            );

            (0, eval)(code);

            console.log(
                '[BF Loader] Loaded ' + filename
            );

        } catch (error) {

            console.error(
                '[BF Loader] Error executing ' + filename,
                error
            );

            throw error;
        }
    }

    function loadBridge() {

        return loadLocalFile('bridge.js')
            .then(function (code) {

                executeFile(
                    'bridge.js',
                    code
                );

            });
    }

    function loadIndex() {

        return loadLocalFile('index.js')
            .then(function (code) {

                var prelude =
                    'var BF_IS_DESKTOP = true;' +
                    'var BF_LOADER_VERSION = ' +
                    JSON.stringify(LOADER_VERSION) +
                    ';' +
                    'var BF_LOAD_LOCAL_FILE = ' +
                    'window.beeForce.getAppFile;' +
                    '\n';

                executeFile(
                    'index.js',
                    prelude + code
                );
            });
    }

    function start() {

        loadBridge()
            .then(function () {
                return loadIndex();
            })
            .then(function () {

                console.log(
                    '%c[BF Loader] BeeForce started successfully.',
                    'color:#059669;font-weight:bold;'
                );

                window.__BF_LOADER_RUNNING__ = false;

            })
            .catch(function (error) {

                console.error(
                    '[BF Loader] Startup failed:',
                    error
                );

                window.__BF_LOADER_RUNNING__ = false;

                alert(
                    'BeeForce failed to start.\n\n' +
                    error.message
                );
            });
    }

    if (!isElectron) {

        alert(
            'BeeForce Electron bridge is not available.'
        );

        window.__BF_LOADER_RUNNING__ = false;

        return;
    }

    start();

})();