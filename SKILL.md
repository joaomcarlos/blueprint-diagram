---
name: blueprint-diagram
description: Use when asked to explain a process, architecture, or concept as a visual graph, flowchart, SVG schematic, or dark technical blueprint diagram, or to repair a blueprint with overlapping text or unclear connectors.
---

# Blueprint Diagram

Create SVG diagrams with the style in `blueprint.py`: dark grid paper, monospace type, cyan flow, purple feedback, amber human steps, green verified outputs. Content and layout belong in a separate script. Measure the text, connect the boxes, then check the rendered diagram.

## Workflow

1. **Model.** List stages, nodes, decision branches, edges, and genuine feedback loops. Check names, commands, and process claims against the supplied source. Reusing an old diagram supplies layout, not verified facts.
2. **Write.** Draft every label, subtitle, branch label, note, legend entry, and caption using the Wording rules below. Read them aloud and replace anything that sounds stiff or compressed. Finish this review before measuring the layout. Apply the same writing rules to the explanation delivered with the diagram.
3. **Budget.** Read `example.py`. Copy it into the output directory and add this skill directory to `sys.path` when importing `blueprint`. Set column widths and reserve routing lanes before placing nodes. Plan using the constraints below. Fit the canvas to the content.
4. **Build.** Use `node(..., h=None)` for wrapped, measured height and `decision(..., label=...)` for a diamond sized to its text. Keep returned shapes. Use `connect()` and `fan_out()` to derive endpoints. For `panel()`, use the returned content origin, or `return_shape=True` and its `content_top`.
5. **Preflight and render.** Run `python3 <skill-dir>/render.py <script.py> --svg <output.svg>`. `write()` checks geometry and refuses invalid export. Fix every reported issue together before rerunning. The renderer produces native-size and `-reading.png` (720px wide) previews.
6. **Review.** View both PNGs and complete [REVIEW.md](REVIEW.md). Check every text group and trace every arrow. Batch corrections by root cause: fix the common column width, padding, or routing lane rather than nudging individual labels. If the same class fails on the next pass, revise that layout budget before rendering again. Delivery requires a clean geometry gate AND a clean visual review.
7. **Deliver.** Link the `.svg`. Include the `.png` when requested. Follow the host's inline visualization requirements when showing the figure in chat.

## Wording

Write like a person explaining the process to a colleague. Use familiar words, active verbs, and short sentences. Name the action: "Water pushes potatoes through the blades" explains more than "Hydraulic cutting mechanism". Keep the technical facts and exact command names.

Use periods, commas, and ordinary words such as "and", "then", and "to". Diagram text must contain no em dashes, en dashes, semicolons, vertical bars, or middle-dot separators. `write()` rejects those characters. Replace plus signs, slashes, and arrow symbols used as shorthand with words. Put the flow arrows between boxes.

Read the labels aloud before rendering. Rewrite phrases such as "Verify and synthesize", "After cut", and "Supplier finishes cook/freeze" as "Check the result", "After cutting", and "Ready to send to restaurants". Remove stock introductions, promotional language, forced slogans, and repeated summaries. For a mechanism, say what moves and what acts on it. Use only facts supported by the sources.

## Layout constraints

| Element | Construction rule |
|---|---|
| Capitalization | Use sentence case for node labels, subtitles, decisions, branch labels, annotations, legends, and captions. Capitalize the first word of each independent label. Preserve acronyms and proper names. A wrapped continuation keeps the case of the original sentence. Structural titles, section headings, card headings, and rail headings use uppercase. Commands, API identifiers, model slugs, paths, and quoted source text retain their exact spelling. |
| Text | Keep body text at 20px and annotations at least 18px. Wrap at words or shorten copy. Enlarge the box/column/canvas to retain padding. Long identifiers need enough width or an explicit meaningful break. |
| Boxes | Use 24px content padding and at least 24px between shapes. 32 to 48px is the normal working gap. Measure height before setting the next row's y coordinate. Marker, heading, and subtitle share the same text indent. |
| Sections | Content starts below the measured header and metadata. Long tags move to a separate row. Reserve 64 to 90px between sections for clear arrows. |
| Decisions | Use short questions, with explicit `\n` for two lines. Fit all text corners inside the diamond slopes. Example: input at top, yes from right, no from bottom or left. |
| Connectors | Use orthogonal segments and exact named side ports. Leave/enter each port on its normal axis: left/right horizontally. Top/bottom vertically. Keep at least 24px before an elbow and 12px from unrelated shapes. |
| Branch labels | Label each outcome. Put labels beside a straight segment, at least 8px clear of the stroke and away from vertices/arrowheads. `connect(label=...)` centers on the longest horizontal segment. Vertical labels need `label_pos=(x, baseline_y)`. |
| Feedback | Reserve a dedicated 48 to 64px lane outside occupied content, plus separate space for its rotated label. Route back only when the process actually retries or feeds upstream. |
| Footer | Use measured `legend()` rows and its returned last baseline to place `caption()` below. Keep text and rails inside the canvas safe margin. |

## Helpers

| API | Purpose |
|---|---|
| `node(x,y,w,None,text,sub=...,marker=...)` | Wrap and measure height. Returns a shape with `x,y,w,h,right,bottom`. |
| `decision(cx,cy,label='OK?')` | Auto-size a decision. Returns a shape. Explicit `r` stays fixed and must fit. |
| `shape.port('left').xy` | Exact cardinal boundary point. |
| `connect(a,'right',b,'left',via=[...],label='Yes')` | Attach shape ports using deliberately reserved elbow coordinates. |
| `fan_out(source,targets,spine_x=...)` | Derive target centers and stub lengths from the shapes. |
| `check()` / `write(path)` | Collect geometry failures / export only after they pass. |

`header`, `panel`, `card`, `kv`, `text`, `rail`, `vlabel`, `legend`, and `caption` retain the shared visual style. Low-level `edge()` and legacy `fan()` are checked too. Their coordinates must still meet the port contract. `line()`/`bracket()` are decorative strokes and require visual review. The geometry gate checks text fit/clearance, node/panel bounds, orthogonality, endpoints, port axes, short segments, and arrow paths through unrelated nodes/text. Review handles arrow-to-arrow crossings, topology, optical balance, and readability.

## Maintenance

Run `python3 -m unittest -v test_blueprint.py` from this directory after changing helpers. Render and review both `example.py --svg factory.svg` and `t3-orchestration.py`. Pango/Cairo and `rsvg-convert` are required. Measurement uses the same font stack as the SVG so local font substitutions are accounted for. New visual idioms belong in the library. Retain its palette and type hierarchy.
