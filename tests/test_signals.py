from __future__ import annotations

import pytest
from djangosdk.agents.base import Agent
from djangosdk.signals import (
    agent_started,
    agent_completed,
    agent_failed,
    cache_hit,
    cache_miss,
)
from djangosdk.testing import FakeProvider, override_ai_provider


class SimpleAgent(Agent):
    provider = "fake"
    model = "fake-model"


def test_agent_started_signal_fires():
    received = []

    def handler(sender, agent, prompt, **kwargs):
        received.append(prompt)

    agent_started.connect(handler)
    try:
        fake = FakeProvider(text="OK")
        with override_ai_provider(fake):
            SimpleAgent().handle("Test signal")
        assert received == ["Test signal"]
    finally:
        agent_started.disconnect(handler)


def test_agent_completed_signal_fires():
    received = []

    def handler(sender, response, **kwargs):
        received.append(response.text)

    agent_completed.connect(handler)
    try:
        fake = FakeProvider(text="Done!")
        with override_ai_provider(fake):
            SimpleAgent().handle("Complete me")
        assert received == ["Done!"]
    finally:
        agent_completed.disconnect(handler)


def test_agent_failed_signal_fires():
    received = []

    def handler(sender, exception, **kwargs):
        received.append(str(exception))

    agent_failed.connect(handler)
    try:
        from djangosdk.exceptions import ProviderError
        bad = FakeProvider()
        bad.complete = lambda r: (_ for _ in ()).throw(ProviderError("boom"))

        with override_ai_provider(bad):
            with pytest.raises(ProviderError):
                SimpleAgent().handle("Fail me")

        assert len(received) == 1
        assert "boom" in received[0]
    finally:
        agent_failed.disconnect(handler)


def test_cache_miss_signal_fires_on_zero_cache_tokens():
    received = []

    def handler(sender, **kwargs):
        received.append(True)

    cache_miss.connect(handler)
    try:
        from djangosdk.agents.response import UsageInfo
        fake = FakeProvider(usage=UsageInfo(cache_read_tokens=0))
        with override_ai_provider(fake):
            SimpleAgent().handle("No cache")
        assert received == [True]
    finally:
        cache_miss.disconnect(handler)


def test_cache_hit_signal_fires_on_nonzero_cache_tokens():
    received = []

    def handler(sender, cache_read_tokens, **kwargs):
        received.append(cache_read_tokens)

    cache_hit.connect(handler)
    try:
        from djangosdk.agents.response import UsageInfo
        fake = FakeProvider(usage=UsageInfo(cache_read_tokens=100, total_tokens=110))
        with override_ai_provider(fake):
            SimpleAgent().handle("Cache hit")
        assert received == [100]
    finally:
        cache_hit.disconnect(handler)
