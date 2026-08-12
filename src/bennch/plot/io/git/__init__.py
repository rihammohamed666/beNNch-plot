"UUID set management modules."

import logging
import os
from hashlib import md5
from typing import Any, Generator, Iterable, Literal
from uuid import UUID

import git
from pydantic import BaseModel, Field, RootModel, field_serializer, field_validator

from bennch.plot.config import XDG

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class SortedUUIDs(RootModel[frozenset[UUID]]):
    """
    Basis of all UUIDsets is explicitly a __frozenset__.

    This prevents users from uuids.add("123-321") without validation as
    UUID-type.

    >>> s = SortedUUIDs()  # creates empty set
    >>> s.add('72aaa55c-91bd-4931-951e-b9ed9938b9ac')  # add *string*
    SortedUUIDs(root=frozenset({UUID('72aaa55c-91bd-4931-951e-b9ed9938b9ac')}))

    Note that SortedUUIDs being frozen means that the `add` above returns a
    *new SortedUUIDs object*. This is different from normal `set.add()`.
    """

    # Optional: ensure defaults exist if you need them elsewhere
    root: frozenset[UUID] = Field(default_factory=frozenset)

    @field_serializer("root")
    def serialize_root(self, v: frozenset[UUID]) -> list[str]:
        """
        Serialize to sorted list of str.

        >>> ids = SortedUUIDs(
        ...     [
        ...         "f288c96a-1b75-44bd-98de-16dea35c3a9c",
        ...         "c9d6a911-e27f-49b0-bdbf-68af3ede69be",
        ...     ]
        ... )
        >>> ids.model_dump()
        ['c9d6a911-e27f-49b0-bdbf-68af3ede69be', \
'f288c96a-1b75-44bd-98de-16dea35c3a9c']
        """
        return sorted(str(x) for x in v)

    @field_validator("root", mode="before")
    @classmethod
    def validate_root(cls, v: Any) -> frozenset[UUID]:
        "Create a vaild frozenset from given value."
        if v is None:
            return frozenset()
        if isinstance(v, (list, tuple, set, frozenset)):
            return frozenset(UUID(str(x)) for x in v)
        if isinstance(v, (str, UUID)):
            return frozenset({UUID(str(v))})
        raise TypeError("root must be an iterable of UUIDs/UUID strings, or a single UUID/string.")

    # pylint complains about the named arguments. As the type is 'Any' we want
    # to keep the additional information instead of replacing the unused names
    # by "_". Hence we disable 'unused-argument' check for this line.
    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: Any, handler: Any  # pylint: disable=unused-argument
    ) -> dict[str, Any]:
        "Emit schema as array<string> for the *root* value."
        return {
            "type": "array",
            "items": {"type": "string"},
        }

    def add(self, new: str | UUID) -> "SortedUUIDs":
        """
        Return new SortedUUIDs object with the union of UUIDs.

        >>> ids = SortedUUIDs(["c9d6a911-e27f-49b0-bdbf-68af3ede69be"])
        >>> ids.model_dump()
        ['c9d6a911-e27f-49b0-bdbf-68af3ede69be']
        >>> ids
        SortedUUIDs(root=frozenset({UUID('c9d6a911-e27f-49b0-bdbf-68af3ede69be')}))
        >>> ids = ids.add("03413c4d-a67d-4794-adad-41683bae1fe6")
        >>> ids = ids.add(UUID("03413c4d-a67d-4794-adad-41683bae1fe6"))
        >>> ids.model_dump()
        ['03413c4d-a67d-4794-adad-41683bae1fe6', \
'c9d6a911-e27f-49b0-bdbf-68af3ede69be']
        """
        other = new if isinstance(new, UUID) else UUID(new)
        return SortedUUIDs(self.root.union([other]))

    def remove(self, old: str | UUID) -> "SortedUUIDs":
        """
        Return new SortedUUIDs object with the difference of UUIDs.

        Note that this does not raise an error if the uuid is not in the set.

        >>> ids = SortedUUIDs(
        ...     [
        ...         "c9d6a911-e27f-49b0-bdbf-68af3ede69be",
        ...         "03413c4d-a67d-4794-adad-41683bae1fe6",
        ...     ]
        ... )
        >>> ids.model_dump()
        ['03413c4d-a67d-4794-adad-41683bae1fe6', \
'c9d6a911-e27f-49b0-bdbf-68af3ede69be']
        >>> ids = ids.remove("03413c4d-a67d-4794-adad-41683bae1fe6")
        >>> ids = ids.remove(UUID("03413c4d-a67d-4794-adad-41683bae1fe6"))
        >>> ids.model_dump()
        ['c9d6a911-e27f-49b0-bdbf-68af3ede69be']
        """
        other = old if isinstance(old, UUID) else UUID(old)
        return SortedUUIDs(self.root.difference([other]))

    def union(self, other: Iterable[str | UUID]) -> "SortedUUIDs":
        """
        Return new SortedUUIDs object with the union of UUIDs.

        >>> s1 = SortedUUIDs("03413c4d-a67d-4794-adad-41683bae1fe6")

        >>> s3 = ['c9d6a911-e27f-49b0-bdbf-68af3ede69be']
        >>> s1.union(s3).model_dump()
        ['03413c4d-a67d-4794-adad-41683bae1fe6', \
'c9d6a911-e27f-49b0-bdbf-68af3ede69be']

        As SortedUUIDs is Iterable[UUID] itself, this also works:
        >>> s2 = SortedUUIDs("c9d6a911-e27f-49b0-bdbf-68af3ede69be")
        >>> s1.union(s2).model_dump()
        ['03413c4d-a67d-4794-adad-41683bae1fe6', \
'c9d6a911-e27f-49b0-bdbf-68af3ede69be']
        """
        return SortedUUIDs(self.root.union(SortedUUIDs(frozenset(UUID(str(x)) for x in other))))

    # Mypy does not understand the difference between class iter and instance
    # iter here, so we override. Pydantic would otherwise give (name, value)
    # pairs when iterating a BaseModel-derived object.
    def __iter__(self) -> Generator[UUID, None, None]:  # type: ignore[override]
        "Yield all items of the set (not sorted)."
        yield from self.root

    def __contains__(self, uuid: str | UUID) -> bool:
        "Check if given UUID is in this set."
        return (uuid if isinstance(uuid, UUID) else UUID(uuid)) in self.root

    @property
    def key(self) -> str:
        """
        Return a unique identifier for this set.

        Currently this is the MD5 sum of the string of the JSON encoded
        serialization of this object.

            re-adding a uuid does not change key
        >>> ids = SortedUUIDs([
        ...         "c9d6a911-e27f-49b0-bdbf-68af3ede69be",
        ...         "03413c4d-a67d-4794-adad-41683bae1fe6"
        ... ])
        >>> ids.key
        '625b6ae2532cf6573be880cee5e05af8'
        >>> ids = ids.remove(UUID("03413c4d-a67d-4794-adad-41683bae1fe6"))
        >>> ids = ids.add("03413c4d-a67d-4794-adad-41683bae1fe6")
        >>> ids = ids.add("c9d6a911-e27f-49b0-bdbf-68af3ede69be")
        >>> ids.key  # should be same as above
        '625b6ae2532cf6573be880cee5e05af8'

        """
        return md5(self.model_dump_json().encode()).hexdigest()


