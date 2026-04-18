# Dhurandhar

## What This Is

A macro-first, vision-gated automation framework for gaming minigames. It executes scripted action sequences (key presses, clicks, drags, scrub patterns) but uses screen vision checks at key decision points instead of blind delays. Designed to grow — new minigames are added as self-contained handler plugins.

## Core Value

Reliable, undetectable minigame automation that uses visual confirmation (not timing) to gate macro transitions, making it stable across variable game conditions.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Core macro engine with state machine and tick loop
- [ ] Vision system (region capture, template matching, pixel color, region change detection)
- [ ] Humanized input simulation (Bezier curves, jitter, random delay variance)
- [ ] Honey Scrape + Drag minigame handler
- [ ] Basic Grind minigame handler
- [ ] GUI setup wizard for in-game calibration (positions, regions, template capture)
- [ ] JSON config system for all coordinates, templates, and thresholds
- [ ] Resolution-independent positioning (fullscreen borderless, variable resolution)
- [ ] Debug logging with state transitions and vision events
- [ ] Pluggable handler architecture for future minigame growth

### Out of Scope

- OCR-based text reading — template/pixel matching is sufficient for now
- Auto-detection of which minigame is active — manual selection for v1
- Scheduler/rotation system between minigames — single minigame per session for now
- Mobile/remote control — local desktop execution only

## Context

- Target environment: Fullscreen borderless window, resolution varies per system
- Python 3.10+ on Windows
- Dependencies: pyautogui, opencv-python, mss, numpy, keyboard
- The framework must handle resolution differences — coordinates should scale or be re-calibrated via the setup wizard
- Two initial minigames define the handler pattern; architecture must support easy addition of more

## Constraints

- **Platform**: Windows only (pyautogui + keyboard + mss)
- **Detection avoidance**: All inputs must include randomized timing and imperfect cursor paths
- **Performance**: Vision checks must use region-based capture (never full screen scans)
- **No Python installed yet**: User needs to install Python 3.10+ before running

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Macro-first with vision gates | Simpler than full reactive AI, more reliable than blind timing | — Pending |
| Python + pyautogui | Fastest path to working input simulation on Windows | — Pending |
| Tkinter GUI for setup wizard | Ships with Python, no extra dependencies | — Pending |
| Template matching over OCR | Faster, simpler, sufficient for visual cues | — Pending |
| Handler plugin pattern | Each minigame is isolated, easy to add/remove | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-17 after initialization*
