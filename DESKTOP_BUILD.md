# Configuration Portal Windows Desktop Build

This repository keeps the existing Streamlit code unchanged and adds a production Electron desktop shell. The installed app starts an embedded `app.exe` backend automatically, waits for its internal Streamlit localhost server, and renders the app inside an Electron `BrowserWindow`.

End users never run `streamlit run app.py`, never install Python, never see a terminal, and never open a browser or localhost URL manually.

## Full folder structure

```text
.
├── app.py                         # Existing Streamlit entry point, unchanged
├── modules/                       # Existing Python feature modules, bundled into app.exe
├── services/                      # Existing Python services, bundled into app.exe
├── assets/                        # Optional data/assets folder bundled into app.exe
├── configs/                       # Optional config folder bundled into app.exe
├── requirements.txt               # Existing Python dependencies
├── package.json                   # Electron scripts + electron-builder / NSIS config
├── scripts/
│   ├── build_windows_desktop.ps1  # End-to-end Windows installer build script
│   └── create_icon.py             # Generated Windows icon asset
├── .github/workflows/
│   └── windows-desktop-release.yml # GitHub Actions release-ready installer workflow
├── build/
│   └── pyinstaller-app.spec       # One-file PyInstaller build for app.exe
└── electron/
    ├── main.js                    # Electron runtime, backend manager, tray, updater
    ├── preload.js                 # Secure context bridge
    ├── splash.html                # Dark startup splash screen
    ├── desktop_backend.py         # PyInstaller entry point; launches bundled Streamlit
    └── assets/
        └── icon.ico               # Windows app/tray/installer icon
```

## Production runtime architecture

1. User launches **Configuration Portal** from the installed shortcut.
2. Electron shows the splash screen immediately.
3. Electron checks whether `127.0.0.1:8501` is available.
4. Electron starts the bundled backend executable internally:

   ```text
   resources\backend\app.exe
   ```

5. `app.exe` runs the bundled `app.py` through Streamlit in headless localhost mode.
6. Electron repeatedly probes `http://localhost:8501` until the server responds. No fixed sleep is used.
7. Electron opens the Streamlit UI inside a maximized secure `BrowserWindow`.
8. Closing the window minimizes to tray; tray **Quit** stops `app.exe` and exits.

## Build-machine prerequisites

Install these only on the Windows build machine:

- Windows 10/11 x64
- Python 3.10+
- Node.js 20+
- npm
- Git

Target user machines do **not** need Python, Streamlit, Node.js, npm, or any global `streamlit` command.


## Generated icon asset

`electron/assets/icon.ico` is generated at build time and intentionally ignored by git because some PR systems reject binary files. Generate it with:

```powershell
npm run assets:icon
```

The same icon-generation step runs automatically before `npm run electron:dev`, `npm run python:build`, and `npm run dist`.

## Install build dependencies

```powershell
npm install
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
```

## PyInstaller one-file backend build

Recommended command:

```powershell
pyinstaller --clean --noconfirm build/pyinstaller-app.spec
```

Expected output:

```text
dist\app.exe
```

The spec builds a one-file, no-console backend executable named `app.exe`; embeds `app.py`; bundles `modules/*`, `services/*`, `assets/*`, and `configs/*`; collects Streamlit, pandas, and Playwright; and includes hidden imports for dynamic Streamlit/runtime dependencies.

### Full equivalent PyInstaller command

The checked-in spec is preferred because it auto-discovers all current and future files under `modules/`, `services/`, `assets/`, and `configs/`. If you need the explicit command form, run this from the repository root on Windows:

```powershell
pyinstaller --clean --noconfirm --onefile --noconsole --name app --icon electron\assets\icon.ico --collect-all streamlit --collect-all pandas --collect-all playwright --add-data "app.py;." --add-data "modules;modules" --add-data "services;services" --add-data "assets;assets" --add-data "configs;configs" --hidden-import altair --hidden-import openpyxl --hidden-import pptx --hidden-import requests --hidden-import tornado --hidden-import watchdog --hidden-import modules.paycodes --hidden-import modules.paycode_events --hidden-import modules.paycode_combinations --hidden-import modules.paycode_event_sets --hidden-import modules.shift_templates --hidden-import modules.shift_template_sets --hidden-import modules.schedule_patterns --hidden-import modules.schedule_pattern_sets --hidden-import modules.employee_lookup_table --hidden-import modules.organization_location_lookup_table --hidden-import modules.accruals --hidden-import modules.accrual_policies --hidden-import modules.accrual_policy_sets --hidden-import modules.timeoff_policies --hidden-import modules.timeoff_policy_sets --hidden-import modules.regularization_policies --hidden-import modules.regularization_policy_sets --hidden-import modules.roles --hidden-import modules.overtime_policies --hidden-import modules.timecard_updation --hidden-import modules.punch --hidden-import modules.schedule_pattern_mapper --hidden-import modules.known_locations --hidden-import modules.organization_locations --hidden-import modules.schedule_delete --hidden-import modules.admin_logs --hidden-import modules.access_control --hidden-import modules.ui_helpers --hidden-import services.auth --hidden-import services.activity_logger --hidden-import services.api electron\desktop_backend.py
```

