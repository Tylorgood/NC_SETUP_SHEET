from __future__ import annotations

import re

from ..models import ParsedInstructions


class PlainEnglishInstructionParser:
    name = "plain-english-v0"
    family = "instruction_parser"

    def parse(self, text: str) -> ParsedInstructions:
        parsed = ParsedInstructions(raw=text or "")
        if not text:
            return parsed

        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]
        for sentence in sentences:
            lower = sentence.lower()
            if any(word in lower for word in ["must", "never", "do not", "don't", "shall", "require"]):
                parsed.constraints.append(sentence)
            elif any(word in lower for word in ["add", "change", "revise", "update", "verify", "check", "use", "generate"]):
                parsed.actions.append(sentence)
            else:
                parsed.notes.append(sentence)

            for machine in ["PR160P4", "trunnion", "router", "lathe", "waterjet", "Haas"]:
                if machine.lower() in lower:
                    parsed.machines.append(machine)
            for control in ["Haas", "Fanuc", "Siemens", "Heidenhain"]:
                if control.lower() in lower:
                    parsed.controls.append(control)

        parsed.machines = sorted(set(parsed.machines))
        parsed.controls = sorted(set(parsed.controls))
        return parsed
