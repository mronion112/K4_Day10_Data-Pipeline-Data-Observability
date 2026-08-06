from __future__ import annotations

"""Run a small, real LLM-agent demonstration against the baseline index."""

from core.config import load_settings, require_llm_credentials
from core.utils import read_json, write_json
from retrieval.agent import build_agent, run_agent_question
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    settings = load_settings()
    require_llm_credentials(settings)
    if not settings.paths.embeddings_json.exists() or not settings.paths.eval_testset.exists():
        raise RuntimeError("Baseline artifacts are missing. Run `uv run python script/run_phase1.py` first.")

    index = LocalEmbeddingIndex.load(settings)
    agent = build_agent(settings, index)
    questions = read_json(settings.paths.eval_testset)[:3]
    answers = []
    for item in questions:
        answer = run_agent_question(agent, item["question"])
        answers.append({
            "id": item["id"],
            "question": item["question"],
            "ground_truth": item["ground_truth"],
            "agent_answer": answer,
        })
        print(f"\nQ: {item['question']}\nA: {answer}\n")
    write_json(settings.paths.demo_answers, {
        "provider": settings.llm_provider,
        "model": settings.model_name,
        "answers": answers,
    })
    print(f"Saved real agent demo to {settings.paths.demo_answers}")


if __name__ == "__main__":
    main()
