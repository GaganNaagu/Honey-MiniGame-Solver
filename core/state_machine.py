"""
Dhurandhar — Lightweight state machine engine.
Handlers define their own states as Enums and register handler functions.
"""

import logging

logger = logging.getLogger("dhurandhar.state")


class StateMachine:
    """Generic state machine for minigame handlers.
    
    Usage:
        class MyStates(Enum):
            INIT = auto()
            WORK = auto()
            DONE = auto()
        
        sm = StateMachine(MyStates.INIT)
        sm.register(MyStates.INIT, my_init_fn)
        sm.register(MyStates.WORK, my_work_fn)
        
        while sm.state != MyStates.DONE:
            sm.tick(context)
    """

    def __init__(self, initial_state):
        self.state = initial_state
        self._handlers = {}

    def register(self, state, handler_fn):
        """Register a function to run when in a given state.
        
        The function receives (context) and should call sm.transition()
        to move to the next state.
        """
        self._handlers[state] = handler_fn

    def transition(self, new_state):
        """Explicitly transition to a new state."""
        old = self.state
        self.state = new_state
        logger.info(f"[STATE] {old.name} → {new_state.name}")

    def tick(self, context):
        """Execute the handler for the current state."""
        handler = self._handlers.get(self.state)
        if handler:
            return handler(context)
        else:
            logger.warning(f"No handler registered for state: {self.state.name}")
            return None
