/* =========================================================
 * BeeForce Configuration Portal
 * Electron API Bridge
 *
 * Architecture:
 *
 *   BeeForce modules
 *          |
 *        fetch()
 *          |
 *      bridge.js
 *          |
 *   window.beeForce.apiRequest()
 *          |
 *       Electron IPC
 *          |
 *       main.js
 *          |
 *      HTTPS request
 *          |
 *    BeeForce API
 *
 * No pywebview.
 * No localhost proxy.
 * No Gist API calls.
 * ========================================================= */

(function () {

    'use strict';

    // ---------------------------------------------------------
    // Make sure the Electron native bridge exists
    // ---------------------------------------------------------

    var hasElectronBridge =
        !!(
            window.beeForce &&
            typeof window.beeForce.apiRequest === 'function'
        );

    if (!hasElectronBridge) {

        console.warn(
            '[BeeForce Bridge] Electron native bridge is not available.'
        );

        return;
    }

    // ---------------------------------------------------------
    // Prevent bridge from being installed twice
    // ---------------------------------------------------------

    if (window.__BF_BRIDGE_ACTIVE__) {

        console.log(
            '[BeeForce Bridge] Already active.'
        );

        return;
    }

    window.__BF_BRIDGE_ACTIVE__ = true;

    // ---------------------------------------------------------
    // BeeForce API hosts
    //
    // This is a client-side dispatch list.
    //
    // The actual API destination/security check is also
    // enforced in Electron main.js.
    // ---------------------------------------------------------

    var KNOWN_HOSTS = {

        'esampark.beeforce.in':
            'production',

        'esampark-uat.beeforce.in':
            'uat'
    };

    // ---------------------------------------------------------
    // Keep the original browser fetch
    //
    // Requests to non-BeeForce hosts will continue normally.
    // ---------------------------------------------------------

    var nativeFetch =
        window.fetch.bind(window);

    // ---------------------------------------------------------
    // Create a minimal Fetch Response-compatible object
    //
    // Existing BeeForce modules expect:
    //
    // response.ok
    // response.status
    // response.headers.get()
    // response.json()
    // response.text()
    // response.clone()
    // ---------------------------------------------------------

    function makeShimResponse(
        status,
        headers,
        bodyText
    ) {

        var headerMap =
            new Headers(
                headers || {}
            );

        return {

            ok:
                status >= 200 &&
                status < 300,

            status:
                status,

            statusText:
                '',

            headers:
                headerMap,

            json:
                function () {

                    try {

                        return Promise.resolve(
                            JSON.parse(
                                bodyText || ''
                            )
                        );

                    } catch (error) {

                        return Promise.reject(
                            new TypeError(
                                'Failed to parse response as JSON: ' +
                                error.message
                            )
                        );
                    }
                },

            text:
                function () {

                    return Promise.resolve(
                        bodyText || ''
                    );
                },

            clone:
                function () {

                    return makeShimResponse(
                        status,
                        headers,
                        bodyText
                    );
                }
        };
    }

    // ---------------------------------------------------------
    // Convert Request/Headers into a plain object
    // ---------------------------------------------------------

    function convertHeaders(headers) {

        var result = {};

        try {

            new Headers(
                headers || {}
            ).forEach(
                function (value, key) {

                    result[key] = value;
                }
            );

        } catch (error) {

            console.warn(
                '[BeeForce Bridge] Could not process headers:',
                error
            );
        }

        return result;
    }

    // ---------------------------------------------------------
    // Convert request body into a string
    // ---------------------------------------------------------

    function getRequestBody(
        input,
        init,
        method
    ) {

        var mergedInit =
            init
                ? Object.assign({}, init)
                : {};

        if (
            mergedInit.body !== undefined &&
            mergedInit.body !== null
        ) {

            var explicitBody =
                mergedInit.body;

            if (
                typeof explicitBody ===
                'string'
            ) {

                return Promise.resolve(
                    explicitBody
                );
            }

            return Promise.resolve(
                String(explicitBody)
            );
        }

        if (
            typeof input !== 'string' &&
            input &&
            method !== 'GET' &&
            method !== 'HEAD'
        ) {

            var requestBody =
                input.body;

            if (
                requestBody !== undefined &&
                requestBody !== null
            ) {

                if (
                    typeof requestBody ===
                    'string'
                ) {

                    return Promise.resolve(
                        requestBody
                    );
                }

                return Promise.resolve(
                    String(requestBody)
                );
            }
        }

        return Promise.resolve(
            undefined
        );
    }

    // ---------------------------------------------------------
    // Replace window.fetch()
    // ---------------------------------------------------------

    window.fetch = function (
        input,
        init
    ) {

        var urlString;

        try {

            // -----------------------------------------------
            // Determine URL
            // -----------------------------------------------

            if (
                typeof input ===
                'string'
            ) {

                urlString = input;

            } else if (
                input &&
                input.url
            ) {

                urlString = input.url;

            } else {

                return nativeFetch(
                    input,
                    init
                );
            }

            // -----------------------------------------------
            // Parse URL
            // -----------------------------------------------

            var url =
                new URL(
                    urlString,
                    window.location.href
                );

            // -----------------------------------------------
            // Check whether this is a BeeForce API host
            // -----------------------------------------------

            var env =
                KNOWN_HOSTS[
                    url.hostname
                ];

            // -----------------------------------------------
            // Non-BeeForce request
            //
            // Examples:
            //
            // - local files
            // - images
            // - third-party resources
            // - browser resources
            //
            // Leave these untouched.
            // -----------------------------------------------

            if (!env) {

                return nativeFetch(
                    input,
                    init
                );
            }

            // -----------------------------------------------
            // Merge fetch options
            // -----------------------------------------------

            var mergedInit =
                init
                    ? Object.assign(
                        {},
                        init
                    )
                    : {};

            // -----------------------------------------------
            // HTTP method
            // -----------------------------------------------

            var method =
                mergedInit.method ||
                (
                    typeof input !== 'string' &&
                    input.method
                        ? input.method
                        : undefined
                ) ||
                'GET';

            method =
                String(method)
                    .toUpperCase();

            // -----------------------------------------------
            // Headers
            // -----------------------------------------------

            var existingHeaders =
                mergedInit.headers ||
                (
                    typeof input !== 'string' &&
                    input.headers
                        ? input.headers
                        : {}
                );

            var headersObj =
                convertHeaders(
                    existingHeaders
                );

            // -----------------------------------------------
            // Query parameters
            // -----------------------------------------------

            var query = {};

            url.searchParams.forEach(
                function (
                    value,
                    key
                ) {

                    query[key] =
                        value;
                }
            );

            // -----------------------------------------------
            // Request body
            // -----------------------------------------------

            return getRequestBody(
                input,
                init,
                method
            )
                .then(
                    function (bodyString) {

                        // -----------------------------------
                        // Prepare native request
                        // -----------------------------------

                        var request = {

                            method:
                                method,

                            path:
                                url.pathname,

                            query:
                                query,

                            headers:
                                headersObj,

                            env:
                                env,

                            body:
                                bodyString
                        };

                        console.log(
                            '[BeeForce Bridge] ' +
                            method +
                            ' ' +
                            url.hostname +
                            url.pathname
                        );

                        // -----------------------------------
                        // Send through Electron
                        // -----------------------------------

                        return window.beeForce
                            .apiRequest(
                                request
                            );
                    }
                )
                .then(
                    function (result) {

                        // -----------------------------------
                        // Native/network failure
                        // -----------------------------------

                        if (
                            result &&
                            result.error
                        ) {

                            throw new TypeError(
                                'BeeForce API request failed: ' +
                                (
                                    result.message ||
                                    result.error
                                )
                            );
                        }

                        // -----------------------------------
                        // Convert native response into
                        // fetch-compatible response
                        // -----------------------------------

                        return makeShimResponse(

                            result &&
                            result.status
                                ? result.status
                                : 0,

                            result &&
                            result.headers
                                ? result.headers
                                : {},

                            result &&
                            result.body !== undefined
                                ? result.body
                                : ''
                        );
                    }
                );

        } catch (error) {

            // -------------------------------------------------
            // Synchronous parsing error
            //
            // Preserve normal fetch behavior rather than
            // breaking unrelated browser/local requests.
            // -------------------------------------------------

            console.error(
                '[BeeForce Bridge] Fetch processing error:',
                error
            );

            return nativeFetch(
                input,
                init
            );
        }
    };

    console.log(
        '%c✓ BeeForce Electron API bridge active',
        'color:#059669;font-weight:bold;'
    );

})();