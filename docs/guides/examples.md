# Real-World Examples

Complete examples showing how to use Potato in real-world scenarios.

## User Management System

A complete user management system with create, read, update operations.

### Domain Models

```python
from potato.domain import Domain
from datetime import datetime

class User(Domain):
    id: int
    username: str
    email: str
    full_name: str
    created_at: datetime
    is_active: bool = True
```

### BuildDTOs

```python
from potato.dto import BuildDTO

class CreateUser(BuildDTO[User]):
    username: str
    email: str
    full_name: str

class UpdateUser(BuildDTO[User]):
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
```

### ViewDTOs

```python
from potato.dto import ViewDTO
from typing import Annotated

class UserView(ViewDTO[User]):
    id: int
    username: str
    email: str
    full_name: str
    created_at: str
    is_active: bool

class UserSummary(ViewDTO[User]):
    id: int
    username: str
    full_name: str
```

### Usage

```python
from datetime import datetime

def create_user(create_dto: CreateUser) -> UserView:
    # Validate username uniqueness
    if username_exists(create_dto.username):
        raise ValueError("Username already exists")
    
    # Create domain model
    user = User(
        **create_dto.model_dump(),
        id=generate_id(),
        created_at=datetime.now()
    )
    
    # Save to database
    save_user(user)
    
    # Return view
    return UserView.build(user)

def get_user(user_id: int) -> UserView:
    user = fetch_user(user_id)
    return UserView.build(user)

def list_users() -> list[UserSummary]:
    users = fetch_all_users()
    return [UserSummary.build(user) for user in users]

def update_user(user_id: int, update_dto: UpdateUser) -> UserView:
    user = fetch_user(user_id)
    
    # Update only provided fields
    update_data = update_dto.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    save_user(user)
    return UserView.build(user)
```

## E-commerce Order System

A complete e-commerce order system with buyer, seller, and products.

### Domain Models

```python
from potato.domain import Domain
from potato.domain.aggregates import Aggregate
from typing import Annotated

class User(Domain):
    id: int
    username: str
    email: str

class Product(Domain):
    id: int
    name: str
    description: str
    base_price: int

class Price(Domain):
    amount: int
    currency: str

class Order(Aggregate[User, Product, Price]):
    customer: User
    product: Product
    price_amount: Annotated[int, Price.amount]
    price_currency: Annotated[str, Price.currency]
    quantity: int
    status: str = "pending"
```

### Aliases for Multiple Users

```python
# Create aliases for buyer and seller
Buyer = User.alias("buyer")
Seller = User.alias("seller")
```

### ViewDTOs

```python
from potato.dto import ViewDTO

class OrderView(ViewDTO[Aggregate[User, Product]]):
    customer_id: Annotated[int, User.id]
    customer_name: Annotated[str, User.username]
    product_id: Annotated[int, Product.id]
    product_name: Annotated[str, Product.name]
    price_amount: int
    price_currency: str
    quantity: int
    status: str

class TransactionView(ViewDTO[Aggregate[Buyer, Seller, Product]]):
    buyer_id: Annotated[int, Buyer.id]
    buyer_name: Annotated[str, Buyer.username]
    buyer_email: Annotated[str, Buyer.email]
    
    seller_id: Annotated[int, Seller.id]
    seller_name: Annotated[str, Seller.username]
    seller_email: Annotated[str, Seller.email]
    
    product_id: Annotated[int, Product.id]
    product_name: Annotated[str, Product.name]
    product_description: Annotated[str, Product.description]
    
    price_amount: int
    price_currency: str
    quantity: int
```

### BuildDTOs

```python
from potato.dto import BuildDTO

class CreateOrder(BuildDTO[Order]):
    customer_id: int
    product_id: int
    quantity: int
```

### Usage

```python
def create_order(create_dto: CreateOrder) -> OrderView:
    # Fetch related domains
    customer = fetch_user(create_dto.customer_id)
    product = fetch_product(create_dto.product_id)
    
    # Calculate price
    price = calculate_price(product, create_dto.quantity)
    
    # Create order
    order = Order(
        customer=customer,
        product=product,
        price_amount=price.amount,
        price_currency=price.currency,
        quantity=create_dto.quantity,
        status="pending"
    )
    
    # Save order
    save_order(order)
    
    # Return view
    return OrderView.build(customer, product)

def get_transaction(order_id: int) -> TransactionView:
    order = fetch_order(order_id)
    
    # Fetch buyer and seller
    buyer = fetch_user(order.customer_id)
    seller = fetch_seller_for_product(order.product_id)
    
    return TransactionView.build(
        buyer=buyer,
        seller=seller,
        product=order.product
    )
```

## Social Network Follow System

A system for managing user follows with source and target users.

### Domain Models

