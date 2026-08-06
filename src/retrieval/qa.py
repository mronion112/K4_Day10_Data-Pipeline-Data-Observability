from __future__ import annotations

from dataclasses import dataclass
import re

from core.config import Settings
from core.utils import first_sentence
from retrieval.index import LocalEmbeddingIndex, SearchResult


@dataclass(frozen=True)
class AnswerResult:
    question: str
    answer: str
    retrieved_doc_ids: list[str]
    retrieved_contexts: list[str]
    retrieved_titles: list[str]


def _extract_answer(question: str, top_result: SearchResult) -> str:
    lowered = question.lower()
    metadata = top_result.metadata

    # Tien hanh va Anh de hoi ve tac gia
    author_keywords = [
        "who authored", "list the authors", "who wrote",
        "tác giả", "ai là tác giả", "tac gia",
    ]
    if any(kw in lowered for kw in author_keywords):
        return metadata["authors_joined"]

    # Hoi ve ngay xuat ban
    date_keywords = [
        "when was", "publication date", "published on",
        "xuất bản", "xuat ban", "ngày nào",
    ]
    if any(kw in lowered for kw in date_keywords):
        return metadata["published"]

    # Hoi ve linh vuc / categories
    cat_keywords = [
        "what categories", "lĩnh vực", "linh vuc", "thuộc lĩnh",
        "thuoc linh", "chủ đề", "chu de",
    ]
    if any(kw in lowered for kw in cat_keywords):
        return metadata["categories_joined"]

    # Hoi ve y nghia/ung dung -> tra ve tom tat summary
    abstract_keywords = [
        "ý nghĩa", "y nghia", "ứng dụng", "ung dung",
        "tóm tắt", "tom tat", "nội dung chính", "noi dung chinh",
        "so sánh", "so sanh",
    ]
    if any(kw in lowered for kw in abstract_keywords):
        return metadata["summary"]

    # Mac dinh: tra ve first sentence cua summary
    return first_sentence(metadata["summary"])


def answer_question(question: str, settings: Settings, index: LocalEmbeddingIndex, top_k: int | None = None) -> AnswerResult:
    title_match = re.search(r"'([^']+)'", question)
    exact = index.lookup(title_match.group(1)) if title_match else None
    retrieved = index.search(question, top_k=top_k)
    if exact:
        exact_result = SearchResult(
            paper_id=exact["paper_id"],
            title=exact["title"],
            score=1.0,
            content=exact["content"],
            metadata=exact["metadata"],
        )
        deduped = [exact_result] + [item for item in retrieved if item.paper_id != exact_result.paper_id]
        retrieved = deduped[: (top_k or settings.top_k)]
    if not retrieved:
        answer = "I don't know from the indexed corpus."
    else:
        answer = _extract_answer(question, retrieved[0])
    return AnswerResult(
        question=question,
        answer=answer,
        retrieved_doc_ids=[item.paper_id for item in retrieved],
        retrieved_contexts=[item.content for item in retrieved],
        retrieved_titles=[item.title for item in retrieved],
    )
