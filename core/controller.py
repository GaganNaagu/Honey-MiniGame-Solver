"""
Dhurandhar — Controller with threaded abort flag.
Uses threading.Event for reliable F6 stop across all modules.
"""

import time
import threading
import keyboard
import logging

logger = logging.getLogger("dhurandhar.controller")


class Controller:
    """Runs the active handler in a background thread.
    F6 sets a threading.Event that all modules check.
    """

    def __init__(self, vision, input_sim, config):
        self.vision = vision
        self.input = input_sim
        self.config = config
        self.handlers = []
        self.active_handler = None
        self.abort_event = threading.Event()
        self._run_thread = None

        # Share abort flag with input module
        self.input.set_abort_flag(self.abort_event)

    def register_handler(self, handler):
        self.handlers.append(handler)
        handler.set_abort_flag(self.abort_event)
        logger.info(f"Registered handler: {handler.name}")

    def set_active_handler(self, index):
        if 0 <= index < len(self.handlers):
            self.active_handler = self.handlers[index]

    def is_running(self):
        return self._run_thread is not None and self._run_thread.is_alive()

    def start(self, on_status=None, on_done=None):
        """Start the macro in a background thread."""
        if self.is_running():
            return

        if not self.active_handler:
            if self.handlers:
                self.active_handler = self.handlers[0]
            else:
                logger.error("No handlers registered!")
                return

        self.abort_event.clear()
        self._run_thread = threading.Thread(
            target=self._run_loop,
            args=(on_status, on_done),
            daemon=True
        )
        self._run_thread.start()

    def stop(self):
        """Signal stop via abort event."""
        self.abort_event.set()
        logger.info("Stop signal sent")

    def _run_loop(self, on_status, on_done):
        handler = self.active_handler
        logger.info(f"Running: {handler.name}")

        if on_status:
            on_status(f"Running: {handler.name}")

        while not self.abort_event.is_set():
            try:
                done = handler.run(self.vision, self.input, self.config)
                if done:
                    logger.info("Cycle complete")
                    handler.reset()
                    if on_status:
                        on_status("Cycle done, restarting...")
                else:
                    # Aborted
                    break
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
                handler.reset()
                time.sleep(2.0)

        handler.reset()
        logger.info("Stopped")

        if on_done:
            on_done()
