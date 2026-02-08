"""Tests for Private[T] field enforcement."""

import pytest

from potato import Private, ViewDTO, BuildDTO, Domain


class TestPrivateFieldsViewDTO:
    """Test Private[T] exclusion from ViewDTO."""

    def test_private_field_raises_error_in_viewdto(self) -> None:
        """Test that including a Private field in ViewDTO raises TypeError."""

        class User(Domain):
            id: int
            username: str
            password_hash: Private[str]

        User.model_rebuild()

        with pytest.raises(TypeError, match="Private"):
            class UserView(ViewDTO[User]):
                id: int
                username: str
                password_hash: str  # This should be rejected

    def test_private_field_excluded_works(self) -> None:
        """Test that ViewDTO works when Private fields are not included."""

        class User(Domain):
            id: int
            username: str
            password_hash: Private[str]

        User.model_rebuild()

        class UserView(ViewDTO[User]):
            id: int
            username: str

        user = User(id=1, username="alice", password_hash="hashed")
        view = UserView.from_domain(user)

        assert view.id == 1
        assert view.username == "alice"
        assert not hasattr(view, "password_hash")


class TestPrivateFieldsBuildDTO:
    """Test Private[T] in BuildDTO context."""

    def test_private_fields_not_in_build_dto(self) -> None:
        """Test that Private fields can be excluded from BuildDTO."""

        class User(Domain):
            id: int
            username: str
            password_hash: Private[str]

        User.model_rebuild()

        class UserCreate(BuildDTO[User]):
            username: str

        dto = UserCreate(username="alice")
        user = dto.to_domain(id=1, password_hash="hashed_value")

        assert user.id == 1
        assert user.username == "alice"
        assert user.password_hash == "hashed_value"
