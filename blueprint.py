#!/usr/bin/env python3
"""blueprint.py — generate dark technical "blueprint figure" SVG diagrams.

The caller supplies CONTENT and LAYOUT; this module supplies the STYLE:
near-black grid paper, cyan flow lines, purple feedback rails, amber human
nodes, green shipped outputs, monospace type throughout.

Use named ports and measured heights; example.py is the complete template.
write() runs geometry checks before exporting. Render with render.py and
complete REVIEW.md before delivery. Text uses Pango, as does rsvg-convert.
"""
import html
from layout import (Box, Shape, Text, Route, LayoutError, PADDING, GAP,
                    text_width, text_box, wrap, check)

# ---------------------------------------------------------------- palette
C = dict(
    bg       = "#0B0F17",   # near-black navy paper
    grid_min = "#1A2436",   # fine grid line
    grid_maj = "#22304A",   # major grid line
    panel    = "#121A29",   # section frame fill
    node     = "#192634",   # node fill
    border   = "#2A3A55",   # node / panel border
    text     = "#DEE6F4",   # primary text
    dim      = "#7C89A4",   # secondary text
    faint    = "#5A6B82",   # annotations, side rails text
    cyan     = "#4ACAF0",   # agent / main flow
    cyan_hi  = "#4ED6FD",   # arrowheads, section numbers
    cyan_dim = "#2D758E",   # cyan borders
    purple   = "#AC83F6",   # feedback loops
    amber    = "#FDB147",   # human-in-the-loop
    amber_bg = "#2A2110",   # human node fill
    green    = "#4FC7AD",   # shipped / pass
)

FONT = "'JetBrains Mono','JetBrainsMono Nerd Font','Noto Sans Mono',monospace"
ROLE = dict(agent="cyan", human="amber", item="cyan", feedback="purple",
            shipped="green", plain="dim", flow="cyan", decision="cyan")

def _c(role):
    return C[ROLE.get(role, role)]

