"""Tests for core types: Auto[T], Private[T], and Field class."""

from potato import Auto, Private, Domain, Field
from potato.core import AutoMarker, PrivateMarker

from typing import Annotated, get_args, get_origin


class TestAutoType:
    """Test Auto[T] marker type."""

    def test_auto_is_annotated(self) -> None:
        """Test that Auto[int] produces Annotated[int, AutoMarker]."""
        hint = Auto[int]
        assert get_origin(hint) is Annotated
        args = get_args(hint)
        assert args[0] is int
        assert args[1] is AutoMarker or isinstance(args[1], AutoMarker)

    def test_auto_in_domain(self) -> None:
        """Test Auto[T] in a domain model."""

        class User(Domain):
            id: Auto[int]
            username: str

        User.model_rebuild()
        user = User(id=1, username="test")
        assert user.id == 1
        assert user.username == "test"


class TestPrivateType:
    """Test Private[T] marker type."""

    def test_private_is_annotated(self) -> None:
        """Test that Private[str] produces Annotated[str, PrivateMarker]."""
        hint = Private[str]
        assert get_origin(hint) is Annotated
        args = get_args(hint)
        assert args[0] is str
        assert args[1] is PrivateMarker or isinstance(args[1], PrivateMarker)

    def test_private_in_domain(self) -> None:
        """Test Private[T] in a domain model."""

        class User(Domain):
            id: int
            password_hash: Private[str]

        User.model_rebuild()
        user = User(id=1, password_hash="hashed_value")
        assert user.password_hash == "hashed_value"


class TestFieldClass:
    """Test Field configuration class."""

    def test_field_with_source(self) -> None:
        """Test Field accepts source parameter."""
        from potato.types import FieldProxy

        class User(Domain):
            username: str

        field = Field(source=User.username)
        assert isinstance(field.source, FieldProxy)
        assert field.source.field_name == "username"

    def test_field_with_transform(self) -> None:
        """Test Field accepts transform parameter."""
        field = Field(transform=lambda x: x.upper())
        assert field.transform is not None
        assert field.transform("hello") == "HELLO"

    def test_field_with_visible(self) -> None:
        """Test Field accepts visible parameter."""
        field = Field(visible=lambda ctx: ctx.is_admin)
        assert field.visible is not None

    def test_field_with_all_params(self) -> None:
        """Test Field accepts all parameters together."""

        class User(Domain):
            email: str

        field = Field(
            source=User.email,
            transform=lambda x: x.lower(),
            visible=lambda ctx: True,
        )
        assert field.source is not None
        assert field.transform is not None
        assert field.visible is not None
