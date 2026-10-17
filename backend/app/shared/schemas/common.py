from pydantic import BaseModel
from typing import TypeVar, Generic, List

T = TypeVar("T")


class PageResult(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: str | None = None


class SuccessResponse(BaseModel):
    success: bool = True
    message: str = "ok"
