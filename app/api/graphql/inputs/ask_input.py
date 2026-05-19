"""Input type for the `ask` query.

Defined as an input object so we can grow new fields (model override, max
iterations, locale, etc.) without changing the field signature.
"""

from __future__ import annotations

import strawberry


@strawberry.input(description="Arguments accepted by the `ask` query.")
class AskInput:
    query: str = strawberry.field(description="The user's question for Orion.")
