# blueprint-diagram

An agent skill that generates dark technical "blueprint" SVG figures — near-black
grid paper, monospace type, numbered section frames, cyan flow lines, purple
feedback rails, amber human-in-the-loop nodes, green shipped outputs.

The style is encoded in `blueprint.py` + `layout.py`; the agent supplies only
content and layout intent. `SKILL.md` tells the agent when and how to use it.

## Install

Clone into your agent's skills directory:

```bash
git clone https://github.com/joaomcarlos/blueprint-diagram ~/.config/devin/skills/blueprint-diagram
```

Works with any runtime that reads `SKILL.md` skills (`~/.config/devin/skills/`,
`~/.claude/skills/`, `~/.agents/skills/`).

## Files

- `SKILL.md` — trigger conditions, design language, workflow (render-and-look required)
- `blueprint.py` — drawing primitives (panels, nodes, cards, ladders, edges, fans, rails)
- `layout.py` — measured layout and geometry validation (export gate)
- `render.py` — SVG → PNG previews via `rsvg-convert`
- `test_blueprint.py` — 21 regression cases
- `example.py` → `factory.svg/png` — the reference figure (software factory)
- `t3-orchestration.py` → `t3-orchestration.svg/png` — second worked example
- `REVIEW.md` — notes from the skill's own repair review
