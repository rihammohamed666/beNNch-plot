"""
UUID set management classes.

These are the base types for anything containing multiple UUIDs. Classes
serialize gracefully and provide the basis for set hashes.
"""

import logging
import os
from hashlib import md5
from pathlib import Path
from typing import Any, Generator, Iterable, Literal
from uuid import UUID

import git
from pydantic import BaseModel, Field, RootModel, field_serializer, field_validator

from bennch.plot.config import XDG
from bennch.plot.io import yaml

log = logging.getLogger(__name__)


class UuidSet(RootModel[frozenset[UUID]]):
    """
    Basis of all UUIDsets is explicitly a __frozenset__.

    This prevents users from uuids.add("123-321") without validation as
    UUID-type.

    >>> s = UuidSet()  # creates empty set
    >>> s.add('72aaa55c-91bd-4931-951e-b9ed9938b9ac')  # add *string*
    UuidSet(root=frozenset({UUID('72aaa55c-91bd-4931-951e-b9ed9938b9ac')}))

    Note that UuidSet being frozen means that the `add` above returns a
    *new UuidSet object*. This is different from normal `set.add()`.
    """

    # Optional: ensure defaults exist if you need them elsewhere
    root: frozenset[UUID] = Field(default_factory=frozenset)

    @field_serializer("root")
    def serialize_root(self, v: frozenset[UUID]) -> list[str]:
        """
        Serialize to sorted list of str.

        >>> ids = UuidSet(
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

    def add(self, new: str | UUID) -> "UuidSet":
        """
        Return new UuidSet object with the union of UUIDs.

        >>> ids = UuidSet(["c9d6a911-e27f-49b0-bdbf-68af3ede69be"])
        >>> ids.model_dump()
        ['c9d6a911-e27f-49b0-bdbf-68af3ede69be']
        >>> ids
        UuidSet(root=frozenset({UUID('c9d6a911-e27f-49b0-bdbf-68af3ede69be')}))
        >>> ids = ids.add("03413c4d-a67d-4794-adad-41683bae1fe6")
        >>> ids = ids.add(UUID("03413c4d-a67d-4794-adad-41683bae1fe6"))
        >>> ids.model_dump()
        ['03413c4d-a67d-4794-adad-41683bae1fe6', \
'c9d6a911-e27f-49b0-bdbf-68af3ede69be']
        """
        other = new if isinstance(new, UUID) else UUID(new)
        return UuidSet(self.root.union([other]))

    def remove(self, old: str | UUID) -> "UuidSet":
        """
        Return new UuidSet object with the difference of UUIDs.

        Note that this does not raise an error if the uuid is not in the set.

        >>> ids = UuidSet(
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
        return UuidSet(self.root.difference([other]))

    def union(self, other: Iterable[str | UUID]) -> "UuidSet":
        """
        Return new UuidSet object with the union of UUIDs.

        >>> s1 = UuidSet("03413c4d-a67d-4794-adad-41683bae1fe6")

        >>> s3 = ['c9d6a911-e27f-49b0-bdbf-68af3ede69be']
        >>> s1.union(s3).model_dump()
        ['03413c4d-a67d-4794-adad-41683bae1fe6', \
'c9d6a911-e27f-49b0-bdbf-68af3ede69be']

        As UuidSet is Iterable[UUID] itself, this also works:
        >>> s2 = UuidSet("c9d6a911-e27f-49b0-bdbf-68af3ede69be")
        >>> s1.union(s2).model_dump()
        ['03413c4d-a67d-4794-adad-41683bae1fe6', \
'c9d6a911-e27f-49b0-bdbf-68af3ede69be']
        """
        return UuidSet(self.root.union(UuidSet(frozenset(UUID(str(x)) for x in other))))

    # Mypy does not understand the difference between class iter and instance
    # iter here, so we override. Pydantic would otherwise give (name, value)
    # pairs when iterating a BaseModel-derived object.
    def __iter__(self) -> Generator[UUID, None, None]:  # type: ignore[override]
        "Yield all items of the set (not sorted)."
        yield from self.root

    def __contains__(self, uuid: str | UUID) -> bool:
        "Check if given UUID is in this set."
        return (uuid if isinstance(uuid, UUID) else UUID(uuid)) in self.root

    def __len__(self) -> int:
        "Return the total number of unique UUIDs in this set."
        return len(self.root)

    @property
    def key(self) -> str:
        """
        Return a unique identifier for this set.

        Currently this is the MD5 sum of the string of the JSON encoded
        serialization of this object.

            re-adding a uuid does not change key
        >>> ids = UuidSet([
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
        log.debug("String for key calculation: %s", self.model_dump_json().encode())
        return md5(self.model_dump_json().encode()).hexdigest()


class CommentedUuidSet(BaseModel):
    "Set of UUIDs with annotations."

    version: Literal["1"] = "1"
    uuids: UuidSet
    comment: str = ""
    creator: str = Field(default_factory=os.getlogin)

    def add(self, uuid: str | UUID) -> "CommentedUuidSet":
        """
        Add the given UUID to the uuids field.

        This is not just syntactic sugar for a direct add to self.uuids!
        When using direct access, the update will not be reflected in this
        Uuidset object, as this instance cannot know the newly created frozen
        UuidSet object.
        """
        # Note: the assignment in the following line is the main point of this
        # method.
        self.uuids = self.uuids.add(uuid)
        return self

    def extend(self, uuids: Iterable[str | UUID]) -> "CommentedUuidSet":
        """
        Add the UUIDs of the given iterable to the uuids field.

        This is not just syntactic sugar for a direct extend of self.uuids!
        When using direct access, the update will not be reflected in this
        Uuidset object, as this instance cannot know the newly created frozen
        UuidSet object.
        """
        # Note: the assignment in the following line is the main point of this
        # method.
        self.uuids = self.uuids.union(UuidSet(frozenset(UUID(str(x)) for x in uuids)))
        return self

    def remove(self, uuid: str | UUID) -> "CommentedUuidSet":
        """
        Remove the given UUID from the uuids field.

        This is not just syntactic sugar for a direct remove from self.uuids!
        When using direct access, the update will not be reflected in this
        Uuidset object, as this instance cannot know the newly created frozen
        UuidSet object.

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


class SetCache:
    """
    Manage a SetCache storage repository.

    Note that none of the methods is allowed to leak a pathname to the calling
    context. This class may well be re-implemented as database or by other
    means!

    Note that the returned handles are of type `str`. The implementation
    details of the handle are irrelevant here and *must not* matter. Do not
    make assumptions about the nature of the returned str-value. Treat it as
    opaque handle! The only definition of UuidSet keys is in the `UuidSet`
    class.
    """

    def __init__(self):
        log.debug("SetCache")
        self._path = XDG("bennch-plot/sets").data_home
        log.debug("BeNNch SetCache cache location: %s (exists: %s)", self._path, self._path.exists())
        if not (self._path / ".git").exists():
            self.reinit()

    def reinit(self):
        "Initialize a new repository."
        log.debug("creating SetCache cache: %s (exists: %s)", self._path, self._path.exists())
        self._path.mkdir(parents=True, exist_ok=True)
        log.debug("(re-)initializing git repository…")
        git.Repo.init(self._path)

    def sync(self) -> None:
        "Make sure the default remote knows everything and we're uptodate."

    def save(self, uset: UuidSet, overwrite: bool = False) -> str:
        """
        Add given set to the storage.

        Parameters
        ----------
        overwrite: bool
            re-write the given set-file into the cache. This can help when
            on-disk format of cache-files changes, or file syntax became
            corrupted.

        Returns
        -------
        str: handle of stored set.
        """
        handle = uset.key
        log.debug("adding set %s with key %s", uset, handle)
        filename = self._path_to(handle)
        if filename.exists() and not overwrite:
            log.info("set already in storage.")
        else:
            with filename.open("w", encoding="utf8") as outfile:
                # Align with UuidSet.key() to allow easy checking of file
                # consistency!
                log.debug("  writing %s", repr(uset.model_dump_json()))
                outfile.write(uset.model_dump_json())
        return handle

    def load(self, handle: str) -> UuidSet:
        "Load a UuidSet from the cache."
        filename = self._path_to(handle)
        log.debug("loading set from %s", filename)
        with filename.open("r", encoding="utf8") as infile:
            return UuidSet.model_validate(yaml.load(infile))  # actually the oposite of save()

    def __contains__(self, handle: str) -> bool:
        "Check if the given handle points to a known set."
        return self._path_to(handle).exists()

    def near_match(self, handle: str) -> list[str]:
        """
        Return possible sets similar to the given handle.

        This method may be used to implement tab-completion, or selection of
        approximate set names.
        """
        log.debug("Searching for sets with pattern %s", repr(handle))
        path = Path(str(self._path_to(handle).with_suffix("")) + "*")
        log.debug("  search pattern %s", repr(path))
        log.debug("  searching %s", path.parent)
        log.debug("  for %s", path.name)
        return list(self._handle_of(path) for path in path.parent.glob(path.name))

    def _path_to(self, handle: str) -> Path:
        "Return the correctly mapped path for the given handle."
        # For now hashes are just stored flat in a path, but this will change
        # as soon as the number of known sets increases and directories are
        # split up. Probably will also need some bad-char cleaning for
        # arbitrary handle strings.

        # when changing this definition, also fix the inverse method
        # _handle_of()!
        return self._path / f"{handle}.yaml"

    def _handle_of(self, path: Path) -> str:
        """
        Inverse of _path_to().

        >>> sc = SetCache()
        >>> sc._handle_of(sc._path_to("asdf")) == "asdf"
        True
        """
        if self._path != path.parent:
            raise ValueError("not a valid object path.")

        # currently the handle is directly used as filename...
        return path.with_suffix("").name
