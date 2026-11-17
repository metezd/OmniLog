"""Deterministic fake OpenAI responses for tests."""

import hashlib
import json
from types import SimpleNamespace


class FakeOpenAI:
    """A small fake for the OpenAI embeddings and chat completion APIs."""

    def __init__(self):
        self.embeddings = SimpleNamespace(create=self._create_embeddings)
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create_completion)
        )

    @staticmethod
    def _create_embeddings(*, model, input, dimensions=None, **kwargs):
        data = []

        for index, text in enumerate(input):
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vector = [
                (digest[i % len(digest)] / 127.5) - 1.0
                for i in range(dimensions or 1536)
            ]
            data.append(
                SimpleNamespace(index=index, embedding=vector)
            )

        return SimpleNamespace(data=data)

    @staticmethod
    def _create_completion(*, model, messages, **kwargs):
        text = messages[-1]["content"].lower()

        spoiler_words = (
            "dies",
            "killer",
            "murder",
            "death",
            "betrayal",
            "turns out",
            "ending",
            "revealed",
        )
        contains_spoiler = any(word in text for word in spoiler_words)

        result = {
            "contains_spoiler": contains_spoiler,
            "score": 0.95 if contains_spoiler else 0.05,
        }

        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(result))
                )
            ]
        )