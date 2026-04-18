"""
Dhurandhar — Honey Scrape + Drag minigame handler.

Macro sequence:
    1. Press E           -> vision gate: UI appeared?
    2. Click start point -> hold for ~1 second
    3. Sweep left-right  -> vision gate: clean honey detected?
    4. Drag to target    -> fixed action
    5. Loop if counter < target, else done
"""

from enum import Enum, auto
from minigames.base_handler import BaseHandler
import time
import logging

logger = logging.getLogger("dhurandhar.honey")


class HoneyState(Enum):
    INIT = auto()
    CLICK_AND_HOLD = auto()
    SCRAPE = auto()
    DRAG = auto()
    VERIFY = auto()
    COMPLETE = auto()


class HoneyScrapeHandler(BaseHandler):
    """Honey Scrape + Drag minigame macro.

    Runs a scripted sequence with vision gates at key transitions.
    All positions/regions/templates come from config.
    """

    MAX_INIT_RETRIES = 3
    MAX_SCRAPE_TIMEOUT = 15.0

    def __init__(self):
        super().__init__("Honey Scrape")
        self.state = HoneyState.INIT
        self.counter = 0
        self.target_count = 10
        self.init_retries = 0

    def detect(self, frame):
        return True

    def run(self, vision, inp, config):
        """Execute one full cycle (press E through all scrapes)."""
        cfg = config.get("honey_game", {})
        self.target_count = cfg.get("target_count", 10)

        while self.state != HoneyState.COMPLETE:
            if self._is_aborted():
                logger.info("[HONEY] Aborted")
                self.state = HoneyState.COMPLETE
                return False

            logger.info(f"[HONEY] {self.state.name} | {self.counter}/{self.target_count}")

            if self.state == HoneyState.INIT:
                self._do_init(vision, inp, cfg)
            elif self.state == HoneyState.CLICK_AND_HOLD:
                self._do_click_and_hold(vision, inp, cfg)
            elif self.state == HoneyState.SCRAPE:
                self._do_scrape(vision, inp, cfg)
            elif self.state == HoneyState.DRAG:
                self._do_drag(inp, cfg)
            elif self.state == HoneyState.VERIFY:
                self._do_verify(vision, cfg)

        return not self._is_aborted()

    # ── Macro Steps ───────────────────────────────────────

    def _do_init(self, vision, inp, cfg):
        """Step 1: Press E -> vision gate: wait for UI."""
        logger.info("[HONEY] [STEP 1] Pressing Start Key ('e')")
        inp.press_key(cfg.get("start_key", "e"))

        ui_template = cfg.get("templates", {}).get("ui_active")
        ui_region = cfg.get("ui_region")

        if ui_template and ui_region:
            logger.info("[HONEY] [STEP 1] Waiting for UI to appear (Vision Gate)...")
            found, _ = vision.wait_for_template(
                ui_template, tuple(ui_region), timeout=5.0
            )
            if found:
                logger.info("[HONEY] [STEP 1] UI detected! Proceeding to click-and-hold.")
                self.state = HoneyState.CLICK_AND_HOLD
                self.init_retries = 0
            else:
                self.init_retries += 1
                if self.init_retries >= self.MAX_INIT_RETRIES:
                    logger.error("[HONEY] [STEP 1] UI not detected after max retries")
                    self.state = HoneyState.COMPLETE
                else:
                    logger.warning(f"[HONEY] [STEP 1] UI not detected, retry {self.init_retries}")
                    time.sleep(0.5)
        else:
            logger.info("[HONEY] [STEP 1] No UI template configured. Blindly waiting 0.5s.")
            time.sleep(0.5)
            self.state = HoneyState.CLICK_AND_HOLD

    def _do_click_and_hold(self, vision, inp, cfg):
        """Step 2: Click start position, hold, drag slightly, release."""
        pos = cfg.get("start_click", [960, 540])
        hold_ms = cfg.get("hold_duration_ms", 150) # Extremely fast hold

        logger.info(f"[HONEY] [STEP 2] Clicking start button at {pos}")
        inp.click(pos[0], pos[1])
        inp.delay(50) 

        # 1. Move to hold position and mouse down
        hold_pos = cfg.get("hold_position", pos)
        logger.info(f"[HONEY] [STEP 2] Moving to hold position {hold_pos} and pressing mouse down.")
        inp.mouse_down(hold_pos[0], hold_pos[1])
        
        # 2. Hold for a short duration
        logger.info(f"[HONEY] [STEP 2] Holding mouse down for {hold_ms}ms...")
        inp.delay(hold_ms)

        # 3. Drag a little bit to one side (e.g., +40px right)
        test_x = hold_pos[0] + 40
        test_y = hold_pos[1]
        logger.info(f"[HONEY] [STEP 2] Dragging slightly right to ({test_x}, {test_y})...")
        inp.smooth_move(test_x, test_y, duration_ms=50) 
        inp.delay(10) 

        # 4. Leave holding (release)
        logger.info("[HONEY] [STEP 2] Releasing mouse hold.")
        inp.mouse_up()
        
        # 5. Wait briefly before starting the left/right scraping
        logger.info("[HONEY] [STEP 2] Waiting 50ms before starting rapid sweeps...")
        inp.delay(50) 

        self.state = HoneyState.SCRAPE

    def _do_scrape(self, vision, inp, cfg):
        """Step 3: Sweep left-right across region until clean detected."""
        region = cfg.get("scrape_region", [400, 300, 400, 300])

        clean_template = cfg.get("templates", {}).get("clean")
        scraper_reset_tpl = cfg.get("templates", {}).get("scraper_reset")

        logger.info(f"[HONEY] [STEP 3] Starting rapid horizontal sweeps in region {region}...")
        start_time = time.time()
        sweep_count = 0

        while time.time() - start_time < self.MAX_SCRAPE_TIMEOUT:
            if self._is_aborted():
                inp.mouse_up() # Safety release
                self.state = HoneyState.COMPLETE
                return

            # Sweep left-to-right-to-left smoothly and blazing fast
            completed = inp.sweep_horizontal(region, speed_ms=60) 
            if not completed:
                inp.mouse_up()
                self.state = HoneyState.COMPLETE
                return

            sweep_count += 1

            # Vision gate: Check if scraper snapped back to original position
            if scraper_reset_tpl:
                reset_region = cfg.get("scraper_reset_region", [0, 0, 100, 100])
                found, conf, _ = vision.region_matches_template(
                    tuple(reset_region), scraper_reset_tpl, threshold=0.85
                )
                logger.info(f"[HONEY] [STEP 3] Sweep {sweep_count} | Scraper Reset Conf: {conf:.2f}")
                if found:
                    logger.info(f"[HONEY] [STEP 3] Scraper reset detected (conf {conf:.2f}) after {sweep_count} sweeps")
                    break

            # Fallback Vision gate: check if clean honey texture is present
            if clean_template:
                texture_region = cfg.get("honey_texture_region", region)
                found, conf, _ = vision.region_matches_template(
                    tuple(texture_region), clean_template, threshold=0.92
                )
                logger.info(f"[HONEY] [STEP 3] Sweep {sweep_count} | Clean Honey Conf: {conf:.2f}")
                if found:
                    logger.info(f"[HONEY] [STEP 3] Clean texture detected (conf {conf:.2f}) after {sweep_count} sweeps")
                    break

            if not scraper_reset_tpl and not clean_template:
                # No template provided, sweep a fixed number of times
                if sweep_count >= 5:
                    logger.info("[HONEY] [STEP 3] No template provided, fixed sweeps done")
                    break
        else:
            logger.warning("[HONEY] [STEP 3] Scrape timeout reached!")

        # Once done, release the hold
        inp.mouse_up()

        if not self._is_aborted():
            logger.info("[HONEY] [STEP 3] Scraping complete. Preparing to drag...")
            inp.delay(50) 
            self.state = HoneyState.DRAG

    def _do_drag(self, inp, cfg):
        """Step 4: Drag cleaned piece to target drop zone."""
        # Use honey_texture_region because that's where the clean honey is located!
        region = cfg.get("honey_texture_region", cfg.get("scrape_region", [400, 300, 400, 300]))
        drag_start = (region[0] + region[2] // 2, region[1] + region[3] // 2)
        drag_end = tuple(cfg.get("drag_target", [1200, 540]))

        logger.info(f"[HONEY] [STEP 4] Dragging clean honey from {drag_start} to {drag_end}")
        # Faster drag (100ms)
        inp.drag(drag_start, drag_end, duration_ms=100) 
        inp.delay(50) 
        self.state = HoneyState.VERIFY

    def _do_verify(self, vision, cfg):
        """Step 5: Increment counter, loop or complete."""
        self.counter += 1
        logger.info(f"[HONEY] [STEP 5] Iteration complete. Progress: {self.counter}/{self.target_count}")

        counter_region = cfg.get("counter_region")
        if counter_region:
            time.sleep(0.3)

        if self.counter >= self.target_count:
            logger.info(f"[HONEY] [STEP 5] Complete! {self.counter}/{self.target_count}")
            
            # Wait for UI to close before starting the next batch
            ui_template = cfg.get("templates", {}).get("ui_active")
            ui_region = cfg.get("ui_region")
            if ui_template and ui_region:
                logger.info("[HONEY] [DONE] Waiting for UI to close before resetting...")
                # Simple loop to wait until UI disappears
                start_wait = time.time()
                while time.time() - start_wait < 10.0:
                    found, _, _ = vision.region_matches_template(tuple(ui_region), ui_template, threshold=0.8)
                    if not found:
                        break
                    if self._is_aborted():
                        break
                    time.sleep(0.5)
                logger.info("[HONEY] [DONE] UI closed. Ready for next cycle.")
            else:
                inp.delay(500) # shorter blind wait

            self.state = HoneyState.COMPLETE
        else:
            logger.info(f"[HONEY] Progress: {self.counter}/{self.target_count}")
            logger.info(f"[HONEY] --- Starting Iteration {self.counter + 1} (Back to Step 2) ---")
            self.state = HoneyState.CLICK_AND_HOLD

    def reset(self):
        self.state = HoneyState.INIT
        self.counter = 0
        self.init_retries = 0
