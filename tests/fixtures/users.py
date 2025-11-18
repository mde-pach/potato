"""User domain fixtures."""

from __future__ import annotations

import pytest

from .domains import User


@pytest.fixture
def simple_user() -> User:
    """A user with only required fields."""
    return User(id=1, username="alice", email="alice@example.com")


@pytest.fixture
def user_with_tutor() -> User:
    """A user with a tutor."""
    return User(id=2, username="bob", email="bob@example.com", tutor="alice")


@pytest.fixture
def user_with_friends() -> User:
    """A user with friends."""
    return User(
        id=3,
        username="charlie",
        email="charlie@example.com",
        friends=["alice", "bob"],
    )


@pytest.fixture
def complete_user() -> User:
    """A user with all fields populated."""
    return User(
        id=4,
        username="diana",
        email="diana@example.com",
        tutor="alice",
        friends=["bob", "charlie"],
    )


@pytest.fixture
def buyer_user() -> User:
    """A user representing a buyer in transactions."""
    return User(id=10, username="buyer1", email="buyer1@example.com")


@pytest.fixture
def seller_user() -> User:
    """A user representing a seller in transactions."""
    return User(id=20, username="seller1", email="seller1@example.com")

