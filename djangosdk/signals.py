from django.dispatch import Signal

agent_started = Signal()
"""
Sent when an agent begins processing a request.
kwargs: agent, prompt, model, provider
"""

agent_completed = Signal()
"""
Sent when an agent successfully completes a request.
kwargs: agent, response, model, provider
"""

agent_failed = Signal()
"""
Sent when an agent raises an exception.
kwargs: agent, exception, model, provider
"""

agent_failed_over = Signal()
"""
Sent when the failover mechanism switches providers.
kwargs: agent, from_provider, to_provider, reason
"""

cache_hit = Signal()
"""
Sent when a prompt cache hit occurs.
kwargs: agent, cache_read_tokens
"""

cache_miss = Signal()
"""
Sent when a prompt cache miss occurs.
kwargs: agent
"""
