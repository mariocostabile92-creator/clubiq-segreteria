from backend.app.models.user import User
from backend.app.routers.admin import ADMIN_ROLES, is_platform_admin
from backend.app.routers.athletes import PLAN_ATHLETE_LIMITS
from backend.app.schemas.communication import CommunicationCreate


def test_owner_is_not_platform_admin():
    assert "owner" not in ADMIN_ROLES
    assert "super_admin" in ADMIN_ROLES


def test_role_admin_is_platform_admin():
    assert is_platform_admin(User(email="admin@example.com", role="super_admin"))


def test_plan_athlete_limits():
    assert PLAN_ATHLETE_LIMITS["free"] == 5
    assert PLAN_ATHLETE_LIMITS["pro"] == 80
    assert PLAN_ATHLETE_LIMITS["premium"] is None


def test_communication_schema_defaults():
    payload = CommunicationCreate(message="Promemoria quota")
    assert payload.channel == "whatsapp"
    assert payload.type == "WhatsApp"
    assert payload.direction == "outbound"
    assert payload.status == "opened"
