"""Tests for nested ViewDTO auto-building."""

from potato import Field, ViewDTO, Domain, Aggregate


class Post(Domain):
    id: int
    title: str
    body: str


class Author(Domain):
    id: int
    name: str


class TestNestedViewDTO:
    """Test nested ViewDTO auto-building."""

    def test_single_nested_viewdto(self) -> None:
        """Test that a ViewDTO field typed as another ViewDTO auto-builds."""

        class AuthorSummary(ViewDTO[Author]):
            id: int
            name: str

        class BlogAggregate(Aggregate):
            post: Post
            author: Author

        class PostView(ViewDTO[BlogAggregate]):
            title: str = Field(source=BlogAggregate.post.title)
            author: AuthorSummary = Field(source=BlogAggregate.author)

        post = Post(id=1, title="Hello World", body="Content here")
        author = Author(id=10, name="Alice")
        aggregate = BlogAggregate(post=post, author=author)

        view = PostView.from_domain(aggregate)

        assert view.title == "Hello World"
        assert isinstance(view.author, AuthorSummary)
        assert view.author.id == 10
        assert view.author.name == "Alice"

    def test_list_nested_viewdto(self) -> None:
        """Test that list[ViewDTO] fields auto-build from list of domains."""

        class PostSummary(ViewDTO[Post]):
            id: int
            title: str

        class AuthorWithPosts(Domain):
            id: int
            name: str
            posts: list[Post]

        class AuthorView(ViewDTO[AuthorWithPosts]):
            id: int
            name: str
            posts: list[PostSummary]

        posts = [
            Post(id=1, title="First Post", body="Body 1"),
            Post(id=2, title="Second Post", body="Body 2"),
        ]
        author = AuthorWithPosts(id=10, name="Alice", posts=posts)

        view = AuthorView.from_domain(author)

        assert view.id == 10
        assert view.name == "Alice"
        assert len(view.posts) == 2
        assert isinstance(view.posts[0], PostSummary)
        assert view.posts[0].title == "First Post"
        assert view.posts[1].title == "Second Post"

    def test_nested_viewdto_empty_list(self) -> None:
        """Test nested ViewDTO with empty list."""

        class PostSummary(ViewDTO[Post]):
            id: int
            title: str

        class AuthorWithPosts(Domain):
            id: int
            name: str
            posts: list[Post]

        class AuthorView(ViewDTO[AuthorWithPosts]):
            id: int
            name: str
            posts: list[PostSummary]

        author = AuthorWithPosts(id=10, name="Alice", posts=[])
        view = AuthorView.from_domain(author)

        assert view.posts == []
