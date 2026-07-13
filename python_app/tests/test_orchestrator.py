from unittest.mock import MagicMock

from app.agents.orchestrator import Orchestrator, classify_intent
from app.llm.client import LLMResult


def test_classify_intent_always_includes_orch_and_iitr():
    active = classify_intent("what is NPV")
    assert "orch" in active and "iitr" in active


def test_classify_intent_detects_linkedin_job_keywords():
    assert "li" in classify_intent("Tell me about Professor Rajat Agrawal's LinkedIn")


def test_classify_intent_detects_mospi_keywords():
    assert "mospi" in classify_intent("What is India's GDP growth this year?")


def test_classify_intent_detects_finance_keywords():
    assert "mstar" in classify_intent("How is this stock's market cap trending?")


def test_classify_intent_no_false_positive_on_plain_query():
    active = classify_intent("Explain Porter's Five Forces")
    assert active == ["orch", "iitr"]


def _fake_client(ok=True, text="A helpful answer.", api_key="proxy"):
    client = MagicMock()
    client.api_key = api_key
    client.complete.return_value = LLMResult(ok=ok, text=text, error="" if ok else "boom", input_tokens=10, output_tokens=20)
    return client


def test_orchestrator_answer_success_path():
    orch = Orchestrator(_fake_client())
    result = orch.answer("Explain NPV", system_prompt="sys")
    assert result.ok
    assert result.text == "A helpful answer."
    assert "orch" in result.active_agents
    assert result.elapsed_seconds >= 0


def test_orchestrator_answer_failure_path_returns_error_not_exception():
    orch = Orchestrator(_fake_client(ok=False))
    result = orch.answer("Explain NPV", system_prompt="sys")
    assert not result.ok
    assert result.error == "boom"
    assert result.trace  # still produces a trace even on failure


def test_orchestrator_passes_history_and_query_as_messages():
    client = _fake_client()
    orch = Orchestrator(client)
    history = [{"role": "user", "content": "earlier question"}, {"role": "assistant", "content": "earlier answer"}]
    orch.answer("follow-up question", system_prompt="sys", history=history)

    called_messages = client.complete.call_args.kwargs["messages"]
    assert called_messages[-1] == {"role": "user", "content": "follow-up question"}
    assert called_messages[0] == history[0]
