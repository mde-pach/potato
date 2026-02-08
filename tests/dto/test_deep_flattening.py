"""Tests for deep field flattening (User.address.city)."""

from potato import Field, ViewDTO, Domain


class Address(Domain):
    city: str
    street: str
    zip_code: str


class UserWithAddress(Domain):
    id: int
    name: str
    address: Address


class TestDeepFlattening:
    """Test deep field flattening via FieldProxy chaining."""

    def test_single_level_deep(self) -> None:
        """Test User.address.city single-level deep access."""

        class UserView(ViewDTO[UserWithAddress]):
            name: str
            city: str = Field(source=UserWithAddress.address.city)

        address = Address(city="Paris", street="Rue de Rivoli", zip_code="75001")
        user = UserWithAddress(id=1, name="Alice", address=address)
        view = UserView.from_domain(user)

        assert view.name == "Alice"
        assert view.city == "Paris"

    def test_multiple_deep_fields(self) -> None:
        """Test extracting multiple deep fields."""

        class UserView(ViewDTO[UserWithAddress]):
            name: str
            city: str = Field(source=UserWithAddress.address.city)
            street: str = Field(source=UserWithAddress.address.street)
            zip_code: str = Field(source=UserWithAddress.address.zip_code)

        address = Address(city="London", street="Baker Street", zip_code="NW1 6XE")
        user = UserWithAddress(id=1, name="Sherlock", address=address)
        view = UserView.from_domain(user)

        assert view.name == "Sherlock"
        assert view.city == "London"
        assert view.street == "Baker Street"
        assert view.zip_code == "NW1 6XE"

    def test_deep_flattening_with_transform(self) -> None:
        """Test deep field access combined with transform."""

        class UserView(ViewDTO[UserWithAddress]):
            name: str
            city_upper: str = Field(
                source=UserWithAddress.address.city,
                transform=lambda c: c.upper(),
            )

        address = Address(city="Berlin", street="Unter den Linden", zip_code="10117")
        user = UserWithAddress(id=1, name="Hans", address=address)
        view = UserView.from_domain(user)

        assert view.city_upper == "BERLIN"
