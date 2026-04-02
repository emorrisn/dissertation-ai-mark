import re
import logging

logger = logging.getLogger(__name__)

class Sanitiser:
    def __init__(self, strict: bool = True):
        self.strict = strict

        # High-risk prompt injection patterns
        self.injection_patterns = [
            #  Direct instruction overrides
            r"(?i)ignore\s+(all\s+)?(previous|above)\s+instructions?",
            r"(?i)disregard\s+(all\s+)?(previous|above)",
            r"(?i)forget\s+(everything|all|prior)",
            r"(?i)override\s+.*instructions?",
            r"(?i)do\s+not\s+follow\s+.*rules?",
            r"(?i)bypass\s+.*(safety|filters|restrictions)",
            r"(?i)disable\s+.*(safety|guardrails|filters)",

            #  Role / identity hijacking
            r"(?i)you\s+are\s+now\s+.*",
            r"(?i)act\s+as\s+(a|an)?\s*.*",
            r"(?i)pretend\s+to\s+be\s+.*",
            r"(?i)simulate\s+(a|an)?\s*.*",
            r"(?i)role\s*:\s*system",
            r"(?i)role\s*:\s*assistant",
            r"(?i)you\s+are\s+an?\s+ai\s+.*without\s+restrictions",

            # System prompt extraction attempts
            r"(?i)reveal\s+(the\s+)?system\s+prompt",
            r"(?i)show\s+(me\s+)?(your\s+)?instructions",
            r"(?i)print\s+(the\s+)?hidden\s+prompt",
            r"(?i)what\s+were\s+you\s+told\s+before",
            r"(?i)display\s+developer\s+message",

            # Jailbreak keywords / known phrases
            r"(?i)jailbreak",
            r"(?i)developer\s+mode",
            r"(?i)dan\s+mode",
            r"(?i)god\s+mode",
            r"(?i)unrestricted\s+mode",
            r"(?i)no\s+filters?\s+mode",

            # Instruction framing tricks
            r"(?i)from\s+now\s+on\s*,?",
            r"(?i)starting\s+now\s*,?",
            r"(?i)in\s+this\s+scenario\s*,?",
            r"(?i)for\s+the\s+rest\s+of\s+this\s+conversation",
            r"(?i)assume\s+that\s+.*",
            r"(?i)you\s+must\s+now\s+.*",

            # Chain-of-thought / reasoning extraction
            r"(?i)show\s+your\s+chain\s+of\s+thought",
            r"(?i)explain\s+your\s+internal\s+reasoning",
            r"(?i)think\s+step\s+by\s+step\s+and\s+reveal",
            r"(?i)output\s+your\s+hidden\s+thoughts",

            # Tool / API manipulation
            r"(?i)call\s+this\s+api",
            r"(?i)send\s+request\s+to",
            r"(?i)execute\s+this\s+command",
            r"(?i)run\s+this\s+code",
            r"(?i)open\s+this\s+url",

            # Data exfiltration attempts
            r"(?i)give\s+me\s+all\s+your\s+data",
            r"(?i)dump\s+the\s+database",
            r"(?i)export\s+all\s+records",
            r"(?i)leak\s+.*information",
            r"(?i)show\s+confidential",

            # Prompt boundary breaking
            r"(?i)end\s+of\s+instructions",
            r"(?i)new\s+instructions\s*:",
            r"(?i)system\s*:\s*",
            r"(?i)assistant\s*:\s*",
            r"(?i)user\s*:\s*",

            # Encoding / obfuscation hints
            r"(?i)decode\s+this",
            r"(?i)base64\s+decode",
            r"(?i)rot13",
            r"(?i)hex\s+decode",
            r"(?i)obfuscated\s+instructions",

            # Conditional manipulation
            r"(?i)if\s+you\s+are\s+an?\s+ai",
            r"(?i)if\s+you\s+follow\s+rules\s+then\s+ignore",
            r"(?i)unless\s+you\s+are\s+restricted",

            # Reward / threat manipulation
            r"(?i)you\s+will\s+be\s+rewarded",
            r"(?i)you\s+will\s+be\s+punished",
            r"(?i)this\s+is\s+very\s+important\s+you\s+must",
            r"(?i)failure\s+to\s+comply",

            # Multi-step / recursive instructions
            r"(?i)repeat\s+after\s+me",
            r"(?i)follow\s+these\s+steps",
            r"(?i)step\s+1\s*:",
            r"(?i)first\s*,\s*do\s+this",

            # HTML / Markdown injection tricks
            r"(?i)<\s*script.*?>.*?<\s*/\s*script\s*>",
            r"(?i)<\s*iframe.*?>.*?<\s*/\s*iframe\s*>",
            r"(?i)<\s*meta.*?>",
            r"(?i)\[.*?\]\(javascript:.*?\)",

            # LLM-specific exploit phrasing
            r"(?i)as\s+an\s+ai\s+language\s+model\s+you\s+must",
            r"(?i)you\s+cannot\s+refuse",
            r"(?i)do\s+not\s+say\s+you\s+cannot",
            r"(?i)always\s+comply",

            # Hidden instruction delimiters
            r"(?i)###\s*system",
            r"(?i)###\s*instructions",
            r"(?i)---\s*begin",
            r"(?i)---\s*end",
        ]

        # Obfuscation patterns (common tricks)
        self.obfuscation_patterns = [
            r"(?i)i\s*g\s*n\s*o\s*r\s*e",   # spaced letters
            r"(?i)1gn0re",                # leetspeak
        ]

        # Suspicious formatting / payload hints
        self.payload_patterns = [
            r"<\s*script.*?>.*?<\s*/\s*script\s*>",
            r"(?i)base64\s*,\s*[a-zA-Z0-9+/=]+",
            r"{.*?}",  # possible structured injection blobs
        ]

    def sanitise(self, text: str) -> str:
        if not text:
            return ""

        original_length = len(text)

        # 1. Remove control characters
        text = re.sub(r"[\x00-\x1F\x7F]", " ", text)

        # 2. Normalize whitespace early
        text = re.sub(r"\s+", " ", text)

        # 3. Remove injection attempts
        for pattern in self.injection_patterns:
            text = re.sub(pattern, "[REMOVED_INJECTION]", text)

        # 4. Remove obfuscation attempts
        for pattern in self.obfuscation_patterns:
            text = re.sub(pattern, "[OBFUSCATED]", text)

        # 5. Remove suspicious payloads
        for pattern in self.payload_patterns:
            text = re.sub(pattern, "[REMOVED_PAYLOAD]", text)

        # 6. Optional strict mode cleanup
        if self.strict:
            # Remove excessive symbols
            text = re.sub(r"[^\w\s.,!?@#:/\-()\[\]]", "", text)

        # 7. Length cap
        MAX_LEN = 50000
        if len(text) > MAX_LEN:
            logger.warning("Text truncated due to size limit.")
            text = text[:MAX_LEN] + "..."

        logger.debug(f"Sanitized text from {original_length} → {len(text)} chars")

        return text.strip()