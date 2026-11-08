"""Measured text and geometry checks shared by the blueprint primitives.

Pango is the text engine used by rsvg-convert. Measuring with the same font
stack catches system font substitutions as well as long labels.
"""
import ctypes as ct
from ctypes.util import find_library
from dataclasses import dataclass
from functools import lru_cache
import math

FONT_FAMILY = 'JetBrains Mono,JetBrainsMono Nerd Font,Noto Sans Mono,monospace'
PADDING = 24
GAP = 24
TEXT_GAP = 8
ROUTE_CLEARANCE = 12


class LayoutError(ValueError):
    pass


class _Rect(ct.Structure):
    _fields_ = [(n, ct.c_int) for n in ('x', 'y', 'width', 'height')]


def _bind(lib, name, result, *args):
    fn = getattr(lib, name)
    fn.restype, fn.argtypes = result, list(args)
    return fn


class _Pango:
    def __init__(self):
        try:
            p = ct.CDLL(find_library('pango-1.0') or 'libpango-1.0.so.0')
            pc = ct.CDLL(find_library('pangocairo-1.0') or 'libpangocairo-1.0.so.0')
            g = ct.CDLL(find_library('gobject-2.0') or 'libgobject-2.0.so.0')
        except OSError as e:
            raise RuntimeError('Blueprint text measurement requires Pango and Cairo (also used by rsvg-convert).') from e
        ptr, integer = ct.c_void_p, ct.c_int
        fontmap = _bind(pc, 'pango_cairo_font_map_get_default', ptr)()
        self.context = _bind(p, 'pango_font_map_create_context', ptr, ptr)(fontmap)
        self.new = _bind(p, 'pango_layout_new', ptr, ptr)
        self.desc = _bind(p, 'pango_font_description_from_string', ptr, ct.c_char_p)
        self.size = _bind(p, 'pango_font_description_set_absolute_size', None, ptr, ct.c_double)
        self.setfont = _bind(p, 'pango_layout_set_font_description', None, ptr, ptr)
        self.text = _bind(p, 'pango_layout_set_text', None, ptr, ct.c_char_p, integer)
        self.extents = _bind(p, 'pango_layout_get_pixel_extents', None, ptr, ct.POINTER(_Rect), ct.POINTER(_Rect))
        self.baseline = _bind(p, 'pango_layout_get_baseline', integer, ptr)
        self.free = _bind(p, 'pango_font_description_free', None, ptr)
        self.unref = _bind(g, 'g_object_unref', None, ptr)

    def measure(self, text, size, bold, italic):
        desc = self.desc((FONT_FAMILY + (' Bold' if bold else '') + (' Italic' if italic else '')).encode())
        self.size(desc, size * 1024)
        layout = self.new(self.context)
        try:
            self.setfont(layout, desc)
            self.text(layout, text.encode(), -1)
            ink, logical = _Rect(), _Rect()
            self.extents(layout, ct.byref(ink), ct.byref(logical))
            baseline = self.baseline(layout) / 1024
            return logical.width, ink.x, ink.y - baseline, ink.width, ink.height
        finally:
            self.unref(layout)
            self.free(desc)


@lru_cache(maxsize=1)
def _engine():
    return _Pango()


@lru_cache(maxsize=4096)
def metrics(text, size=20, bold=False, italic=False):
    return _engine().measure(text, size, bold, italic)


def text_width(text, size=20, bold=False, ls=0, italic=False):
    return metrics(text, size, bold, italic)[0] + max(0, len(text) - 1) * ls