## Electron development commands

Run the Python backend directly for debugging:

```powershell
npm run backend:dev
```

Run Electron in development mode. Electron will start `python electron/desktop_backend.py`, wait for localhost readiness, and load the app internally:

```powershell
npm run electron:dev
```

## Installer build commands

Build the backend and installer in one command:

```powershell
npm run dist
```

Or run the complete Windows build helper, which verifies tools, installs dependencies unless `-SkipInstall` is used, builds `dist\app.exe`, and creates the NSIS installer:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows_desktop.ps1
```

To publish release artifacts with electron-builder after setting `GH_TOKEN`:

```powershell
npm run release:github
```

The equivalent npm alias for Windows builders is:

```powershell
npm run build:windows
```

If `dist\app.exe` already exists and you only want to rebuild the Electron installer:

```powershell
npm run dist:electron
```

Final installer output:

```text
release\Configuration Portal-1.0.0-Setup.exe
```

## Installer features

The NSIS configuration creates:

- a Windows `Setup.exe`
- desktop shortcut
- Start menu shortcut
- uninstall entry in Windows Apps & Features
- optional install-directory selection
- bundled `resources\backend\app.exe`

## Auto-update with GitHub Releases

`package.json` includes a GitHub Releases publisher:

```json
"publish": [
  {
    "provider": "github",
    "owner": "venkatesh-beep",
    "repo": "Full-Configuration-Module",
    "releaseType": "release"
  }
]
```

Release steps:

1. Update `version` in `package.json`.
2. Build locally with `npm run dist`, or use the checked-in GitHub Actions workflow.
3. Create and push a tag such as `v1.0.0` to run `.github/workflows/windows-desktop-release.yml` automatically.
4. For manual CI builds, run **Build Windows Desktop Installer** from GitHub Actions and set `publish_release` to `true` when release publication is desired.
5. In CI or private repositories, keep `GH_TOKEN` available before running electron-builder publish commands.

The app checks for updates only when packaged. Automatic downloading is disabled by default so release signing, approval, and rollout policies can be added safely later.

## Runtime logs and error handling

Logs are written per Windows user:

```text
%APPDATA%\Configuration Portal\logs\electron.log
%APPDATA%\Configuration Portal\logs\backend.log
```

Implemented failure handling:

- detects port `8501` conflicts before starting the backend
- shows a user-friendly error dialog when startup fails
- waits for localhost using HTTP polling, not fixed delays
- restarts the backend automatically after crashes, up to three times
- kills the full backend process tree on Windows using `taskkill /T /F`
- blocks external navigation so no browser or localhost URL is shown to users

## Production optimization notes

- Streamlit telemetry is disabled for the embedded runtime.
- Electron renderer uses `nodeIntegration: false`, `contextIsolation: true`, and sandboxing.
- The preload bridge exposes only status/version information and no tokens, secrets, or Node.js APIs.
- Sensitive API/session/token logic remains in the Python backend.
- Build outputs, Node dependencies, release artifacts, and Python caches are ignored by git.

## Test on a clean Windows machine

1. Copy only `release\Configuration Portal-1.0.0-Setup.exe` to another Windows machine.
2. Confirm Python and Streamlit are not installed or not on `PATH`.
3. Run the installer.
4. Launch **Configuration Portal** from the desktop shortcut or Start menu.
5. Confirm no terminal or command prompt appears.
6. Confirm no external browser opens.
7. Confirm the app opens directly in the Electron window.
8. Close the window and confirm it stays available in the system tray.
9. Restore from the tray.
10. Quit from the tray and confirm no `app.exe` backend process remains.
11. Uninstall from Windows Apps & Features and confirm shortcuts are removed.

## Pull request creation troubleshooting

If PR creation fails after these desktop-wrapper changes, verify the local checkout has a GitHub remote and that the current branch has been pushed. This environment may have no `origin` remote configured, so GitHub cannot create a pull request until the branch exists on GitHub.

In this workspace, automated PR creation can also fail when GitHub credentials or remotes are unavailable to the agent. The code changes are still committed locally; use the commands below to publish the branch before opening the PR.

```powershell
git remote -v
```

If no remote is listed, add the repository remote:

```powershell
git remote add origin https://github.com/venkatesh-beep/Full-Configuration-Module.git
```

Push the current branch and set upstream tracking:

```powershell
git push -u origin HEAD
```

Then create the PR with GitHub CLI:

```powershell
gh pr create --base main --head HEAD --title "Add Electron desktop wrapper for Configuration Portal" --body-file DESKTOP_BUILD.md
```

If GitHub CLI is unavailable, open the pushed branch in GitHub and use **Compare & pull request**. The PR should target `main` and include the Electron/PyInstaller packaging summary plus the build/test limitations documented above.