class UuidSet(BaseModel):
    "Set of UUIDs with annotations."

    version: Literal["1"] = "1"
    uuids: SortedUUIDs
    comment: str = ""
    creator: str = Field(default_factory=os.getlogin)

    def add(self, uuid: str | UUID) -> "UuidSet":
        """
        Add the given UUID to the uuids field.

        This is not just syntactic sugar for a direct add to self.uuids!
        When using direct access, the update will not be reflected in this
        Uuidset object, as this instance cannot know the newly created frozen
        SortedUUIDs object.
        """
        # Note: the assignment in the following line is the main point of this
        # method.
        self.uuids = self.uuids.add(uuid)
        return self

    def extend(self, uuids: Iterable[str | UUID]) -> "UuidSet":
        """
        Add the UUIDs of the given iterable to the uuids field.

        This is not just syntactic sugar for a direct extend of self.uuids!
        When using direct access, the update will not be reflected in this
        Uuidset object, as this instance cannot know the newly created frozen
        SortedUUIDs object.
        """
        # Note: the assignment in the following line is the main point of this
        # method.
        self.uuids = self.uuids.union(SortedUUIDs(frozenset(UUID(str(x)) for x in uuids)))
        return self

    def remove(self, uuid: str | UUID) -> "UuidSet":
        """
        Remove the given UUID from the uuids field.

        This is not just syntactic sugar for a direct remove from self.uuids!
        When using direct access, the update will not be reflected in this
        Uuidset object, as this instance cannot know the newly created frozen
        SortedUUIDs object.

        Raises
        ------
        KeyError
            If the given UUID is not part of the set.
        """
        if uuid not in self.uuids:
            raise KeyError(f"UUID {uuid} not in uuidset")
        # Note: the assignment in the following line is the main point of this
        # method.
        self.uuids = self.uuids.remove(uuid)
        return self


class SetsData:
    "Manage a SetsData storage repository."

    def __init__(self):
        log.debug("SetsData")
        self._path = XDG("bennch-plot/sets").data_home
        log.debug("BeNNch SetsData cache location: %s (exists: %s)", self._path, self._path.exists())

    def init(self):
        "Initialize a new repository."
        log.debug("creating SetsData cache: %s (exists: %s)", self._path, self._path.exists())
        self._path.mkdir(parents=True, exist_ok=True)
        log.debug("(re-)initializing git repository…")
        git.Repo.init(self._path)

    def sync(self) -> None:
        "Make sure the default remote knows everything and we're uptodate."

    def add(self, uset: UuidSet) -> None:
        "Add given set to the storage."
        log.debug("adding set %s with key %s", uset, uset.uuids.key)
