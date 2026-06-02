"""
Expose APIRouters for easy import in main.py.

Instead of importing the module and referencing `.router`, this file
re-exports the router instances directly. This avoids attribute errors
when including routers in the FastAPI application.
"""

from .auth import router as auth
from .clubs import router as clubs
from .athletes import router as athletes
from .payments import router as payments
from .certificates import router as certificates
from .dashboard import router as dashboard