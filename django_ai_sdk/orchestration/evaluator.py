from __future__ import annotations

from typing import Any


class EvaluatorOptimizer:
    """
    Evaluator-Optimizer agentic pattern.

    Runs a generator agent, evaluates its output with an evaluator agent,
    and iterates until the evaluator approves or ``max_iterations`` is reached.

    The evaluator receives a prompt of the form::

        "Evaluate this output and respond with APPROVED if it meets quality
        standards, or provide specific feedback for improvement:\\n\\n{output}"

    The loop continues until the evaluator's response contains ``APPROVED``
    (case-insensitive) or ``max_iterations`` is exhausted. The last generator
    response is always returned.

    Example::

        optimizer = EvaluatorOptimizer(
            generator=WritingAgent(),
            evaluator=CriticAgent(),
            max_iterations=3,
        )
        result = optimizer.run("Write a blog post about AI")
        print(result.text)
    """

    def __init__(self, generator, evaluator, max_iterations: int = 3) -> None:
        self.generator = generator
        self.evaluator = evaluator
        self.max_iterations = max_iterations

    def run(self, prompt: str, **kwargs) -> Any:
        """
        Run the evaluator-optimizer loop synchronously.

        Returns the final ``AgentResponse`` from the generator.
        """
        current_prompt = prompt
        last_response = None

        for _ in range(self.max_iterations):
            last_response = self.generator.handle(current_prompt, **kwargs)
            eval_prompt = (
                f"Evaluate this output and respond with APPROVED if it meets quality standards, "
                f"or provide specific feedback for improvement:\n\n{last_response.text}"
            )
            eval_response = self.evaluator.handle(eval_prompt)

            if "APPROVED" in eval_response.text.upper():
                break

            current_prompt = (
                f"Improve the following based on this feedback:\n"
                f"Feedback: {eval_response.text}\n\n"
                f"Original output:\n{last_response.text}"
            )

        return last_response

    async def arun(self, prompt: str, **kwargs) -> Any:
        """
        Run the evaluator-optimizer loop asynchronously.

        Returns the final ``AgentResponse`` from the generator.
        """
        current_prompt = prompt
        last_response = None

        for _ in range(self.max_iterations):
            last_response = await self.generator.ahandle(current_prompt, **kwargs)
            eval_prompt = (
                f"Evaluate this output and respond with APPROVED if it meets quality standards, "
                f"or provide specific feedback for improvement:\n\n{last_response.text}"
            )
            eval_response = await self.evaluator.ahandle(eval_prompt)

            if "APPROVED" in eval_response.text.upper():
                break

            current_prompt = (
                f"Improve the following based on this feedback:\n"
                f"Feedback: {eval_response.text}\n\n"
                f"Original output:\n{last_response.text}"
            )

        return last_response