class Fig:
    def __init__(self, w=1200, h=2000):
        self.w, self.h = w, h
        self.parts = []
        self.shapes, self.texts, self.routes, self.problems = [], [], [], []
        self._owner = None

    def _shape(self, x, y, w, h, name, kind='node', content_top=0):
        shape = Shape(x, y, w, h, name, kind, content_top)
        self.shapes.append(shape)
        self._owner = shape
        return shape

    # ---------------------------------------------------------- internals
    def _add(self, s):
        self.parts.append(s)

    def _txt(self, x, y, s, size=20, fill=None, bold=False, ls=0, anchor="start",
             rotate=None, italic=False):
        s = str(s)
        self.texts.append(Text(s, text_box(x, y, s, size, bold, ls, anchor, rotate, italic), self._owner))
        fill = fill or C["text"]
        st = f"font-family:{FONT};font-size:{size}px;fill:{fill};"
        if bold: st += "font-weight:700;"
        if italic: st += "font-style:italic;"
        if ls: st += f"letter-spacing:{ls}px;"
        tr = f' transform="rotate({rotate} {x} {y})"' if rotate else ""
        self._add(f'<text x="{x}" y="{y}" style="{st}" text-anchor="{anchor}" xml:space="preserve"{tr}>'
                  f'{html.escape(s)}</text>')

    def _rich(self, x, y, segments, size=19, ls=0, anchor="start", rotate=None):
        """Measured rich text; retain a single SVG run for rotated captions."""
        total = sum(text_width(t[0], size, bool(t[2]) if len(t)>2 else False, ls) + ls
                    for t in segments) - ls
        origin = x - ({'start': 0, 'middle': total/2, 'end': total}[anchor])
        if rotate:
            self.problems.append('rotated rich text: use a plain rotated label')
        start = len(self.texts)
        for seg in segments:
            text, role = seg[:2]
            bold = bool(seg[2]) if len(seg)>2 else False
            self._txt(origin, y, text, size, _c(role) if role else C['dim'], bold, ls)
            origin += text_width(text, size, bold, ls) + ls
        pieces = self.texts[start:]
        if pieces:
            left,top=min(t.box.x for t in pieces),min(t.box.y for t in pieces)
            right,bottom=max(t.box.right for t in pieces),max(t.box.bottom for t in pieces)
            self.texts[start:] = [Text(''.join(t.label for t in pieces),Box(left,top,right-left,bottom-top),self._owner)]

    def text(self, x, y, s, size=20, fill=None, bold=False, ls=0,
             anchor="start", rotate=None, italic=False):
        """Public text primitive — annotations, captions, loose labels."""
        self._owner = None
        self._txt(x, y, s, size, fill, bold, ls, anchor, rotate, italic)

    def _polyline(self, pts, color, wdt=2.5, dash=None, glow=False):
        p = " ".join(f"{x},{y}" for x, y in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        g = f' filter="url(#glow)"' if glow else ""
        self._add(f'<polyline points="{p}" fill="none" stroke="{color}" '
                  f'stroke-width="{wdt}" stroke-linejoin="round"{d}{g}/>')

    @staticmethod
    def _arrowhead(x, y, dx, dy, color, size=13):
        """Filled triangle whose tip is (x,y), pointing along (dx,dy)."""
        import math
        n = math.hypot(dx, dy) or 1
        ux, uy = dx / n, dy / n          # unit dir
        px, py = -uy, ux                 # perpendicular
        bx, by = x - ux * size, y - uy * size
        p1 = f"{x},{y}"
        p2 = f"{bx + px * size * 0.42},{by + py * size * 0.42}"
        p3 = f"{bx - px * size * 0.42},{by - py * size * 0.42}"
        return f'<polygon points="{p1} {p2} {p3}" fill="{color}"/>'

    # ------------------------------------------------------------- header
    def header(self, kicker, title, subtitle, x=80, y=48, title_size=58):
        self._owner = None
        self._txt(x, y, kicker.upper(), size=20, fill=C['dim'], ls=3)
        self._txt(x, y+68, title.upper(), size=title_size, bold=True, ls=4)
        baseline = y+112
        for line in wrap(subtitle or '', self.w-2*x, 20):
            self._txt(x, baseline, line, size=20, fill=C['dim'])
            baseline += 28
        self._add(f'<rect x="{x}" y="{baseline-4}" width="120" height="4" fill="{C["cyan"]}"/>')
        return baseline+36

    # -------------------------------------------------------------- panel
    def panel(self, num, name, x, y, w, h, note=None, tag=None, return_shape=False):
        """Frame with measured heading/meta rows; returns safe content origin."""
        heading = num + '  /  ' + name.upper()
        meta = [v for v in (note, tag) if v]
        header_width = text_width(heading, 20, ls=2)
        meta_width = max((text_width(v, 18, italic=bool(note)) for v in meta), default=0)
        stacked = bool(meta) and (len(meta)>1 or header_width+meta_width+64 > w-2*PADDING)
        meta_lines = [line for m in meta for line in wrap(m, w-2*PADDING, 18)] if stacked else meta
        top = y + (84+26*(len(meta_lines)-1) if stacked else 64)
        shape = self._shape(x,y,w,h, name, 'panel', top)
        self._add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{C["panel"]}" fill-opacity="0.55" stroke="{C["border"]}" stroke-width="1.2"/>')
        self._rich(x+PADDING,y+36,[(num,'cyan',True),('  /  '+name.upper(),'dim')],size=20,ls=2)
        for i,m in enumerate(meta_lines):
            self._txt(x+PADDING if stacked else x+w-PADDING, y+62+i*26 if stacked else y+36,
                      m,size=18,fill=C['faint'],anchor='start' if stacked else 'end',italic=bool(note))
        self._owner = None
        return shape if return_shape else (x+PADDING, top)

    # --------------------------------------------------------------- node
    def node(self, x, y, w, h, text=None, lines=None, role="item",
             marker=None, sub=None, align="left", active=False):
        """Wrap words at the usable width. h=None measures the required height.
        Explicit heights remain fixed and are checked before export.
        Returns a shape with named side ports.
        """
        accent = _c(role)
        offset = 48 if marker or (not sub and role != 'plain') else PADDING
        available = w-offset-PADDING
        main_size = 22 if sub else 20
        main = [ln for part in (lines if lines is not None else [text or ''])
                for ln in wrap(part, available, main_size, bool(sub), 1 if sub else 0)]
        secondary = wrap(sub, available, 18) if sub else []
        baselines = [i*36 for i in range(len(main))]
        sub_baselines = [(len(main)-1)*36+34+i*30 for i in range(len(secondary))]
        bounds = [text_box(0,b,t,main_size,bool(sub),1 if sub else 0)
                  for t,b in zip(main,baselines)]
        bounds += [text_box(0,b,t,18) for t,b in zip(secondary,sub_baselines)]
        top = min((b.y for b in bounds), default=0)
        content_h = max((b.bottom for b in bounds), default=0)-top
        if h is None: h = content_h+2*PADDING
        shape = self._shape(x,y,w,h, text or ' / '.join(main))
        border = accent if active or role=='agent' else C['border']
        fill = C['amber_bg'] if active and role=='human' else C['node']
        self._add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{border}" stroke-width="1.4"/>')
        cy = y+h/2
        if marker:
            mx=x+25
            if marker=='square':
                self._add(f'<rect x="{mx-5}" y="{cy-5}" width="10" height="10" fill="{accent}"/>')
            else:
                pts=f'{mx},{cy-7} {mx+7},{cy} {mx},{cy+7} {mx-7},{cy}'
                self._add(f'<polygon points="{pts}" fill="{accent if marker != "decision" else "none"}" stroke="{accent}"/>')
        elif not sub and role != 'plain':
            self._add(f'<circle cx="{x+25}" cy="{cy}" r="4.5" fill="{accent}"/>')
        baseline = y+(h-content_h)/2-top
        tx = x+offset if align=='left' else x+offset+available/2
        anchor = 'start' if align=='left' else 'middle'
        for ln,b in zip(main,baselines):
            self._txt(tx,baseline+b,ln,size=main_size,bold=bool(sub),ls=1 if sub else 0,
                      fill=accent if active else C['text'],anchor=anchor)
        for ln,b in zip(secondary,sub_baselines):
            self._txt(tx,baseline+b,ln,size=18,fill=C['dim'],anchor=anchor)
        self._owner = None
        return shape

    def kv(self, x, y, w, h, left, right, role="item"):
        """Measured two-column row; leave a 24px gutter between values."""
        shape = self._shape(x,y,w,h,left+' / '+right)
        self._add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{C["node"]}" stroke="{C["border"]}" stroke-width="1.4"/>')
        if text_width(left,20)+text_width(right,18)+2*PADDING+GAP > w:
            self.problems.append(f'{shape.name}: key/value columns need a wider box or shorter copy')
        self._txt(x+PADDING,y+h/2+7,left,size=20,fill=_c(role) if role=='human' else C['text'])
        self._txt(x+w-PADDING,y+h/2+7,right,size=18,fill=C['dim'],anchor='end')
        self._owner = None
        return shape

    def card(self, x, y, w, h, head, lines):
        body=[ln for part in lines for ln in wrap(part,w-2*PADDING,20)]
        if h is None: h=78+len(body)*34
        shape=self._shape(x,y,w,h,head)
        self._add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{C["node"]}" stroke="{C["border"]}" stroke-width="1.4"/>')
        self._txt(x+PADDING,y+42,head,size=18,fill=C['dim'],ls=1)
        for i,ln in enumerate(body):
            self._txt(x+PADDING,y+78+i*34,ln,size=20)
        self._owner = None
        return shape

    def line(self, pts, color=None, wdt=1.6, dash=None):
        """Plain polyline, no arrowhead (brackets, connectors)."""
        self._polyline(pts, color or C["faint"], wdt, dash=dash)

    def bracket(self, x, y0, y1, tick=8, color=None):
        """Left square bracket spanning y0→y1 at x (ladder/list grouping)."""
        c = color or C["cyan_dim"]
        self._polyline([(x + tick, y0), (x, y0), (x, y1), (x + tick, y1)], c, 1.6)

    def decision(self, cx, cy, r=None, label='OK?'):
        """Measured diamond. r=None fits every label corner inside its slopes."""
        lines=str(label).split('\n')
        baselines=[6+(i-(len(lines)-1)/2)*26 for i in range(len(lines))]
        boxes=[text_box(0,y,t,18,anchor='middle') for t,y in zip(lines,baselines)]
        required=max((abs(px)+abs(py)+14 for b in boxes
                      for px,py in [(b.x,b.y),(b.right,b.y),(b.x,b.bottom),(b.right,b.bottom)]),default=60)
        if r is None: r=max(60,required)
        shape=self._shape(cx-r,cy-r,2*r,2*r,label,'decision')
        pts=f'{cx},{cy-r} {cx+r},{cy} {cx},{cy+r} {cx-r},{cy}'
        self._add(f'<polygon points="{pts}" fill="{C["bg"]}" stroke="{C["dim"]}" stroke-width="1.6"/>')
        for t,y in zip(lines,baselines):
            self._txt(cx,cy+y,t,size=18,fill=C['dim'],anchor='middle')
        self._owner = None
        return shape

    # -------------------------------------------------------------- edges
    def arrow(self, x0, y0, x1, y1, kind='flow', wdt=3):
        return self.edge([(x0,y0),(x1,y1)],kind=kind,wdt=wdt)

    def edge(self, pts, kind='flow', dashed=False, wdt=2.5, label=None, label_pos=None):
        """Orthogonal path. Endpoints must be named shape ports at export."""
        self._owner = None
        pts=list(pts)
        if len(pts)<2: raise ValueError('An edge needs at least two points')
        self.routes.append(Route(pts, f'edge {len(self.routes)+1}'))
        self._polyline(pts,_c(kind),wdt,dash='7 7' if dashed else None)
        (x0,y0),(x1,y1)=pts[-2:]
        self._add(self._arrowhead(x1,y1,x1-x0,y1-y0,_c(kind),size=12))
        if label:
            horizontal=[(a,b) for a,b in zip(pts,pts[1:]) if a[1]==b[1]]
            if label_pos:
                lx,ly=label_pos
            elif horizontal:
                a,b=max(horizontal,key=lambda ab: abs(ab[0][0]-ab[1][0]))
                lx,ly=(a[0]+b[0])/2,a[1]-16
                if text_width(label,17)+2*GAP>abs(a[0]-b[0]):
                    self.problems.append(f'edge label {label!r}: segment needs room for label and elbow clearance')
            else:
                self.problems.append(f'edge label {label!r}: supply label_pos beside vertical segment')
                lx,ly=pts[0]
            self._txt(lx,ly,label,size=17,fill=C['dim'],anchor='middle')

    def connect(self, source, source_side, target, target_side, via=None, **kwargs):
        """Connect exact side ports. via lists deliberate gutter elbows."""
        return self.edge([source.port(source_side).xy,*(via or []),target.port(target_side).xy],**kwargs)

    def fan_out(self, source, targets, spine_x, kind='flow'):
        """Rightward fan. Target ports and stub lengths come from shapes."""
        sx,sy=source.port('right').xy
        for target in targets:
            tx,ty=target.port('left').xy
            pts=[(sx,sy),(spine_x,sy)]
            if ty != sy: pts.append((spine_x,ty))
            pts.append((tx,ty))
            self.edge(pts,kind=kind)

    def fan(self, x0, trunk_y, spine_x, targets_y, kind='flow', stub=26):
        """Legacy coordinate fan; endpoints and stubs are still validated."""
        for ty in targets_y:
            pts=[(x0,trunk_y),(spine_x,trunk_y)]
            if ty != trunk_y: pts.append((spine_x,ty))
            pts.append((spine_x+stub,ty))
            self.edge(pts,kind=kind)

    # ----------------------------------------------------------- side rails
    def rail(self, pts, label, label_xy, kind='feedback', wdt=3):
        self.edge(pts,kind=kind,wdt=wdt)
        lx,ly=label_xy
        self._txt(lx,ly,label.upper(),size=18,fill=C['purple'],ls=1,anchor='middle',rotate=-90)

    def vlabel(self, x, y, text, fill=None, size=17):
        """Rotated -90 annotation (e.g. 'fix · review · triage' beside a loop)."""
        self._txt(x, y, text, size=size, fill=fill or C["faint"],
                  anchor="middle", rotate=-90, italic=True)

    # ------------------------------------------------------------- footer
    def legend(self, x, y, items):
        """Measured legend rows; returns the last baseline."""
        self._owner = None
        cursor = x
        for role,label in items:
            width = text_width('●  '+label,18)+32
            if cursor+width > self.w-80:
                cursor=x
                y+=36
            self._rich(cursor,y,[('●  ',role),(label,'dim')],size=18)
            cursor+=width
        return y

    def caption(self, x, y, segments):
        """Caption line; segments = [(text, role_or_color|None)]."""
        self._rich(x, y, [(t, r) for t, r in segments], size=20)

    def glyph_legend(self, x, y, items):
        """Marker key inside a panel, e.g. [('◆','agent'),('■','deterministic')].
        Glyphs: ◆ agent-diamond, ■ deterministic-square, ◇ decision."""
        segs = []
        for glyph, label in items:
            role = {"◆": "cyan", "■": "dim", "◇": "dim"}.get(glyph, "dim")
            segs += [(glyph + " ", role), (label + "    ", "dim")]
        self._rich(x, y, segs, size=18)

    # --------------------------------------------------------------- glue
    def check(self):
        """Return all actionable layout failures without writing an artifact."""
        return check(self)

    def write(self, path):
        issues = self.check()
        if issues:
            raise LayoutError('Layout review failed:\n- ' + '\n- '.join(issues))
        defs = f'''<defs>
  <pattern id="gmin" width="26" height="26" patternUnits="userSpaceOnUse">
    <path d="M26 0H0V26" fill="none" stroke="{C['grid_min']}" stroke-width="0.6"/>
  </pattern>
  <pattern id="gmaj" width="130" height="130" patternUnits="userSpaceOnUse">
    <path d="M130 0H0V130" fill="none" stroke="{C['grid_maj']}" stroke-width="0.9"/>
  </pattern>
  <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="3.5" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>'''
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}">'
               f'{defs}'
               f'<rect width="{self.w}" height="{self.h}" fill="{C["bg"]}"/>'
               f'<rect width="{self.w}" height="{self.h}" fill="url(#gmin)"/>'
               f'<rect width="{self.w}" height="{self.h}" fill="url(#gmaj)"/>'
               + "".join(self.parts) + "</svg>")
        with open(path, "w") as fh:
            fh.write(svg)
        return path


# ------------------------------------------------------- layout helpers
def cols(x, w, n, gap):
    """x positions of n equal columns inside (x,w)."""
    cw = (w - gap * (n - 1)) / n
    return [x + i * (cw + gap) for i in range(n)], cw

def rows(y, h, n, gap):
    """y positions of n equal rows inside (y,h)."""
    rh = (h - gap * (n - 1)) / n
    return [y + i * (rh + gap) for i in range(n)], rh