def wrap(text, width, size=20, bold=False, ls=0):
    """Wrap at word boundaries; keep explicit line breaks and identifiers."""
    lines = []
    for paragraph in str(text).split('\n'):
        line = ''
        for word in paragraph.split():
            candidate = f'{line} {word}' if line else word
            if line and text_width(candidate, size, bold, ls) > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self): return self.x + self.w
    @property
    def bottom(self): return self.y + self.h

    def inflate(self, n):
        return Box(self.x-n, self.y-n, self.w+2*n, self.h+2*n)

    def contains(self, other, pad=0):
        return (other.x >= self.x+pad-0.1 and other.y >= self.y+pad-0.1
                and other.right <= self.right-pad+0.1 and other.bottom <= self.bottom-pad+0.1)

    def overlaps(self, other):
        return (self.x < other.right-0.1 and other.x < self.right-0.1
                and self.y < other.bottom-0.1 and other.y < self.bottom-0.1)


@dataclass(frozen=True, eq=False)
class Shape(Box):
    # Identity matters: two coincident shapes are still an overlap.
    name: str = ''
    kind: str = 'node'
    content_top: float = 0

    def port(self, side):
        points = {'left': (self.x, self.y+self.h/2),
                  'right': (self.right, self.y+self.h/2),
                  'top': (self.x+self.w/2, self.y),
                  'bottom': (self.x+self.w/2, self.bottom)}
        if side not in points:
            raise ValueError(f'Unknown port {side!r}; use left/right/top/bottom')
        return Port(self, side, points[side])


@dataclass(frozen=True)
class Port:
    shape: Shape
    side: str
    xy: tuple

    @property
    def normal(self):
        return {'left': (-1, 0), 'right': (1, 0), 'top': (0, -1), 'bottom': (0, 1)}[self.side]


@dataclass
class Text:
    label: str
    box: Box
    owner: Shape | None = None


@dataclass
class Route:
    pts: list
    name: str


def text_box(x, y, text, size, bold=False, ls=0, anchor='start', rotate=None, italic=False):
    advance, ix, iy, iw, ih = metrics(text, size, bold, italic)
    extra = max(0, len(text)-1) * ls
    width = advance + extra
    shift = {'start': 0, 'middle': -width/2, 'end': -width}[anchor]
    # Use ink extents, including italic overhangs, with a small renderer allowance.
    b = Box(x+shift+ix-1, y+iy-1, iw+extra+2, ih+2)
    if not rotate:
        return b
    a = math.radians(rotate)
    pts = [(x+(px-x)*math.cos(a)-(py-y)*math.sin(a),
            y+(px-x)*math.sin(a)+(py-y)*math.cos(a))
           for px, py in [(b.x,b.y),(b.right,b.y),(b.right,b.bottom),(b.x,b.bottom)]]
    xx, yy = zip(*pts)
    return Box(min(xx), min(yy), max(xx)-min(xx), max(yy)-min(yy))


def segment_hits(a, b, box):
    if a[0] == b[0]:
        return box.x < a[0] < box.right and min(a[1],b[1]) < box.bottom and max(a[1],b[1]) > box.y
    if a[1] == b[1]:
        return box.y < a[1] < box.bottom and min(a[0],b[0]) < box.right and max(a[0],b[0]) > box.x
    return False  # diagonals are reported separately


