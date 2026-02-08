"""Tests for lifecycle hooks (@before_build, @after_build)."""

import pytest

from potato import ViewDTO, Domain, before_build, after_build


class User(Domain):
    id: int
    username: str


class AuditContext:
    def __init__(self, reviewer: str):
        self.reviewer = reviewer


class TestBeforeBuild:
    """Test @before_build hook."""

    def test_before_build_enriches_data(self) -> None:
        """Test that before_build adds extra data."""

        class UserView(ViewDTO[User, AuditContext]):
            id: int
            username: str
            reviewer: str = ""

            @before_build
            @classmethod
            def enrich(cls, entity: User, context: AuditContext) -> dict:
                return {"reviewer": context.reviewer}

        user = User(id=1, username="alice")
        ctx = AuditContext(reviewer="bob")
        view = UserView.from_domain(user, context=ctx)

        assert view.id == 1
        assert view.username == "alice"
        assert view.reviewer == "bob"


class TestAfterBuild:
    """Test @after_build hook."""

    def test_after_build_validates(self) -> None:
        """Test that after_build can validate the instance."""
        calls = []

        class UserView(ViewDTO[User]):
            id: int
            username: str

            @after_build
            def on_build(self) -> None:
                calls.append(self.username)

        user = User(id=1, username="alice")
        view = UserView.from_domain(user)

        assert view.username == "alice"
        assert calls == ["alice"]

    def test_after_build_raises_error(self) -> None:
        """Test that after_build can raise validation errors."""

        class UserView(ViewDTO[User]):
            id: int
            username: str

            @after_build
            def validate_username(self) -> None:
                if self.username == "invalid":
                    raise ValueError("Invalid username")

        user = User(id=1, username="invalid")
        with pytest.raises(ValueError, match="Invalid username"):
            UserView.from_domain(user)
