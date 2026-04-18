import time
import logging
import pyautogui
from enum import Enum, auto
from .base_handler import BaseHandler

logger = logging.getLogger("dhurandhar.jar")

class JarState(Enum):
    INIT = auto()
    CLICK = auto()
    ROTATE = auto()
    VERIFY = auto()
    COMPLETE = auto()

class FillJarHandler(BaseHandler):
    def __init__(self):
        super().__init__("Fill into Jar")
        self.state = JarState.INIT
        self.MAX_ROTATE_TIMEOUT = 60.0

    def detect(self, frame):
        """Used for future auto-detection. Currently just returns True when active."""
        return True

    def run(self, vision, inp, config):
        """Execute one full cycle of the Fill into Jar minigame."""
        cfg = config.get("jar_game", {})
        
        while self.state != JarState.COMPLETE:
            if self._is_aborted():
                logger.info("[JAR] Aborted")
                return False

            if self.state == JarState.INIT:
                self._do_init(vision, inp, cfg)
            elif self.state == JarState.CLICK:
                self._do_click(inp, cfg)
            elif self.state == JarState.ROTATE:
                self._do_rotate(vision, inp, cfg)
            elif self.state == JarState.VERIFY:
                self._do_verify(vision, cfg)

        return True

    def _do_init(self, vision, inp, cfg):
        """Step 1: Press E and wait for UI."""
        logger.info(">>> STEP 1: INITIALIZING (Pressing Start Key)")
        inp.press_key(cfg.get("start_key", "e"))
        
        ui_template = cfg.get("templates", {}).get("ui_active")
        ui_region = cfg.get("ui_region", [0, 0, 1920, 1080])
        
        if ui_template:
            logger.info(">>> STEP 1: WAITING FOR UI DETECTION (Short Gap)...")
            start_wait = time.time()
            while time.time() - start_wait < 0.5:
                if self._is_aborted(): return
                found, _, _ = vision.region_matches_template(tuple(ui_region), ui_template)
                if found:
                    logger.info(">>> STEP 1: UI DETECTED!")
                    self.state = JarState.CLICK
                    return
                time.sleep(0.05)
        
        logger.info(">>> STEP 1: PROCEEDING TO CLICKING.")
        self.state = JarState.CLICK

    def _do_click(self, inp, cfg):
        """Step 2: CLICKING 4 TIMES."""
        pos = cfg.get("click_pos", [960, 540])
        count = cfg.get("click_count", 4)
        
        logger.info(f">>> STEP 2: CLICKING {count} TIMES at {pos}")
        for i in range(count):
            if self._is_aborted(): return
            inp.click(pos[0], pos[1])
            inp.delay(50)
            
        logger.info(">>> STEP 2: COMPLETE.")
        self.state = JarState.ROTATE

    def _do_rotate(self, vision, inp, cfg):
        """Step 3: High-speed clockwise rotation until 5x indicator detected."""
        center = cfg.get("circle_center", [960, 540])
        radius = cfg.get("circle_radius", 100)
        # Horizontal Scrape Width based on radius
        width = radius * 2
        start_x = center[0] - radius
        end_x = center[0] + radius
        y = center[1]
        # Use an extremely fast default speed (20ms) for 20x speed
        # If config is too slow (>100ms), we override it to be fast
        cfg_speed = cfg.get("circle_speed_ms", 20)
        speed_ms = cfg_speed if cfg_speed <= 100 else 20
        
        check_tpl = cfg.get("templates", {}).get("final_check")
        check_reg = cfg.get("final_check_region", [0, 0, 1920, 1080])
        
        logger.info(f">>> STEP 3: STARTING TURBO SCRAPE ({speed_ms}ms/pass)")
        
        start_time = time.time()
        last_log_time = 0
        last_vision_time = 0
        
        # Initial move to start point
        inp.mouse_down(int(start_x), int(y))
        
        match_found = False
        while time.time() - start_time < self.MAX_ROTATE_TIMEOUT:
            if self._is_aborted(): 
                inp.mouse_up()
                return

            now = time.time()
            elapsed_ms = (now - start_time) * 1000
            
            # Calculate horizontal position (Triangle wave for left-to-right-to-left)
            # Cycle time is speed_ms for one full back-and-forth
            cycle = (elapsed_ms / speed_ms) % 2
            if cycle < 1:
                # Left to Right
                curr_x = start_x + (width * cycle)
            else:
                # Right to Left
                curr_x = end_x - (width * (cycle - 1))
            
            # High-speed movement across the horizontal line
            pyautogui.moveTo(int(curr_x), int(y))
            
            # Check vision every 10ms
            if check_tpl and (elapsed_ms - last_vision_time) > 10:
                last_vision_time = elapsed_ms
                found, conf, _ = vision.region_matches_template(tuple(check_reg), check_tpl, threshold=0.35)
                
                if elapsed_ms - last_log_time > 200:
                    logger.info(f">>> STEP 3: SCRAPING... (5x Match: {conf:.3f})")
                    last_log_time = elapsed_ms

                if found and elapsed_ms > 500:
                    logger.info(f">>> STEP 3: 5x DETECTED! Conf: {conf:.3f}. Breaking.")
                    match_found = True
                    break
            
        inp.mouse_up()
        
        if match_found:
            logger.info(">>> STEP 3: COMPLETE (Success).")
            self.state = JarState.VERIFY
        else:
            logger.error(">>> STEP 3: TIMEOUT! Could not find ADDED 5X.")
            # Safety reset if we didn't find the target
            self.state = JarState.INIT

    def _do_verify(self, vision, cfg):
        """Step 4: Wait for UI close."""
        ui_template = cfg.get("templates", {}).get("ui_active")
        ui_region = cfg.get("ui_region", [0, 0, 1920, 1080])
        
        logger.info(">>> STEP 4: VERIFYING UI CLOSURE...")
        if ui_template:
            start_wait = time.time()
            while time.time() - start_wait < 5.0:
                if self._is_aborted(): return
                found, _, _ = vision.region_matches_template(tuple(ui_region), ui_template)
                if not found:
                    logger.info(">>> STEP 4: UI CLOSED detected.")
                    break
                time.sleep(0.3)
        
        logger.info(">>> STEP 4: CYCLE COMPLETE.")
        self.state = JarState.COMPLETE

    def reset(self):
        self.state = JarState.INIT
