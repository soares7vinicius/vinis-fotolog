from typing import Optional

from pydantic import BaseModel, Field
from src.models.api_models.pagination import Pagination


class GetPostsPayload(BaseModel):
    user_id: Optional[int] = Field(
        default=None,
        description="Filter posts by user ID. If provided, only posts by this user will be returned.",
    )
    pagination: Pagination = Field(
        default=Pagination(),
        description="Pagination parameters to control the number of posts returned and the page number.",
    )
