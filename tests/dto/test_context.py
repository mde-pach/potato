"""Tests for typed context support in ViewDTO and BuildDTO."""

import pytest

from potato import BuildDTO, Domain, Field, ViewDTO, computed, after_build


class Permissions:
    def __init__(self, is_admin: bool = False, role: str = "user"):
        self.is_admin = is_admin
        self.role = role


class User(Domain):
    id: int
    username: str
    email: str


class TestViewDTORequiredContext:
    """Test ViewDTO with required context (no None in union)."""

    def test_required_context_missing_raises_type_error(self) -> None:
        """Missing required context raises TypeError."""

        class UserView(ViewDTO[User, Permissions]):
            id: int
            username: str

        user = User(id=1, username="alice", email="alice@example.com")

        with pytest.raises(TypeError, match="requires context"):
            UserView.from_domain(user)

    def test_required_context_wrong_type_raises_type_error(self) -> None:
        """Wrong context type raises TypeError."""

        class UserView(ViewDTO[User, Permissions]):
            id: int
            username: str

        user = User(id=1, username="alice", email="alice@example.com")

        with pytest.raises(TypeError, match="Expected context of type"):
            UserView.from_domain(user, context="wrong")

    def test_required_context_provided_works(self) -> None:
        """Providing correct required context works."""

        class UserView(ViewDTO[User, Permissions]):
            id: int
            username: str

        user = User(id=1, username="alice", email="alice@example.com")
        ctx = Permissions(is_admin=True)
        view = UserView.from_domain(user, context=ctx)

        assert view.id == 1
        assert view.username == "alice"


class TestViewDTOOptionalContext:
    """Test ViewDTO with optional context (Ctx | None)."""

    def test_optional_context_missing_works(self) -> None:
        """Missing optional context works, context is None."""

        class UserView(ViewDTO[User, Permissions | None]):
            id: int
            username: str

        user = User(id=1, username="alice", email="alice@example.com")
        view = UserView.from_domain(user)

        assert view.id == 1
        assert view.username == "alice"

    def test_optional_context_provided_works(self) -> None:
        """Providing optional context works."""

        class UserView(ViewDTO[User, Permissions | None]):
            id: int
            username: str

        user = User(id=1, username="alice", email="alice@example.com")
        ctx = Permissions(is_admin=True)
        view = UserView.from_domain(user, context=ctx)

        assert view.id == 1

    def test_optional_context_wrong_type_raises(self) -> None:
        """Wrong type for optional context still raises TypeError."""

        class UserView(ViewDTO[User, Permissions | None]):
            id: int
            username: str

        user = User(id=1, username="alice", email="alice@example.com")

        with pytest.raises(TypeError, match="Expected context of type"):
            UserView.from_domain(user, context="wrong")


class TestTransformWithContext:
    """Test 2-arg transforms that receive context."""

    def test_transform_with_context(self) -> None:
        """A 2-arg transform receives (value, context)."""

        class UserView(ViewDTO[User, Permissions | None]):
            id: int
            email: str = Field(
                source=User.email,
                transform=lambda val, ctx: val if ctx and ctx.is_admin else "***",
            )

        user = User(id=1, username="alice", email="alice@example.com")

        # With admin context
        admin = Permissions(is_admin=True)
        view = UserView.from_domain(user, context=admin)
        assert view.email == "alice@example.com"

        # Without context (hidden)
        view2 = UserView.from_domain(user)
        assert view2.email == "***"

    def test_transform_single_arg_backward_compat(self) -> None:
        """A 1-arg transform still works (backward compat)."""

        class UserView(ViewDTO[User, Permissions | None]):
            id: int
            email: str = Field(
                source=User.email,
                transform=lambda val: val.upper(),
            )

        user = User(id=1, username="alice", email="alice@example.com")
        view = UserView.from_domain(user, context=Permissions())
        assert view.email == "ALICE@EXAMPLE.COM"


class TestAfterBuildWithContext:
    """Test @after_build hooks receiving context."""

    def test_after_build_receives_context(self) -> None:
        """@after_build hook can receive context parameter."""
        calls = []

        class UserView(ViewDTO[User, Permissions]):
            id: int
            username: str

            @after_build
            def on_build(self, context: Permissions) -> None:
                calls.append(context.role)

        user = User(id=1, username="alice", email="alice@example.com")
        ctx = Permissions(is_admin=True, role="admin")
        UserView.from_domain(user, context=ctx)

        assert calls == ["admin"]

    def test_after_build_without_context_param_backward_compat(self) -> None:
        """@after_build hook without context param still works."""
        calls = []

        class UserView(ViewDTO[User, Permissions | None]):
            id: int
            username: str

            @after_build
            def on_build(self) -> None:
                calls.append("called")

        user = User(id=1, username="alice", email="alice@example.com")
        UserView.from_domain(user)

        assert calls == ["called"]


class TestNoContextViewDTO:
    """Test ViewDTO without context (no second type param) still works."""

    def test_no_context_type_works(self) -> None:
        """ViewDTO[User] without context type works as before."""

        class UserView(ViewDTO[User]):
            id: int
            username: str

        user = User(id=1, username="alice", email="alice@example.com")
        view = UserView.from_domain(user)
        assert view.username == "alice"

    def test_no_context_type_with_context_kwarg(self) -> None:
        """Passing context= to a ViewDTO without context type is allowed (no validation)."""

        class UserView(ViewDTO[User]):
            id: int
            username: str

        user = User(id=1, username="alice", email="alice@example.com")
        view = UserView.from_domain(user, context="anything")
        assert view.username == "alice"
