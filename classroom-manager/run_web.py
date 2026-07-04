"""classroom-manager 웹 서버 실행."""

from __future__ import annotations

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host="127.0.0.1",
        port=8080,
        reload=True,
    )
