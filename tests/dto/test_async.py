"""Tests for async ViewDTO support (afrom_domain, afrom_domains)."""

import asyncio

import pytest

from potato import Domain, Field, ViewDTO, computed, before_build, after_build


class User(Domain):
    id: int
    username: str
    email: str


class Permissions:
    def __init__(self, is_admin: bool = False):
        self.is_admin = is_admin


class TestAsyncBasic:
    """Test basic afrom_domain with sync ViewDTO."""

    @pytest.mark.asyncio
    async def test_afrom_domain_sync_viewdto(self) -> None:
        """afrom_domain works with a fully sync ViewDTO."""

        class UserView(ViewDTO[User]):
            id: int
            username: str

        user = User(id=1, username="alice", email="alice@example.com")
        view = await UserView.afrom_domain(user)

        assert view.id == 1
        assert view.username == "alice"

    @pytest.mark.asyncio
    async def test_afrom_domains_sync_viewdto(self) -> None:
        """afrom_domains works and processes concurrently."""

        class UserView(ViewDTO[User]):
            id: int
            username: str

        users = [
            User(id=1, username="alice", email="a@example.com"),
            User(id=2, username="bob", email="b@example.com"),
        ]
        views = await UserView.afrom_domains(users)

        assert len(views) == 2
        assert views[0].username == "alice"
        assert views[1].username == "bob"


class TestAsyncComputedFields:
    """Test async @computed fields."""

    @pytest.mark.asyncio
    async def test_async_computed_field(self) -> None:
        """Async computed field is awaited."""

        class UserView(ViewDTO[User]):
            id: int
            username: str
            greeting: str = ""

            @computed
            async def greeting(self, user: User) -> str:
                await asyncio.sleep(0)  # simulate async work
                return f"Hello, {user.username}!"

        user = User(id=1, username="alice", email="alice@example.com")
        view = await UserView.afrom_domain(user)

        assert view.greeting == "Hello, alice!"

    @pytest.mark.asyncio
    async def test_mixed_sync_async_computed(self) -> None:
        """Mix of sync and async computed fields works."""

        class UserView(ViewDTO[User]):
            id: int
            username: str
            sync_field: str = ""
            async_field: str = ""

            @computed
            def sync_field(self, user: User) -> str:
                return user.username.upper()

            @computed
            async def async_field(self, user: User) -> str:
                await asyncio.sleep(0)
                return user.email.upper()

        user = User(id=1, username="alice", email="alice@example.com")
        view = await UserView.afrom_domain(user)

        assert view.sync_field == "ALICE"
        assert view.async_field == "ALICE@EXAMPLE.COM"


class TestAsyncHooks:
    """Test async before_build and after_build hooks."""

    @pytest.mark.asyncio
    async def test_async_before_build(self) -> None:
        """Async @before_build hook is awaited."""

        class UserView(ViewDTO[User]):
            id: int
            username: str
            extra: str = ""

            @before_build
            async def enrich(cls, user: User) -> dict:
                await asyncio.sleep(0)
                return {"extra": f"enriched:{user.username}"}

        user = User(id=1, username="alice", email="alice@example.com")
        view = await UserView.afrom_domain(user)

        assert view.extra == "enriched:alice"

    @pytest.mark.asyncio
    async def test_async_after_build(self) -> None:
        """Async @after_build hook is awaited."""
        calls = []

        class UserView(ViewDTO[User]):
            id: int
            username: str

            @after_build
            async def on_build(self) -> None:
                await asyncio.sleep(0)
                calls.append("async_after")

        user = User(id=1, username="alice", email="alice@example.com")
        await UserView.afrom_domain(user)

        assert calls == ["async_after"]


class TestAsyncTransform:
    """Test async transforms."""

    @pytest.mark.asyncio
    async def test_async_transform(self) -> None:
        """Async transform function is awaited."""

        async def async_upper(val: str) -> str:
            await asyncio.sleep(0)
            return val.upper()

        class UserView(ViewDTO[User]):
            id: int
            email: str = Field(source=User.email, transform=async_upper)

        user = User(id=1, username="alice", email="alice@example.com")
        view = await UserView.afrom_domain(user)

        assert view.email == "ALICE@EXAMPLE.COM"


class TestAsyncWithContext:
    """Test async methods with typed context."""

    @pytest.mark.asyncio
    async def test_afrom_domain_required_context(self) -> None:
        """afrom_domain enforces required context."""

        class UserView(ViewDTO[User, Permissions]):
            id: int
            username: str

        user = User(id=1, username="alice", email="alice@example.com")

        with pytest.raises(TypeError, match="requires context"):
            await UserView.afrom_domain(user)

    @pytest.mark.asyncio
    async def test_afrom_domain_optional_context(self) -> None:
        """afrom_domain works with optional context."""

        class UserView(ViewDTO[User, Permissions | None]):
            id: int
            username: str

        user = User(id=1, username="alice", email="alice@example.com")
        view = await UserView.afrom_domain(user)
        assert view.username == "alice"

    @pytest.mark.asyncio
    async def test_afrom_domain_with_context_provided(self) -> None:
        """afrom_domain passes context correctly."""

        class UserView(ViewDTO[User, Permissions]):
            id: int
            username: str

        user = User(id=1, username="alice", email="alice@example.com")
        ctx = Permissions(is_admin=True)
        view = await UserView.afrom_domain(user, context=ctx)
        assert view.username == "alice"


class TestAsyncNestedViewDTO:
    """Test async with nested ViewDTO building."""

    @pytest.mark.asyncio
    async def test_async_nested_viewdto(self) -> None:
        """Nested ViewDTO is built using afrom_domain in async path."""

        class Profile(Domain):
            user_id: int
            display_name: str

        class ProfileView(ViewDTO[Profile]):
            user_id: int
            display_name: str

        class UserWithProfile(Domain):
            id: int
            username: str
            profile: Profile

        class UserWithProfileView(ViewDTO[UserWithProfile]):
            id: int
            username: str
            profile: ProfileView

        profile = Profile(user_id=1, display_name="Alice Display")
        user = UserWithProfile(id=1, username="alice", profile=profile)

        view = await UserWithProfileView.afrom_domain(user)

        assert view.id == 1
        assert view.username == "alice"
        assert isinstance(view.profile, ProfileView)
        assert view.profile.display_name == "Alice Display"
