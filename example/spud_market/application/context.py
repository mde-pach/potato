from dataclasses import dataclass


@dataclass
class Permissions:
    is_admin: bool
    user_id: int | None = None
