from pathlib import Path

import openai
from openai import AsyncOpenAI

from amazon_deals_bot.config.settings import settings
from amazon_deals_bot.utils.logger import logger

_PROMPT_PATH = Path(__file__).parents[4] / "prompts" / "copy_v1.md"

_INPUT_COST_PER_TOKEN = 0.00000015
_OUTPUT_COST_PER_TOKEN = 0.0000006


class OpenAIClient:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_copy(
        self,
        deal_name: str,
        price: float,
        original_price: float,
        discount_pct: int,
        source: str,
        affiliate_url: str,
    ) -> str:
        template = _PROMPT_PATH.read_text(encoding="utf-8")
        prompt = (
            template
            .replace("{deal_name}", deal_name)
            .replace("{price}", f"{price:.2f}")
            .replace("{original_price}", f"{original_price:.2f}")
            .replace("{discount_pct}", str(discount_pct))
            .replace("{source}", source)
            .replace("{affiliate_url}", affiliate_url)
        )

        try:
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature,
            )
        except openai.OpenAIError as exc:
            logger.bind(event="openai_error", error=str(exc)).error("openai request failed")
            raise

        usage = response.usage
        logger.bind(
            event="openai_tokens",
            input=usage.prompt_tokens,
            output=usage.completion_tokens,
            model=settings.openai_model,
        ).info("copy generated")

        cost_usd = (
            usage.prompt_tokens * _INPUT_COST_PER_TOKEN
            + usage.completion_tokens * _OUTPUT_COST_PER_TOKEN
        )
        logger.bind(
            event="openai_cost",
            cost_usd=round(cost_usd, 8),
            daily_alert_usd=settings.openai_daily_cost_alert_usd,
            model=settings.openai_model,
        ).info("openai call cost")

        return response.choices[0].message.content.strip()