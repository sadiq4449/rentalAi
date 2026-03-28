from pydantic import BaseModel


class FavoriteOut(BaseModel):
    id: str
    user_id: str
    property_id: str
