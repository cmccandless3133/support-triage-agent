"""Knowledge-base loading and BM25 retrieval (pure Python, no vector DB needed)."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = set(
    "a an and are as at be but by can do does for from has have how i if in into is it its "
    "me my of on or our so that the their them then there this to was we what when where "
    "which who will with you your".split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


@dataclass(frozen=True)
class Article:
    id: str
    title: str
    category: str
    body: str

    @property
    def text(self) -> str:
        return f"{self.title}\n{self.body}"


def load_kb(kb_dir: str | Path) -> dict[str, Article]:
    articles: dict[str, Article] = {}
    for path in sorted(Path(kb_dir).glob("KB-*.md")):
        raw = path.read_text(encoding="utf-8")
        _, front, body = raw.split("---", 2)
        meta = dict(
            line.split(":", 1) for line in front.strip().splitlines() if ":" in line
        )
        meta = {k.strip(): v.strip() for k, v in meta.items()}
        articles[meta["id"]] = Article(meta["id"], meta["title"], meta["category"], body.strip())
    if not articles:
        raise FileNotFoundError(f"No KB-*.md files found in {kb_dir}")
    return articles


class BM25Index:
    """Okapi BM25 over article title + body."""

    def __init__(self, articles: dict[str, Article], k1: float = 1.5, b: float = 0.75):
        self.ids = list(articles)
        self.docs = [tokenize(articles[i].text) for i in self.ids]
        self.k1, self.b = k1, b
        self.avgdl = sum(map(len, self.docs)) / len(self.docs)
        self.tf = [Counter(d) for d in self.docs]
        df = Counter(t for d in self.docs for t in set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def search(self, query: str, k: int = 4) -> list[tuple[str, float]]:
        q = tokenize(query)
        scores = []
        for idx, tf in enumerate(self.tf):
            dl = len(self.docs[idx])
            s = 0.0
            for t in q:
                if t not in tf:
                    continue
                f = tf[t]
                s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            scores.append((self.ids[idx], s))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [x for x in scores[:k] if x[1] > 0]
