# MERCURY X Recording Guide

## Purpose

This guide provides step-by-step instructions for capturing screenshots and recording demo videos from the MERCURY X Control Center and portfolio page. Follow these steps to produce clean, professional captures that preserve provenance labels and claim boundaries.

---

## 1. Environment preparation

### Launch the Control Center

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m http.server 4173 --directory ui/control-center
```

Open `http://127.0.0.1:4173` in the browser.

### Launch the portfolio page

In a separate PowerShell window:

```powershell
.\.venv\Scripts\python.exe -m http.server 4174
```

Open `http://127.0.0.1:4174/ui/portfolio/` in the browser.

### Verify both surfaces load

- Control Center: mode banner reads "STATIC DEMO · No live infrastructure" and the overview renders with metric cards.
- Portfolio: hero section renders with orbit visualization and "Research / Experimental" chip.

If either fails to load, check that the Python HTTP server started without port conflicts and that you are using the correct paths.

---

## 2. Browser window preparation

### Recommended browser

Use a Chromium-based browser (Chrome, Edge, Brave) or Firefox. Avoid browsers with custom UI chrome, heavy bookmark bars, or non-standard rendering that could distort the interface.

### Window size and resolution

| Capture type | Recommended window size | Display scaling |
|---|---|---|
| Full-page screenshots | **1920 × 1080** logical pixels | 100% or native |
| High-DPI / retina screenshots | **2560 × 1440** logical pixels | 100% or native |
| Video recording | **1920 × 1080** at 30 fps or 60 fps | 100% |

To set an exact viewport:
1. Open DevTools (`F12` or `Ctrl+Shift+I`).
2. Toggle Device Toolbar (`Ctrl+Shift+M`).
3. Set a custom responsive size (e.g., 1920 × 1080).
4. Alternatively, resize the browser window manually and use a ruler extension to verify dimensions.

### Before each capture session

- [ ] Close **all unrelated browser tabs**. Use a dedicated browser window or profile.
- [ ] Hide the **bookmarks bar** (`Ctrl+Shift+B` in Chrome/Edge).
- [ ] Clear the **address bar** of any sensitive or unrelated URLs. Navigate directly to the target URL.
- [ ] Disable browser **notifications** to prevent popups during recording.
- [ ] Disable **browser extensions** that add visible UI elements (ad blockers with badge counts, developer tools, etc.).
- [ ] Set browser zoom to **100%** (`Ctrl+0`).
- [ ] Verify the browser's **color scheme** is set to dark (the Control Center uses `color-scheme: dark`).
- [ ] **Do not** use browser themes that alter the tab bar, scrollbar, or window chrome colors.

---

## 3. Sensitive information checklist

Before recording, verify that **none** of the following are visible:

- [ ] Local file paths in the address bar (use `http://127.0.0.1:4173` not `file:///...`)
- [ ] Terminal history with unrelated commands, personal directories, or credentials
- [ ] Other browser tabs showing email, social media, chat, or personal sites
- [ ] Desktop wallpaper, taskbar notifications, or system tray icons (if recording the full screen, use a clean desktop or record only the browser window)
- [ ] DevTools open with console errors or network requests
- [ ] Any `.env` files, API keys, tokens, or credentials
- [ ] Personal username in the terminal prompt (consider a temporary clean prompt: `$env:PROMPT = "PS> "`)

### Terminal recording

If the recording includes terminal commands (e.g., launching the server), open a **fresh** PowerShell window and navigate directly to the repository:

```powershell
cd C:\Users\DELL\Downloads\Mercury-x
```

Do not scroll up to reveal prior command history.

---

## 4. Scenario reset procedure

Scenarios must be reset to their initial state before advancing to the specific step required by the [SCREENSHOT_PLAN.md](SCREENSHOT_PLAN.md) or [DEMO_VIDEO_SCRIPT.md](DEMO_VIDEO_SCRIPT.md).

### Full reset

1. Navigate to the **Scenario Player** view (`#/scenarios`).
2. Click the **↺ Reset** button in the scenario controls.
3. The scenario status should read **READY** and the step counter should show **1 / N**.

### Selecting a specific scenario

1. In the scenario catalog sidebar, click the desired scenario card.
2. The scenario resets automatically on selection.
3. Verify the hero shows the correct scenario name and "READY" status.

### Advancing to a specific step

1. Click **Start scenario** to begin (status changes from READY to RUNNING).
2. Click **Next step →** repeatedly until the desired step is reached.
3. Verify the step counter, current step label, and lifecycle highlight match the screenshot plan.

### Between scenarios

Always reset the current scenario before selecting the next one. The system handles this automatically on scenario selection, but verify the state is clean.

---

## 5. Recording order

Follow this sequence for a smooth recording session. The order minimizes unnecessary scenario switches.

### Screenshots (batch capture)

1. **Screenshot 01** — Mission Control Overview (default state, no scenario)
2. **Screenshot 02** — Workload Intelligence (select wrk-7f2a, no scenario)
3. **Screenshot 03** — Execution Graph (default state)
4. **Screenshot 09** — Digital Twin (default state)
5. **Screenshot 11** — Governance + Evidence (default state)
6. **Screenshot 12** — Portfolio Page Hero (switch to portfolio tab)
7. Select `normal-orchestration` scenario → advance to step 8 → **Screenshot 04** — Compute Fabric
8. Advance to step 10 → **Screenshot 10** — Scenario Player
9. Select `quality-slo-conflict` → advance to step 4 → **Screenshot 05** — SLO Quality Conflict
10. Select `live-migration` → advance to step 8 → **Screenshot 06** — Migration & Recovery
11. Select `adversarial-counterfactual` → advance to step 5 → **Screenshot 07** — Scheduler Intelligence
12. Select `federated-privacy` → advance to step 6 → **Screenshot 08** — Federation & Privacy

