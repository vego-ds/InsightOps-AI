from collections.abc import AsyncIterator
from typing import Protocol

from insightops.runtime.run_context import RunContext


class RuntimeAdapter(Protocol):
    async def stream_events(self, context: RunContext) -> AsyncIterator[dict]:
        """Stream already-serialized run event payload dictionaries."""
        ...
