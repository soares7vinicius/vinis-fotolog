from pydantic import BaseModel, Field


class Pagination(BaseModel):
    page: int = Field(
        default=1,
        ge=1,
        description="The page number to retrieve, starting from 1.",
    )
    size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="The number of items per page, must be between 1 and 100.",
    )
    total: int = Field(
        default=0,
        ge=0,
        description="The total number of items available across all pages.",
    )


class PaginatedResponse(BaseModel):
    items: list[BaseModel] = Field(
        default_factory=list,
        description="The list of items for the current page.",
    )
    pagination: Pagination = Field(
        default_factory=Pagination,
        description="Pagination information including page number, size, and total items.",
    )
