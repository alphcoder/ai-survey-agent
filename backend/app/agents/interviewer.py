from openai import AsyncOpenAI

from ..config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)

DEFAULT_SYSTEM_PROMPT = """Ты — профессиональный AI-интервьюер для маркетинговых и продуктовых исследований.

Правила:
- Задавай по одному вопросу за раз
- Слушай ответ респондента и адаптируй следующий вопрос
- Используй открытые вопросы для глубоких инсайтов
- Если ответ поверхностный — задай уточняющий вопрос
- Будь вежливым и нейтральным, не наводи на ответ
- Следуй цели исследования, но будь гибким
- Когда все ключевые темы раскрыты — заверши интервью"""


async def generate_question(
    goal: str,
    history: list[dict[str, str]],
    max_questions: int,
    custom_prompt: str | None = None,
) -> str:
    system = custom_prompt or DEFAULT_SYSTEM_PROMPT
    system += f"\n\nЦель исследования: {goal}"
    system += f"\nМаксимум вопросов: {max_questions}"
    system += f"\nЗадано вопросов: {len([m for m in history if m['role'] == 'assistant'])}"

    messages = [{"role": "system", "content": system}] + history

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        max_tokens=500,
        temperature=0.7,
    )
    return response.choices[0].message.content


async def generate_summary(
    goal: str,
    history: list[dict[str, str]],
) -> dict:
    prompt = f"""Проанализируй интервью и верни JSON:
{{
  "summary": "Краткое резюме интервью (3-5 предложений)",
  "key_insights": ["инсайт 1", "инсайт 2", ...],
  "sentiment": "positive/neutral/negative",
  "quotes": ["важная цитата 1", ...],
  "recommendations": ["рекомендация 1", ...]
}}

Цель исследования: {goal}"""

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": "\n".join(f"{m['role']}: {m['content']}" for m in history)},
    ]

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        max_tokens=1000,
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    import json
    return json.loads(response.choices[0].message.content)
