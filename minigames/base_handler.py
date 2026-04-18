"""
Dhurandhar — Base handler interface for minigame macros.
"""

from abc import ABC, abstractmethod


class BaseHandler(ABC):
    """Abstract base class for all minigame handlers.
    
    Each handler is a self-contained macro for one minigame.
    Subclasses define the scripted sequence + vision gates.
    """

    def __init__(self, name):
        self.name = name
        self._abort_flag = None

    def set_abort_flag(self, flag):
        """Used by Controller to signal stops."""
        self._abort_flag = flag

    def _is_aborted(self):
        """Check if stop signal was sent."""
        return self._abort_flag and self._abort_flag.is_set()

    @abstractmethod
    def detect(self, frame):
        """Return True if this minigame is currently active on screen.
        
        Used for future auto-detection. For now, handlers are selected manually.
        """
        pass

    @abstractmethod
    def run(self, vision, input_sim, config):
        """Execute one full cycle of the minigame macro.
        
        Args:
            vision: Vision instance for screen checks
            input_sim: Input instance for mouse/keyboard
            config: dict with handler-specific settings
            
        Returns:
            True when one complete cycle is done, False if interrupted.
        """
        pass

    @abstractmethod
    def reset(self):
        """Reset internal state for a fresh cycle."""
        pass
