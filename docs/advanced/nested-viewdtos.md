# Nested ViewDTOs

When a ViewDTO field's type is another ViewDTO, Potato auto-builds it from the corresponding domain field.

## Basic Nesting

```python
from potato import Domain, ViewDTO, Field

class User(Domain):
    id: int
    username: str

class Post(Domain):
    id: int
    title: str
    author: User

class UserSummary(ViewDTO[User]):
    id: int
    username: str

class PostView(ViewDTO[Post]):
    id: int
    title: str
    author: UserSummary = Field(source=Post.author)
    # UserSummary.from_domain(post.author) is called automatically
```

When building `PostView.from_domain(post)`, Potato detects that `author` is a ViewDTO type and calls `UserSummary.from_domain(post.author)` for you.

## Lists of ViewDTOs

Nesting also works with lists:

```python
class User(Domain):
    id: int
    username: str
    posts: list[Post]

class PostSummary(ViewDTO[Post]):
    id: int
    title: str

class UserDetail(ViewDTO[User]):
    id: int
    username: str
    posts: list[PostSummary] = Field(source=User.posts)
    # PostSummary.from_domain(p) is called for each post
```

## Context Propagation

When you pass a `context` to `from_domain()`, it propagates to nested ViewDTOs:

```python
class Permissions:
    def __init__(self, is_admin: bool):
        self.is_admin = is_admin

class UserSummary(ViewDTO[User, Permissions]):
    id: int
    username: str
    email: str = Field(visible=lambda ctx: ctx.is_admin)

class PostView(ViewDTO[Post, Permissions]):
    id: int
    title: str
    author: UserSummary = Field(source=Post.author)

# Context flows to nested UserSummary
view = PostView.from_domain(post, context=Permissions(is_admin=True))
```

## Next Steps

- **[Inheritance](inheritance.md)** — Share fields between ViewDTOs
- **[Visibility](visibility.md)** — Context-based field inclusion
