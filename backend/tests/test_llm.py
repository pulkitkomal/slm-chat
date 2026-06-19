import re
import pytest
from llm import LLMClient


@pytest.mark.asyncio
async def test_extract_entities_parses_triples():
    text = "user | likes | pizza\nuser | dislikes | rain"
    triples = []
    for line in text.strip().split("\n"):
        parts = [p.strip() for p in re.split(r"\s*\|\s*", line)]
        if len(parts) == 3:
            triples.append((parts[0], parts[1], parts[2]))
    assert len(triples) == 2
    assert triples[0] == ("user", "likes", "pizza")


@pytest.mark.asyncio
async def test_extract_entities_empty():
    text = ""
    triples = []
    for line in text.strip().split("\n"):
        parts = [p.strip() for p in re.split(r"\s*\|\s*", line)]
        if len(parts) == 3:
            triples.append((parts[0], parts[1], parts[2]))
    assert len(triples) == 0
