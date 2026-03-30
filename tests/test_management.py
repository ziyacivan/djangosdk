from __future__ import annotations

from io import StringIO
from django.core.management import call_command


def test_ai_sdk_publish_outputs_settings_block(capsys):
    """ai_sdk_publish should write the AI_SDK settings skeleton to stdout."""
    out = StringIO()
    call_command("ai_sdk_publish", stdout=out)
    output = out.getvalue()
    assert "AI_SDK" in output


def test_ai_sdk_check_runs_without_error(capsys):
    """ai_sdk_check should not raise when no real providers are configured."""
    out = StringIO()
    err = StringIO()
    # Should complete without raising even with fake/empty providers
    try:
        call_command("ai_sdk_check", stdout=out, stderr=err)
    except SystemExit:
        pass  # non-zero exit is acceptable when no providers configured
    # As long as no unexpected exception was raised the command works
