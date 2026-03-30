"""Tests for analytics/cost.py."""
from __future__ import annotations

from decimal import Decimal
import pytest


# ===========================================================================
# calculate_cost()
# ===========================================================================

class TestCalculateCost:
    def test_gpt4o_cost(self):
        from django_ai_sdk.analytics.cost import calculate_cost

        cost = calculate_cost("gpt-4o", prompt_tokens=1_000_000, completion_tokens=0)
        assert cost == Decimal("2.5")

    def test_gpt4o_output_cost(self):
        from django_ai_sdk.analytics.cost import calculate_cost

        cost = calculate_cost("gpt-4o", prompt_tokens=0, completion_tokens=1_000_000)
        assert cost == Decimal("10.0")

    def test_claude_cost(self):
        from django_ai_sdk.analytics.cost import calculate_cost

        cost = calculate_cost("claude-3-7-sonnet", prompt_tokens=1_000_000, completion_tokens=0)
        assert cost == Decimal("3.0")

    def test_unknown_model_returns_zero_cost(self):
        from django_ai_sdk.analytics.cost import calculate_cost

        cost = calculate_cost("unknown-model-xyz", prompt_tokens=1_000, completion_tokens=500)
        assert cost == Decimal("0")

    def test_small_call_has_sub_cent_cost(self):
        from django_ai_sdk.analytics.cost import calculate_cost

        cost = calculate_cost("gpt-4o-mini", prompt_tokens=100, completion_tokens=50)
        assert cost < Decimal("0.01")
        assert cost > Decimal("0")

    def test_model_matching_is_case_insensitive(self):
        from django_ai_sdk.analytics.cost import calculate_cost

        cost_lower = calculate_cost("gpt-4o", prompt_tokens=1000, completion_tokens=0)
        cost_upper = calculate_cost("GPT-4O", prompt_tokens=1000, completion_tokens=0)
        assert cost_lower == cost_upper

    def test_deepseek_r1_cost(self):
        from django_ai_sdk.analytics.cost import calculate_cost

        cost = calculate_cost("deepseek-reasoner", prompt_tokens=1_000_000, completion_tokens=0)
        assert cost == Decimal("0.55")

    def test_o3_cost(self):
        from django_ai_sdk.analytics.cost import calculate_cost

        cost = calculate_cost("o3", prompt_tokens=0, completion_tokens=1_000_000)
        assert cost == Decimal("40.0")


# ===========================================================================
# cost_report()
# ===========================================================================

@pytest.mark.django_db
class TestCostReport:
    def _create_messages(self):
        from django_ai_sdk.models.conversation import Conversation
        from django_ai_sdk.models.message import Message

        conv_openai = Conversation.objects.create(
            agent_class="TestAgent", provider="openai", model="gpt-4o"
        )
        conv_anthropic = Conversation.objects.create(
            agent_class="TestAgent", provider="anthropic", model="claude-3-7-sonnet"
        )

        # Assistant messages with token info
        Message.objects.create(
            conversation=conv_openai,
            role=Message.Role.ASSISTANT,
            content="Response",
            prompt_tokens=1000,
            completion_tokens=200,
        )
        Message.objects.create(
            conversation=conv_anthropic,
            role=Message.Role.ASSISTANT,
            content="Response",
            prompt_tokens=500,
            completion_tokens=100,
        )
        return conv_openai, conv_anthropic

    def test_report_contains_provider_keys(self):
        from django_ai_sdk.analytics.cost import cost_report

        self._create_messages()
        report = cost_report(days=1)

        assert "openai" in report
        assert "anthropic" in report

    def test_report_total_tokens_is_sum(self):
        from django_ai_sdk.analytics.cost import cost_report

        self._create_messages()
        report = cost_report(days=1)

        assert report["openai"]["total_tokens"] == 1200  # 1000 + 200
        assert report["anthropic"]["total_tokens"] == 600

    def test_report_total_usd_is_positive(self):
        from django_ai_sdk.analytics.cost import cost_report

        self._create_messages()
        report = cost_report(days=1)

        assert report["openai"]["total_usd"] > 0
        assert report["anthropic"]["total_usd"] > 0

    def test_report_uses_cost_usd_when_present(self):
        from django_ai_sdk.models.conversation import Conversation
        from django_ai_sdk.models.message import Message
        from django_ai_sdk.analytics.cost import cost_report

        conv = Conversation.objects.create(
            agent_class="TestAgent", provider="openai", model="gpt-4o"
        )
        # Message with pre-computed cost_usd
        Message.objects.create(
            conversation=conv,
            role=Message.Role.ASSISTANT,
            content="Response",
            cost_usd=Decimal("1.23456789"),
        )

        report = cost_report(days=1)
        # Should use the stored cost_usd directly
        assert abs(report["openai"]["total_usd"] - 1.23456789) < 0.0001

    def test_report_empty_when_no_messages(self):
        from django_ai_sdk.analytics.cost import cost_report

        report = cost_report(days=1)
        assert report == {}
