import os
import asyncio

from openai import AsyncOpenAI, APITimeoutError


_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=os.environ["VLLM_BASE_URL"],
            api_key="unused",  # vLLM doesn't require a real key
            timeout=120.0,
        )
    return _client


async def complete(
    messages: list[dict],
    temperature: float = 0.7,
) -> dict:
    """Call the vLLM inference service and return the response with token metadata."""
    client = _get_client()
    model = os.environ.get("VLLM_MODEL", "ibm-granite/granite-3.1-8b-instruct")

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            choice = response.choices[0]
            return {
                "content": choice.message.content,
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
                "model": response.model,
            }
        except APITimeoutError as e:
            last_error = e
            if attempt == 0:
                await asyncio.sleep(2)

    raise last_error
