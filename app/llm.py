from anthropic import AsyncAnthropic

from app.config import settings
from app.schemas import ExtractionResult

EXTRACTION_TOOL = {
    "name": "record_obligations",
    "description": "Record the regulatory obligations found in the text, if any.",
    "input_schema": {
        "type": "object",
        "properties": {
            "obligations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "obligation": {
                            "type": "string",
                            "description": "The specific obligation or requirement being imposed",
                        },
                        "applies_to": {
                            "type": "string",
                            "description": "Who the obligation applies to, e.g. 'UK-authorised payment firms'",
                        },
                        "deadline": {
                            "type": ["string", "null"],
                            "description": "Compliance deadline if explicitly stated, else null",
                        },
                    },
                    "required": ["obligation", "applies_to", "deadline"],
                },
            }
        },
        "required": ["obligations"],
    },
}

SYSTEM_PROMPT = (
    "You are a regulatory analyst. Given a single item from a financial regulator's news or "
    "publications feed, extract every concrete obligation it imposes on firms. An obligation is "
    "a specific, actionable requirement — not general commentary or background. If the text "
    "contains no concrete obligation, return an empty list. Do not invent deadlines or scope "
    "that isn't stated in the text."
)


def _client() -> AsyncAnthropic:
    return AsyncAnthropic(api_key=settings.anthropic_api_key)


async def extract_obligations(title: str, content: str) -> ExtractionResult:
    client = _client()
    message = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "record_obligations"},
        messages=[{"role": "user", "content": f"Title: {title}\n\nText: {content}"}],
    )
    for block in message.content:
        if block.type == "tool_use" and block.name == "record_obligations":
            return ExtractionResult.model_validate(block.input)
    return ExtractionResult(obligations=[])
