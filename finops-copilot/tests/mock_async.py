# Compatibility module for Python 3.7 (which doesn't have AsyncMock)
import asyncio
from unittest.mock import MagicMock

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

    def __await__(self):
        return self().__await__()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass