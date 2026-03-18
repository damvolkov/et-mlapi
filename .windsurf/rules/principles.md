---
description: Engineering philosophy and agent behavior constraints.
alwaysApply: true
---

# Principles

- Architecture = contract with reality. Enforce SOLID, hexagonal, low coupling regardless of author.
- Context engineering is non-negotiable. Output quality is bounded by input constraints.
- Local correctness ≠ global correctness. Evaluate every change against the whole system.
- Constraints enable speed. Well-defined boundaries = confident changes.
- Touch only requested files. No extra files, comments, or docs beyond task scope.
- Temp files: create → use → delete.
- Standard fix: only what is asked. Non-critical lateral: warn. Critical lateral: stop → explain → await.
- Concise, declarative, code-first output.
