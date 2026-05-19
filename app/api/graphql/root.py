"""Root `Query` and `Mutation` types.

This module wires individual resolvers from `queries/` and `mutations/` onto
the root Strawberry types. Keep this file small: it should only do field
binding, not contain business logic.
"""

from __future__ import annotations

import strawberry

from app.api.graphql import queries
from app.api.graphql.types import AskResponseGQL


@strawberry.type
class Query:
    tools: list[str] = strawberry.field(
        resolver=queries.tools,
        description="List the names of all registered agent tools.",
    )
    ask: AskResponseGQL = strawberry.field(
        resolver=queries.ask,
        description="Ask Orion a question. Runs the full ReAct loop.",
    )


# Mutations are not used in the MVP. When you add one, declare a `Mutation`
# strawberry type here that binds resolvers from `app.api.graphql.mutations`,
# then pass `mutation=Mutation` to `strawberry.Schema(...)` in `schema.py`.
