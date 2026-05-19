"""GraphQL layer for Orion.

Folder layout:

    graphql/
    ├── __init__.py       # re-exports `graphql_router` + `schema`
    ├── schema.py         # builds strawberry.Schema + the FastAPI router
    ├── root.py           # root Query/Mutation types (field bindings only)
    ├── types/            # output types (one per file)
    ├── inputs/           # input types  (one per file)
    ├── queries/          # query resolvers  (one per file)
    └── mutations/        # mutation resolvers (one per file)
"""

from app.api.graphql.schema import graphql_router, schema

__all__ = ["graphql_router", "schema"]
