#!/usr/bin/env python3
"""Blueprint diagram: McDonald's potato peeling and cutting mechanics."""
import sys
from pathlib import Path

sys.path.insert(0, '/home/jc/.config/devin/skills/blueprint-diagram')
from blueprint import Fig, C

f = Fig(1200, 2760)
f.header(
    'FIG. 1. POTATO PEELING AND CUTTING',
    'MCDONALD\'S POTATO LINE',
    'Suppliers peel, cut, blanch, dry, fry, and freeze potatoes.',
    title_size=44,
)

# ---------------------------------------------------------------- peeling
p1 = f.panel(
    '01', 'PEELING', 60, 230, 1080, 680,
    note='Steam loosens the skin. Water and brushes remove it.',
    return_shape=True,
)
whole = f.node(130, 380, 250, None, 'Whole potatoes',
               sub='Arrive at the factory', role='item')
prep = f.node(130, whole.bottom + 56, 250, None, 'Wash and sort',
              sub='Remove dirt, stones and metal', role='item')
steam = f.node(560, 380, 340, None, 'Steam peeler',
               sub='Steam heats the skin. Lifters mix the potatoes. Steam vents fast.', role='item')
brush = f.node(560, steam.bottom + 56, 340, None, 'Rinse and brush',
               sub='Wash and brush off the loose skin', role='item')
peeled = f.node(930, brush.y + (brush.h - 168) / 2, 180, 168, 'Peeled potatoes',
                sub='Ready to cut', role='item')

f.connect(whole, 'bottom', prep, 'top')
f.connect(prep, 'right', steam, 'left', via=[(430, prep.y + prep.h / 2), (430, steam.y + steam.h / 2)])
f.connect(steam, 'bottom', brush, 'top')
f.connect(brush, 'right', peeled, 'left')
f.text(560, max(brush.bottom, peeled.bottom) + 48, 'Loose skin goes to other uses or waste', size=18, fill=C['dim'])

# ---------------------------------------------------------------- cutting
p2 = f.panel(
    '02', 'CUTTING', 60, 990, 1080, 700,
    note='Water carries each potato through cutting blades.',
    return_shape=True,
)
preheat = f.node(130, 1160, 280, 200, 'Warm the potatoes',
                 sub='Hot water softens them. Some sites add pulses.', role='item')
cutter = f.node(540, 1160, 360, 200, 'Cut into fries',
                sub='Water lines up potatoes in a funnel, then pushes them through blades.', role='item')
strips = f.node(950, 1176, 160, 168, 'Fries',
                sub='Straight strips', role='item')
slabs = f.node(540, 1470, 360, 140, 'Offcuts',
               sub='Outer pieces go to other uses', role='plain')

f.connect(preheat, 'right', cutter, 'left')
f.connect(cutter, 'right', strips, 'left')
f.connect(cutter, 'bottom', slabs, 'top', label='Offcuts',
          label_pos=(850, 1425))
f.text(560, 1650, 'Offcuts go to other uses', size=18, fill=C['dim'])
f.connect(p1, 'bottom', p2, 'top')

# ------------------------------------------------------- downstream + notes
p3 = f.panel(
    '03', 'AFTER CUTTING', 60, 1770, 1080, 860,
    note='What happens next depends on the supplier.',
    return_shape=True,
)
optical = f.node(130, 1960, 250, 228, 'Check for defects',
                 sub='Scanners find flaws. Air jets remove bad fries.', role='item')
finish = f.node(470, 1960, 300, 228, 'Blanch, dry, partly fry and freeze',
                sub='Ready to send to restaurants', role='item')
restaurant = f.node(860, 1960, 240, 228, 'At the restaurant',
                    sub='Fry in oil, then add salt', role='shipped')
f.connect(optical, 'right', finish, 'left')
f.connect(finish, 'right', restaurant, 'left')

f.text(130, 2240, 'MECHANISM NOTES', size=18, fill=C['dim'], bold=True, ls=1)
f.kv(130, 2270, 880, 72, 'Steam peel', 'Pressure, fast venting, water and brushes')
f.kv(130, 2370, 880, 72, 'Water-gun cut', 'Funnel and guides line up the potatoes')
f.kv(130, 2470, 880, 72, 'Other cuts', 'Pushers trim. Shaped blades make crinkle cuts')
f.connect(p2, 'bottom', p3, 'top')

last = f.legend(80, 2680, [('item', 'Process'), ('shipped', 'Fries output'), ('plain', 'Offcuts and notes')])
f.caption(80, last + 54, [
    ("Sources: McDonald's, Lamb Weston, McCain, TOMRA, and Lamb Weston patents.", None),
])

f.write(Path(__file__).with_name('potato-fries.svg'))
