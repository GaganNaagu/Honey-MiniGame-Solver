"""
Dhurandhar — Vision system for screen capture and template matching.
Uses mss for fast region captures and opencv for template/pixel analysis.
"""

import cv2
import numpy as np
import mss
import time
import logging
from core.utils import resolve_template_path

logger = logging.getLogger("dhurandhar.vision")


class Vision:
    """Screen capture and visual detection engine.
    
    All captures are region-based (never full screen) for performance.
    Templates are cached after first load.
    """

    def __init__(self):
        self._template_cache = {}

    def capture_region(self, region):
        """Capture a screen region.
        
        Args:
            region: tuple (x, y, w, h) — top-left corner + dimensions
            
        Returns:
            numpy array (BGR format)
        """
        x, y, w, h = region
        monitor = {"left": x, "top": y, "width": w, "height": h}
        
        # Instantiate mss locally to avoid threading issues with DC handles
        with mss.mss() as sct:
            img = np.array(sct.grab(monitor))
            
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def load_template(self, path):
        """Load and cache a template image."""
        resolved_path = resolve_template_path(path)
        if resolved_path not in self._template_cache:
            tmpl = cv2.imread(resolved_path)
            if tmpl is None:
                raise FileNotFoundError(f"Template not found: {resolved_path}")
            self._template_cache[resolved_path] = tmpl
            logger.debug(f"Loaded template: {resolved_path}")
        return self._template_cache[resolved_path]

    def match_template(self, frame, template_path, threshold=0.8):
        """Check if a template exists in a frame.
        
        Args:
            frame: numpy array (BGR)
            template_path: path to template image
            threshold: minimum confidence (0.0 - 1.0)
            
        Returns:
            (found: bool, confidence: float, location: tuple)
        """
        template = self.load_template(template_path)

        # Handle template larger than frame
        if (template.shape[0] > frame.shape[0] or
                template.shape[1] > frame.shape[1]):
            logger.warning("Template larger than capture region — skipping match")
            return False, 0.0, (0, 0)

        result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        found = max_val >= threshold
        if found:
            logger.debug(f"Template match: {template_path} conf={max_val:.2f} at {max_loc}")
        return found, max_val, max_loc

    def wait_for_template(self, template_path, region, timeout=10.0,
                          threshold=0.8, interval=0.1):
        """Block until a template appears in a region or timeout.
        
        This is a VISION GATE — macro steps call this to wait for visual confirmation.
        
        Args:
            template_path: path to template image
            region: (x, y, w, h) to capture
            timeout: max seconds to wait
            threshold: match confidence threshold
            interval: seconds between checks
            
        Returns:
            (found: bool, location: tuple or None)
        """
        start = time.time()
        while time.time() - start < timeout:
            frame = self.capture_region(region)
            found, confidence, loc = self.match_template(frame, template_path, threshold)
            if found:
                logger.info(f"[VISION GATE] Template found: {template_path} ({confidence:.2f})")
                return True, loc
            time.sleep(interval)

        logger.warning(f"[VISION GATE] Timeout ({timeout}s) waiting for: {template_path}")
        return False, None

    def check_pixel_color(self, x, y, expected_rgb, tolerance=30):
        """Check if a pixel matches an expected color.
        
        Args:
            x, y: screen coordinates
            expected_rgb: (R, G, B) tuple
            tolerance: max per-channel deviation
            
        Returns:
            bool
        """
        frame = self.capture_region((x, y, 1, 1))
        actual_bgr = frame[0, 0]
        actual_rgb = (int(actual_bgr[2]), int(actual_bgr[1]), int(actual_bgr[0]))
        match = all(abs(a - e) <= tolerance for a, e in zip(actual_rgb, expected_rgb))
        logger.debug(f"Pixel ({x},{y}): expected={expected_rgb} actual={actual_rgb} match={match}")
        return match

    def region_changed(self, region, reference, threshold=0.05):
        """Check if a region looks different from a reference snapshot.
        
        Used as a vision gate to detect texture changes (e.g., dirty → clean honey).
        
        Args:
            region: (x, y, w, h) to capture now
            reference: numpy array — the "before" snapshot
            threshold: minimum change ratio to count as "changed"
            
        Returns:
            bool
        """
        current = self.capture_region(region)
        if current.shape != reference.shape:
            reference = cv2.resize(reference, (current.shape[1], current.shape[0]))
        diff = cv2.absdiff(current, reference)
        change_ratio = np.mean(diff) / 255.0
        changed = change_ratio > threshold
        logger.debug(f"Region change: {change_ratio:.4f} (threshold={threshold}) → {'CHANGED' if changed else 'same'}")
        return changed

    def region_matches_template(self, region, template_path, threshold=0.8):
        """Capture a region and check if it matches a template.
        
        Convenience wrapper combining capture + match.
        """
        frame = self.capture_region(region)
        return self.match_template(frame, template_path, threshold)

    def clear_cache(self):
        """Clear the template cache (useful after setup wizard updates templates)."""
        self._template_cache.clear()
        logger.info("Template cache cleared")
