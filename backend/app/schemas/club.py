from pydantic import BaseModel


class ClubOut(BaseModel):
    """
    Pydantic schema for returning basic club information.
    """

    id: int
    name: str
    public_code: str | None = None
    logo: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    president: str | None = None
    secretary: str | None = None

    class Config:
        from_attributes = True