def check(fig):
    errors = list(fig.problems)
    canvas = Box(0, 0, fig.w, fig.h)
    panels = [s for s in fig.shapes if s.kind == 'panel']
    nodes = [s for s in fig.shapes if s.kind != 'panel']
    for s in fig.shapes:
        if s.w <= 0 or s.h <= 0 or not canvas.contains(s, GAP):
            errors.append(f'{s.name}: outside canvas safe margin or invalid dimensions')
    for i, s in enumerate(nodes):
        for other in nodes[i+1:]:
            if s.inflate(GAP/2).overlaps(other.inflate(GAP/2)):
                errors.append(f'{s.name} / {other.name}: node clearance below {GAP}px')
        for panel in panels:
            if s.overlaps(panel) and not panel.contains(s, PADDING):
                errors.append(f'{s.name}: outside panel {panel.name} padding')
            elif panel.contains(s) and s.y < panel.content_top:
                errors.append(f'{s.name}: overlaps panel {panel.name} heading space')
    for i, p in enumerate(panels):
        for q in panels[i+1:]:
            if p.overlaps(q): errors.append(f'{p.name} / {q.name}: panels overlap')
    for i, t in enumerate(fig.texts):
        if not t.label.strip(): continue
        forbidden = {';': 'semicolon', '\u2014': 'em dash', '\u2013': 'en dash',
                     '|': 'vertical bar', '\u00b7': 'middle dot'}
        found = [name for char, name in forbidden.items() if char in t.label]
        if found:
            errors.append(f'text {t.label!r}: punctuation rule rejects {", ".join(found)}. Use plain words and normal sentences')
        if not canvas.contains(t.box, 16):
            errors.append(f'text {t.label!r}: outside canvas safe margin')
        if t.owner:
            s = t.owner
            if s.kind == 'decision':
                cx, cy, r = s.x+s.w/2, s.y+s.h/2, s.w/2
                if any(abs(x-cx)+abs(y-cy) > r-12 for x,y in
                       [(t.box.x,t.box.y),(t.box.right,t.box.y),
                        (t.box.x,t.box.bottom),(t.box.right,t.box.bottom)]):
                    errors.append(f'{s.name}: decision label needs a larger diamond')
            elif not s.contains(t.box, 12 if s.kind == 'panel' else PADDING-2):
                errors.append(f'{s.name}: text {t.label!r} exceeds box padding; widen or increase height')
        for u in fig.texts[i+1:]:
            if u.label.strip() and t.box.inflate(TEXT_GAP/2).overlaps(u.box.inflate(TEXT_GAP/2)):
                errors.append(f'text clearance: {t.label!r} / {u.label!r}')
        for s in nodes:
            if s is not t.owner and s.overlaps(t.box.inflate(TEXT_GAP)):
                errors.append(f'text {t.label!r}: overlaps {s.name}')
    for route in fig.routes:
        pts = route.pts
        ports = []
        for point in (pts[0], pts[-1]):
            matches = [s.port(side) for s in fig.shapes for side in ('left','right','top','bottom')
                       if math.dist(s.port(side).xy, point) < 0.1]
            ports.append(matches[0] if len(matches) == 1 else None)
        for endpoint, port in enumerate(ports):
            if port is None:
                errors.append(f'{route.name}: endpoint {endpoint+1} must attach to a named shape port')
                continue
            a,b = (pts[0],pts[1]) if endpoint == 0 else (pts[-1],pts[-2])
            dx,dy = b[0]-a[0], b[1]-a[1]
            nx,ny = port.normal
            if dx*nx+dy*ny <= 0 or abs(dx*ny-dy*nx) > 0.1:
                errors.append(f'{route.name}: {port.shape.name}.{port.side} violates port normal/axis')
        for j,(a,b) in enumerate(zip(pts,pts[1:])):
            if a[0] != b[0] and a[1] != b[1]:
                errors.append(f'{route.name}: segment {j+1} is diagonal')
            if math.dist(a,b) < GAP:
                errors.append(f'{route.name}: segment/stub {j+1} needs at least {GAP}px')
            if not canvas.contains(Box(min(a[0],b[0]), min(a[1],b[1]), abs(a[0]-b[0]), abs(a[1]-b[1])), 16):
                errors.append(f'{route.name}: segment outside canvas')
            for s in nodes:
                attached = ((j == 0 and ports[0] and ports[0].shape is s) or
                            (j == len(pts)-2 and ports[1] and ports[1].shape is s))
                if not attached and segment_hits(a,b,s.inflate(ROUTE_CLEARANCE)):
                    errors.append(f'{route.name}: crosses {s.name} clearance')
            for t in fig.texts:
                if segment_hits(a,b,t.box.inflate(TEXT_GAP)):
                    errors.append(f'{route.name}: crosses text {t.label!r} clearance')
    return list(dict.fromkeys(errors))
