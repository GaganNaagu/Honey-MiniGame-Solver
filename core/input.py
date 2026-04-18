"""
Dhurandhar — Humanized input simulation layer.
All actions include randomized timing, Bezier cursor paths, and micro-jitter.
"""

import pyautogui
import time
import random
import math
import logging

logger = logging.getLogger("dhurandhar.input")

# Keep failsafe on (move mouse to corner to abort)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0  # We handle delays ourselves


class Input:
    """Humanized mouse and keyboard simulation."""

    def __init__(self, jitter=5, delay_variance=0.2):
        self.jitter = jitter
        self.delay_variance = delay_variance
        self._abort_flag = None  # Set by controller to a threading.Event

    def set_abort_flag(self, flag):
        """Set the abort flag (threading.Event) checked during long operations."""
        self._abort_flag = flag

    def _is_aborted(self):
        return self._abort_flag and self._abort_flag.is_set()

    def _jitter_pos(self, x, y):
        return (
            x + random.randint(-self.jitter, self.jitter),
            y + random.randint(-self.jitter, self.jitter)
        )

    def delay(self, base_ms):
        """Sleep with ±variance randomization."""
        variance = base_ms * self.delay_variance
        actual = base_ms + random.uniform(-variance, variance)
        time.sleep(max(0.01, actual / 1000.0))

    def _bezier_points(self, start, end, steps=20):
        sx, sy = start
        ex, ey = end
        dist = math.hypot(ex - sx, ey - sy)
        offset = max(20, dist * 0.3)
        cx = (sx + ex) / 2 + random.uniform(-offset, offset)
        cy = (sy + ey) / 2 + random.uniform(-offset, offset)

        points = []
        for i in range(steps + 1):
            t = i / steps
            x = (1 - t) ** 2 * sx + 2 * (1 - t) * t * cx + t ** 2 * ex
            y = (1 - t) ** 2 * sy + 2 * (1 - t) * t * cy + t ** 2 * ey
            points.append((int(x), int(y)))
        return points

    # ── Keyboard ──────────────────────────────────────────

    def press_key(self, key, hold_ms=50):
        logger.info(f"[INPUT] press_key({key})")
        import keyboard
        keyboard.press(key)
        self.delay(hold_ms)
        keyboard.release(key)
        self.delay(50)

    # ── Mouse ─────────────────────────────────────────────

    def smooth_move(self, x, y, duration_ms=50):
        current = pyautogui.position()
        points = self._bezier_points(current, (x, y))
        step_delay = (duration_ms / 1000.0) / max(len(points), 1)
        for px, py in points:
            if self._is_aborted():
                return
            pyautogui.moveTo(px, py)
            self._exact_sleep(step_delay)

    def click(self, x, y, delay_after=20):
        jx, jy = self._jitter_pos(x, y)
        logger.info(f"[INPUT] click({jx}, {jy})")
        self.smooth_move(jx, jy, duration_ms=50)
        pyautogui.click(jx, jy)
        self.delay(delay_after)

    def mouse_down(self, x=None, y=None):
        if x is not None and y is not None:
            jx, jy = self._jitter_pos(x, y)
            self.smooth_move(jx, jy, duration_ms=50)
            pyautogui.mouseDown(jx, jy)
        else:
            pyautogui.mouseDown()
        logger.info("[INPUT] mouse_down")

    def mouse_up(self):
        pyautogui.mouseUp()
        logger.info("[INPUT] mouse_up")

    def drag(self, start, end, duration_ms=100):
        sx, sy = self._jitter_pos(*start)
        ex, ey = self._jitter_pos(*end)
        logger.info(f"[INPUT] drag({sx},{sy} -> {ex},{ey})")
        self.smooth_move(sx, sy, duration_ms=50)
        pyautogui.mouseDown()
        self.delay(20)

        points = self._bezier_points((sx, sy), (ex, ey))
        step_delay = (duration_ms / 1000.0) / max(len(points), 1)
        for px, py in points:
            if self._is_aborted():
                pyautogui.mouseUp()
                return
            pyautogui.moveTo(px, py)
            self._exact_sleep(step_delay)

        self.delay(20)
        pyautogui.mouseUp()

    def _exact_sleep(self, duration_sec):
        """Busy-wait for precise sub-15ms delays on Windows."""
        if duration_sec <= 0:
            return
        end_time = time.perf_counter() + duration_sec
        while time.perf_counter() < end_time:
            pass

    def sweep_horizontal(self, region, speed_ms=400):
        """Sweep cursor left-to-right then right-to-left across a region."""
        x, y, w, h = region
        # Use exact vertical center, NO up/down movement
        sweep_y = y + (h // 2)
        left_x = x + 10
        right_x = x + w - 10
        
        # Calculate steps dynamically to ensure smooth but accurate movement
        # If speed_ms is very low, we do fewer steps to avoid sleep overhead
        steps = max(5, min(30, int(w / 20))) 
        step_delay = (speed_ms / 1000.0) / steps

        # Left to right
        for i in range(steps + 1):
            if self._is_aborted():
                return False
            px = left_x + (right_x - left_x) * i / steps
            py = sweep_y
            pyautogui.moveTo(int(px), int(py))
            self._exact_sleep(step_delay)

        # Right to left
        for i in range(steps + 1):
            if self._is_aborted():
                return False
            px = right_x - (right_x - left_x) * i / steps
            py = sweep_y
            pyautogui.moveTo(int(px), int(py))
            self._exact_sleep(step_delay)

        return True