```python
from potato.domain import Domain

class User(Domain):
    id: int
    username: str
    email: str

class Follow(Domain):
    id: int
    follower_id: int
    followee_id: int
    created_at: str
```

### Aliases

```python
Follower = User.alias("follower")
Followee = User.alias("followee")
```

### ViewDTOs

```python
from potato.dto import ViewDTO
from potato.domain.aggregates import Aggregate
from typing import Annotated

class FollowView(ViewDTO[Aggregate[Follower, Followee]]):
    follower_id: Annotated[int, Follower.id]
    follower_username: Annotated[str, Follower.username]
    followee_id: Annotated[int, Followee.id]
    followee_username: Annotated[str, Followee.username]
    created_at: str

class UserFollowersView(ViewDTO[User]):
    id: int
    username: str
    email: str
```

### BuildDTOs

```python
from potato.dto import BuildDTO

class CreateFollow(BuildDTO[Follow]):
    followee_id: int
```

### Usage

```python
def follow_user(current_user_id: int, create_dto: CreateFollow) -> FollowView:
    # Check if already following
    if is_following(current_user_id, create_dto.followee_id):
        raise ValueError("Already following this user")
    
    # Create follow relationship
    follow = Follow(
        id=generate_id(),
        follower_id=current_user_id,
        followee_id=create_dto.followee_id,
        created_at=get_current_timestamp()
    )
    
    save_follow(follow)
    
    # Fetch users for view
    follower = fetch_user(current_user_id)
    followee = fetch_user(create_dto.followee_id)
    
    return FollowView.build(follower=follower, followee=followee)

def get_followers(user_id: int) -> list[UserFollowersView]:
    follows = fetch_followers(user_id)
    followers = [fetch_user(f.follower_id) for f in follows]
    return [UserFollowersView.build(follower) for follower in followers]
```

## Blog Post System

A blog system with posts, authors, and comments.

### Domain Models

```python
from potato.domain import Domain
from potato.domain.aggregates import Aggregate
from typing import Annotated

class User(Domain):
    id: int
    username: str
    email: str

class Post(Aggregate[User]):
    id: int
    title: str
    content: str
    author: User
    published: bool = False
    created_at: str

class Comment(Aggregate[User, Post]):
    id: int
    content: str
    author: User
    post_id: Annotated[int, Post.id]
    created_at: str
```

### ViewDTOs

```python
from potato.dto import ViewDTO
from typing import Annotated

class PostView(ViewDTO[Aggregate[User]]):
    id: int
    title: str
    content: str
    author_id: Annotated[int, User.id]
    author_username: Annotated[str, User.username]
    published: bool
    created_at: str

class PostSummary(ViewDTO[Aggregate[User]]):
    id: int
    title: str
    author_username: Annotated[str, User.username]
    created_at: str

class CommentView(ViewDTO[Aggregate[User, Post]]):
    id: int
    content: str
    author_id: Annotated[int, User.id]
    author_username: Annotated[str, User.username]
    post_id: Annotated[int, Post.id]
    created_at: str
```

### BuildDTOs

```python
from potato.dto import BuildDTO

class CreatePost(BuildDTO[Post]):
    title: str
    content: str

class CreateComment(BuildDTO[Comment]):
    content: str
    post_id: int
```

### Usage

```python
def create_post(author_id: int, create_dto: CreatePost) -> PostView:
    author = fetch_user(author_id)
    
    post = Post(
        id=generate_id(),
        title=create_dto.title,
        content=create_dto.content,
        author=author,
        published=False,
        created_at=get_current_timestamp()
    )
    
    save_post(post)
    return PostView.build(author)

def get_post(post_id: int) -> PostView:
    post = fetch_post(post_id)
    return PostView.build(post.author)

def list_posts() -> list[PostSummary]:
    posts = fetch_all_posts()
    return [PostSummary.build(post.author) for post in posts]

def create_comment(author_id: int, create_dto: CreateComment) -> CommentView:
    author = fetch_user(author_id)
    post = fetch_post(create_dto.post_id)
    
    comment = Comment(
        id=generate_id(),
        content=create_dto.content,
        author=author,
        post_id=post.id,
        created_at=get_current_timestamp()
    )
    
    save_comment(comment)
    return CommentView.build(author, post)
```

## TODO: FastAPI Integration Example

This section will contain a complete FastAPI integration example showing how to use Potato with FastAPI endpoints.

The example will cover:

- Setting up FastAPI routes
- Using BuildDTO for request bodies
- Using ViewDTO for response models
- Error handling
- Request validation

______________________________________________________________________

## Next Steps

- **[Patterns](patterns.md)** - Common patterns and best practices
- **[ViewDTO](../core/viewdto.md)** - Learn more about ViewDTO
- **[BuildDTO](../core/builddto.md)** - Learn more about BuildDTO
