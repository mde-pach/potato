from typing import Annotated, TypeVar, get_type_hints, get_origin, get_args, TypeAlias

class SystemMarker:
    pass

T = TypeVar("T")
System: TypeAlias = Annotated[T, SystemMarker]

class User:
    id: System[int]
    name: str

hints = get_type_hints(User, include_extras=True)
print(f"Hints: {hints}")
print(f"id type: {hints['id']}")
print(f"Origin of id: {get_origin(hints['id'])}")
print(f"Args of id: {get_args(hints['id'])}")

# Check if it matches Annotated[int, SystemMarker]
expected_origin = Annotated
print(f"Matches Annotated? {get_origin(hints['id']) is Annotated}")
