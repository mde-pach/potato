"""Tests for edge cases and error handling across all components."""

from __future__ import annotations

from typing import Type

import pytest
from pydantic import ValidationError

from potato.domain import Domain
from potato.domain.aggregates import Aggregate
from potato.dto import BuildDTO, ViewDTO

from ..fixtures.domains import Price, Product, User


# =============================================================================
# Edge Case Test Classes
# =============================================================================


class EmptyDomain(Domain):
    """Domain with no fields."""
    pass


class SingleFieldDomain(Domain):
    """Domain with just one field."""
    value: str


class OptionalOnlyDomain(Domain):
    """Domain with only optional fields."""
    optional1: str | None = None
    optional2: int | None = None
    optional3: list[str] = []


# =============================================================================
# Test Edge Cases for Domain
# =============================================================================


class TestDomainEdgeCases:
    """Test edge cases for Domain models."""

    def test_empty_domain(self) -> None:
        """Test creating domain with no fields."""
        domain = EmptyDomain()
        assert isinstance(domain, EmptyDomain)

    def test_single_field_domain(self) -> None:
        """Test domain with single field."""
        domain = SingleFieldDomain(value="test")
        assert domain.value == "test"

    def test_optional_only_domain_with_no_args(self) -> None:
        """Test domain with only optional fields and no arguments."""
        domain = OptionalOnlyDomain()
        assert domain.optional1 is None
        assert domain.optional2 is None
        assert domain.optional3 == []

    def test_optional_only_domain_with_some_args(self) -> None:
        """Test domain with only optional fields and some arguments."""
        domain = OptionalOnlyDomain(optional1="test", optional3=["a", "b"])
        assert domain.optional1 == "test"
        assert domain.optional2 is None
        assert domain.optional3 == ["a", "b"]

    def test_very_long_field_values(self, user_class: Type[User]) -> None:
        """Test domain with very long field values."""
        long_value = "x" * 10000
        user = user_class(id=1, username=long_value, email=long_value)
        assert len(user.username) == 10000
        assert len(user.email) == 10000

    def test_special_characters_in_all_fields(self, user_class: Type[User]) -> None:
        """Test domain with special characters in all string fields."""
        user = user_class(
            id=1,
            username="!@#$%^&*()_+-=[]{}|;:',.<>?/~`",
            email="test+tag@sub-domain.example.co.uk",
            tutor="<script>alert('xss')</script>",
        )
        assert "!@#$" in user.username
        assert "+" in user.email
        assert user.tutor is not None
        assert "<script>" in user.tutor

    def test_zero_and_negative_numbers(self, price_class: Type[Price]) -> None:
        """Test domain with zero and negative numbers."""
        price1 = price_class(amount=0, currency="USD")
        assert price1.amount == 0

        price2 = price_class(amount=-100, currency="USD")
        assert price2.amount == -100

    def test_empty_lists(self, user_class: Type[User]) -> None:
        """Test domain with explicitly empty lists."""
        user = user_class(id=1, username="test", email="test@example.com", friends=[])
        assert user.friends == []
        assert len(user.friends) == 0


# =============================================================================
# Test Edge Cases for ViewDTO
# =============================================================================


class MinimalView(ViewDTO[User]):
    """ViewDTO with just one field."""
    id: int


class EmptyProductView(ViewDTO[Product]):
    """ViewDTO that maps no fields from product."""
    pass


class TestViewDTOEdgeCases:
    """Test edge cases for ViewDTO."""

    def test_minimal_view_with_one_field(self, simple_user: User) -> None:
        """Test ViewDTO with just one field."""
        view = MinimalView.from_domain(simple_user)
        assert view.id == 1
        assert not hasattr(view, "username")
        assert not hasattr(view, "email")

    def test_view_from_domain_with_none_values(self, user_class: Type[User]) -> None:
        """Test ViewDTO from domain with None values."""
        user = user_class(id=1, username="test", email="test@example.com", tutor=None)

        class UserViewWithTutor(ViewDTO[User]):
            id: int
            username: str
            tutor: str | None

        view = UserViewWithTutor.from_domain(user)
        assert view.tutor is None

    def test_view_from_domain_with_empty_list(self, user_class: Type[User]) -> None:
        """Test ViewDTO from domain with empty list."""
        user = user_class(id=1, username="test", email="test@example.com", friends=[])

        class UserViewWithFriends(ViewDTO[User]):
            id: int
            friends: list[str]

        view = UserViewWithFriends.from_domain(user)
        assert view.friends == []

    def test_view_with_very_long_strings(self, user_class: Type[User]) -> None:
        """Test ViewDTO with very long string values."""
        long_value = "y" * 10000
        user = user_class(id=1, username=long_value, email="test@example.com")

        class SimpleView(ViewDTO[User]):
            username: str

        view = SimpleView.from_domain(user)
        assert len(view.username) == 10000


# =============================================================================
# Test Edge Cases for BuildDTO
# =============================================================================


class MinimalBuildDTO(BuildDTO[User]):
    """BuildDTO with just one field."""
    email: str


