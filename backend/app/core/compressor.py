"""
Lightweight prompt compression.

Strips filler/politeness phrases and redundant whitespace while preserving
task-relevant content. This is a heuristic, rule-based compressor -- a
starting point that can later be swapped for a learned compressor
(e.g. an LLMLingua-style model) without changing the pipeline's interface.
"""
import re

_FILLER_PATTERNS = [
    r"\bi was wondering if\b",
    r"\bcould you please\b",
    r"\bcan you please\b",
    r"\bwould you mind\b",
    r"\bi would like to know\b",
    r"\bi want to know\b",
    r"\bplease\b",
    r"\bkindly\b",
    r"\bjust wanted to ask\b",
    r"\bactually\b",
    r"\bbasically\b",
    r"\bin order to\b",
    r"\bvery\s+very\b",
]


def count_tokens(text: str) -> int:
    """
    Approximate token count without a network-dependent tokenizer.
    ~4 characters per token is the standard rule-of-thumb approximation for
    English text used by most cost estimators; swap for a real tokenizer
    (tiktoken/anthropic count-tokens API) if exact counts matter later.
    """
    text = text.strip()
    if not text:
        return 0
    return max(1, round(len(text) / 4))


def compress(text: str) -> tuple[str, int, int]:
    """Returns (compressed_text, original_token_count, compressed_token_count)."""
    original_tokens = count_tokens(text)

    compressed = text.strip()
    for pattern in _FILLER_PATTERNS:
        compressed = re.sub(pattern, "", compressed, flags=re.IGNORECASE)

    compressed = re.sub(r"\s+", " ", compressed).strip()
    compressed = re.sub(r"\s+([,.?!])", r"\1", compressed)

    if not compressed:
        compressed = text.strip()

    compressed_tokens = count_tokens(compressed)
    return compressed, original_tokens, compressed_tokens
