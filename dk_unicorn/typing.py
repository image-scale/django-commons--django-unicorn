import typing
from collections.abc import Iterator
from typing import TYPE_CHECKING, Generic, TypeVar

from django.db.models import Model, QuerySet

M_co = TypeVar("M_co", bound=Model, covariant=True)

if TYPE_CHECKING:
    QuerySetType = QuerySet[M_co] | list[M_co] | None
else:
    class QuerySetType(Generic[M_co], QuerySet):
        def __iter__(self) -> Iterator[M_co]: ...