class TestBuildDTOEdgeCases:
    """Test edge cases for BuildDTO."""

    def test_minimal_build_dto(self) -> None:
        """Test BuildDTO with just one field."""
        dto = MinimalBuildDTO(email="test@example.com")
        assert dto.email == "test@example.com"

    def test_build_dto_with_none_values(self) -> None:
        """Test BuildDTO with None values."""

        class BuildWithOptional(BuildDTO[User]):
            username: str
            email: str
            tutor: str | None = None

        dto = BuildWithOptional(username="test", email="test@example.com", tutor=None)
        assert dto.tutor is None

    def test_build_dto_with_empty_list(self) -> None:
        """Test BuildDTO with empty list."""

        class BuildWithList(BuildDTO[User]):
            username: str
            email: str
            friends: list[str] = []

        dto = BuildWithList(username="test", email="test@example.com", friends=[])
        assert dto.friends == []

    def test_build_dto_type_coercion(self) -> None:
        """Test BuildDTO with type coercion."""

        class BuildWithCoercion(BuildDTO[User]):
            username: str
            email: str

        dto = BuildWithCoercion(username="test", email="test@example.com")
        assert isinstance(dto.username, str)


# =============================================================================
# Test Edge Cases for Aggregates
# =============================================================================


class MinimalAggregate(Aggregate):
    """Aggregate with just one domain."""
    user: User


class TestAggregateEdgeCases:
    """Test edge cases for Aggregate domains."""

    def test_aggregate_with_one_domain(self, simple_user: User) -> None:
        """Test aggregate with just one domain."""
        agg = MinimalAggregate(user=simple_user)
        assert agg.user.id == 1

    def test_aggregate_with_none_in_optional_domain_field(
        self, simple_user: User, simple_product: Product
    ) -> None:
        """Test aggregate where nested domain has None values."""

        class AggregateWithOptional(Aggregate):
            user: User
            product: Product

        user_with_none = User(
            id=1, username="test", email="test@example.com", tutor=None
        )
        agg = AggregateWithOptional(user=user_with_none, product=simple_product)
        assert agg.user.tutor is None


# =============================================================================
# Test Error Handling and Validation
# =============================================================================


class TestErrorHandling:
    """Test error handling across components."""

    def test_domain_with_invalid_type(self, user_class: Type[User]) -> None:
        """Test that invalid types raise appropriate errors."""
        with pytest.raises(ValidationError):
            user_class(id="string", username="test", email="test@example.com")

    def test_view_dto_from_domain_with_none_argument(self) -> None:
        """Test ViewDTO from_domain with None argument."""

        class SimpleView(ViewDTO[User]):
            id: int

        with pytest.raises((ValidationError, TypeError, AttributeError)):
            SimpleView.from_domain(None)

    def test_build_dto_with_wrong_types(self) -> None:
        """Test BuildDTO with wrong field types."""

        class SimpleBuild(BuildDTO[User]):
            username: str
            email: str

        with pytest.raises(ValidationError):
            SimpleBuild(username=123, email=456)

    def test_aggregate_with_mismatched_types(self, simple_user: User) -> None:
        """Test aggregate with mismatched field types."""

        class TypedAggregate(Aggregate):
            user: User
            product: Product

        with pytest.raises(ValidationError):
            TypedAggregate(user=simple_user, product=simple_user)


# =============================================================================
# Test Boundary Values
# =============================================================================


class TestBoundaryValues:
    """Test boundary values."""

    def test_max_int_value(self, user_class: Type[User]) -> None:
        """Test maximum integer value."""
        max_int = 2**63 - 1
        user = user_class(id=max_int, username="test", email="test@example.com")
        assert user.id == max_int

    def test_min_int_value(self, user_class: Type[User]) -> None:
        """Test minimum integer value."""
        min_int = -(2**63)
        user = user_class(id=min_int, username="test", email="test@example.com")
        assert user.id == min_int

    def test_empty_string_in_all_fields(self, user_class: Type[User]) -> None:
        """Test empty strings in all string fields."""
        user = user_class(id=1, username="", email="", tutor="")
        assert user.username == ""
        assert user.email == ""
        assert user.tutor == ""

    def test_single_character_strings(self, user_class: Type[User]) -> None:
        """Test single character strings."""
        user = user_class(id=1, username="a", email="b", tutor="c")
        assert user.username == "a"
        assert len(user.username) == 1


# =============================================================================
# Test Unicode and Encoding
# =============================================================================


class TestUnicodeAndEncoding:
    """Test unicode and encoding edge cases."""

    def test_emoji_in_fields(self, user_class: Type[User]) -> None:
        """Test emoji characters in fields."""
        user = user_class(
            id=1, username="rocket", email="test@example.com", tutor="professor"
        )
        assert user.username == "rocket"

    def test_mixed_unicode_scripts(self, user_class: Type[User]) -> None:
        """Test mixed unicode scripts."""
        user = user_class(
            id=1, username="Hello test", email="test@example.com"
        )
        assert "Hello" in user.username

    def test_rtl_languages(self, user_class: Type[User]) -> None:
        """Test right-to-left languages."""
        user = user_class(
            id=1, username="test_rtl", email="test@example.com",
        )
        assert user.username == "test_rtl"

    def test_zero_width_characters(self, user_class: Type[User]) -> None:
        """Test zero-width characters."""
        user = user_class(id=1, username="test\u200buser", email="test@example.com")
        assert "\u200b" in user.username
