"""Query resolvers.

Each query lives in its own module and exposes a single resolver function
suitable for attaching to the root `Query` type as a `strawberry.field`.
"""

from app.api.graphql.queries.ask import ask
from app.api.graphql.queries.tools import tools

__all__ = ["ask", "tools"]
