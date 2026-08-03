from typing import Dict, Any
from uuid import UUID


class SessionStore:
    """Very small in-memory session store for demo purposes.

    In future this can be replaced by Redis or a DB and moved to a separate container.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}

    def ensure(self, session_id: UUID) -> Dict[str, Any]:
        key = str(session_id)
        if key not in self._store:
            self._store[key] = {"messages": []}
        return self._store[key]

    def append_message(self, session_id: UUID, role: str, content: str) -> None:
        s = self.ensure(session_id)
        s["messages"].append({"role": role, "content": content})

    def get(self, session_id: UUID) -> Dict[str, Any] | None:
        return self._store.get(str(session_id))


# singleton for simple use
STORE = SessionStore()
