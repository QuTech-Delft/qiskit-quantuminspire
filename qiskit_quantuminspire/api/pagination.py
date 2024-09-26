from typing import Any, Awaitable, Callable, Generic, List, Optional, TypeVar, Union, cast

from pydantic import BaseModel, Field
from typing_extensions import Annotated

PageType = TypeVar("PageType")
ItemType = TypeVar("ItemType")


class PageInterface(BaseModel, Generic[ItemType]):
    """The page models in the generated API client don't inherit from a common base class, so we have to trick the
    typing system a bit with this fake base class."""

    items: List[ItemType]
    total: Optional[Annotated[int, Field(strict=True, ge=0)]]
    page: Optional[Annotated[int, Field(strict=True, ge=1)]]
    size: Optional[Annotated[int, Field(strict=True, ge=1)]]
    pages: Optional[Annotated[int, Field(strict=True, ge=0)]] = None


class PageReader(Generic[PageType, ItemType]):
    """Helper class for reading fastapi-pagination style pages returned by the compute_api_client."""

    async def get_all(self, api_call: Callable[..., Awaitable[PageType]], **kwargs: Any) -> List[ItemType]:
        """Get all items from an API call that supports paging."""
        items: List[ItemType] = []
        page = 1

        while True:
            response = cast(PageInterface[ItemType], await api_call(page=page, **kwargs))

            items.extend(response.items)
            page += 1
            if response.pages is None or page > response.pages:
                break
        return items

    async def get_single(self, api_call: Callable[..., Awaitable[PageType]], **kwargs: Any) -> Union[ItemType, None]:
        """Get a single item from an API call that supports paging."""
        response = cast(PageInterface[ItemType], await api_call(**kwargs))
        if len(response.items) > 1:
            raise RuntimeError(f"Response contains more than one item -> {kwargs}.")

        return response.items[0] if response.items else None
