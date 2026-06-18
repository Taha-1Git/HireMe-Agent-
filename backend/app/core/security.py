"""Security utilities for TrueHire AI"""

from fastapi.security import HTTPBearer

security = HTTPBearer(auto_error=False)
