"""Build the Strawberry schema and the FastAPI GraphQL router."""

from __future__ import annotations

import strawberry
from strawberry.fastapi import GraphQLRouter

from app.api.graphql.root import Query

schema = strawberry.Schema(query=Query)

graphql_router: GraphQLRouter = GraphQLRouter(schema, graphql_ide="graphiql")