### Primary demo video

Follow the [DEMO_VIDEO_SCRIPT.md](DEMO_VIDEO_SCRIPT.md) segment order. Record in one continuous take if possible; editing is easier than multiple spliced takes. Allow 2–3 seconds of silence between segments for edit points.

### Short demo video

Record after the primary demo, when you are familiar with the navigation flow. Follow the [SHORT_DEMO_SCRIPT.md](SHORT_DEMO_SCRIPT.md) segment order.

---

## 6. Provenance label visibility

### Rules

1. **Never** crop, blur, overlay, or digitally remove `STATIC DEMO`, `SYNTHETIC`, `SIMULATED`, `UNKNOWN`, or `UNCALIBRATED` labels from any capture.
2. The sidebar **mode banner** ("STATIC DEMO · No live infrastructure") must be visible in full-viewport captures.
3. The **source legend** on the overview page must be visible in overview captures.
4. **Provenance badges** (colored diamond + source type text) on metric cards, table rows, and panels are part of the interface—they should not be treated as visual clutter.
5. **Callout boxes** (demonstration boundary, calibration honesty, infrastructure boundary, human control) must remain visible and readable.

### Verification

After capturing, review each screenshot and video frame for:

- [ ] Mode banner visible in sidebar
- [ ] Source legend visible on overview
- [ ] Provenance badges visible on data elements
- [ ] Boundary callouts visible and legible
- [ ] No provenance labels accidentally cropped

---

## 7. Capture tools

### Screenshots

| Platform | Recommended tool | Notes |
|---|---|---|
| Windows | **Snipping Tool** (`Win+Shift+S`) or **ShareX** | ShareX supports exact region capture, annotations, and auto-naming |
| Browser | **DevTools screenshot** (`Ctrl+Shift+P` → "Capture screenshot") | Captures the viewport at exact resolution without window chrome |
| Cross-platform | **Full Page Screen Capture** browser extension | For scrolling captures (portfolio page) |

### Video recording

| Platform | Recommended tool | Notes |
|---|---|---|
| Windows | **OBS Studio** (free) or **Xbox Game Bar** (`Win+G`) | OBS supports exact resolution, audio input selection, and scene composition |
| Cross-platform | **OBS Studio** | Set output to 1920×1080 at 30 fps minimum; use MP4 or MKV container |

For OBS:
- Add a **Window Capture** source targeting only the browser window.
- Enable **Audio Input Capture** for narration.
- Disable system audio capture unless intentional.
- Record at **CRF 18–22** for high quality with reasonable file size.

---

## 8. Final recording checklist

Before the session:

- [ ] Both servers running (port 4173 for Control Center, port 4174 for portfolio)
- [ ] Browser window clean (no extra tabs, bookmarks bar hidden, 100% zoom)
- [ ] No sensitive information visible
- [ ] Recording tool configured (resolution, frame rate, audio)
- [ ] Narration script printed or on a second monitor
- [ ] Microphone tested and audio levels checked

During the session:

- [ ] Move cursor deliberately—avoid rapid or nervous movement
- [ ] Scroll slowly and predictably
- [ ] Pause 2–3 seconds on each panel before narrating
- [ ] Reset scenarios before advancing to target steps
- [ ] Verify provenance labels are visible in frame

After the session:

- [ ] Review all captures for provenance label visibility
- [ ] Verify no sensitive information leaked into any frame
- [ ] Run the claim-safety checklist from the demo script
- [ ] Save source files alongside exports for future editing
- [ ] Name files descriptively (e.g., `mercury-x-mission-control-overview.png`, `mercury-x-demo-full.mp4`)

---

## 9. Output file naming

| Type | Pattern | Example |
|---|---|---|
| Screenshot | `mercury-x-{view}-{variant}.png` | `mercury-x-mission-control-overview.png` |
| Primary demo | `mercury-x-demo-full.mp4` | |
| Short demo | `mercury-x-demo-short.mp4` | |
| Thumbnail | `mercury-x-thumbnail.png` | |

Store captures in a local directory outside the repository (e.g., `~/mercury-x-media/`). Do not commit large binary media files to the Git repository unless a Git LFS strategy is in place.

---

## 10. Reference documents

- [SCREENSHOT_PLAN.md](SCREENSHOT_PLAN.md) — exact capture specifications
- [DEMO_VIDEO_SCRIPT.md](DEMO_VIDEO_SCRIPT.md) — primary ~5 minute demo narration
- [SHORT_DEMO_SCRIPT.md](SHORT_DEMO_SCRIPT.md) — 60–90 second short demo narration
- [docs/RUNNING.md](../RUNNING.md) — server launch and validation commands
- [docs/ui/CONTROL_CENTER.md](../ui/CONTROL_CENTER.md) — Control Center documentation
- [docs/ui/DEMO_SCENARIOS.md](../ui/DEMO_SCENARIOS.md) — scenario documentation
- [docs/PORTFOLIO.md](../PORTFOLIO.md) — portfolio page documentation
