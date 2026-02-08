"""Tests for error messages with hints."""

import pytest

from potato import Domain, ViewDTO, Field


class TestErrorMessages:
    """Test that errors include helpful hints."""

    def test_cross_domain_error_includes_aggregate_hint(self) -> None:
        """Test that cross-domain reference error includes Aggregate hint."""

        class User(Domain):
            id: int
            username: str

        class Order(Domain):
            id: int
            amount: float

        with pytest.raises(TypeError, match="Hint"):
            class UserView(ViewDTO[User]):
                username: str
                order_id: int = Field(source=Order.id)

    def test_invalid_field_reference_error(self) -> None:
        """Test that invalid field reference raises AttributeError."""

        class User(Domain):
            name: str

        with pytest.raises(AttributeError):
            class UserView(ViewDTO[User]):
                name: str = Field(source=User.nonexistent)

    def test_private_field_error_includes_hint(self) -> None:
        """Test that Private field error includes hint."""
        from potato import Private

        class User(Domain):
            id: int
            password: Private[str]

        User.model_rebuild()

        with pytest.raises(TypeError, match="Hint"):
            class UserView(ViewDTO[User]):
                id: int
                password: str
