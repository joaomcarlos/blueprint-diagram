#!/usr/bin/env python3
"""The delegation policy, using measured nodes and explicit connector ports."""
from pathlib import Path
from blueprint import Fig, C

f = Fig(1200, 2140)
f.header('FIG. 1. TASK DELEGATION', 'T3 ORCHESTRATION',
         'Research in parallel. Make decisions and edits here.', title_size=50)
LX, RX = 148, 1080

triage = f.panel('01', 'TRIAGE', LX, 240, RX-LX, 350, return_shape=True)
owner = f.node(180, 330, 400, 160, 'This thread', role='agent',
               sub='Plans the work and makes decisions')
direct = f.node(720, 304, 320, 112, 'Single lookup', sub='One simple check')
gather = f.node(720, 444, 320, 112, 'Research worker', sub='Finds facts', role='agent')
f.fan_out(owner, [direct, gather], spine_x=650)
f.text(180, 550, 'Delegate research for larger tasks.', 18, C['dim'])

delegate = f.panel('02', 'DELEGATE', LX, 680, RX-LX, 380, return_shape=True)
call = f.node(180, 760, 400, 200, 'delegate_task', role='agent', sub='Runs a research task')
worker = f.card(700, 760, 340, 200, 'FLASH WORKER',
                ['Reads only', 'Cites sources', 'Up to 60 lines'])
f.connect(call, 'right', worker, 'left')
f.text(180, 1004, 'Target: swe-2-flash-medium', 18, C['dim'])
f.text(180, 1038, 'Workers return facts and sources.', 18, C['dim'])
f.connect(triage, 'bottom', delegate, 'top')

verify = f.panel('03', 'VERIFY CITATIONS', LX, 1150, RX-LX, 500, return_shape=True)
f.text(180, 1230, 'Check a few sources before using the findings.', 18, C['dim'])
gate = f.decision(370, 1370, label='Sources\nOK?')
passed = f.node(740, 1314, 300, 112, 'Checked', role='shipped', sub='Use these findings')
retry = f.node(190, 1504, 360, 112, 'Try again', sub='Or ask for help', role='feedback')
f.connect(gate, 'right', passed, 'left', kind='shipped', label='Yes')
f.connect(gate, 'bottom', retry, 'top', kind='feedback', label='No', label_pos=(428, 1480))
f.connect(retry, 'left', call, 'left', via=[(90, 1560), (90, 860)], kind='feedback', dashed=True)
f.vlabel(48, 1210, 'Retry', fill=C['purple'])
f.connect(delegate, 'bottom', verify, 'top')

apply = f.panel('04', 'EDIT AND REPORT', LX, 1740, RX-LX, 230, return_shape=True)
write = f.node(180, 1810, 400, 110, 'Make edits here', role='agent', sub='Check the result')
output = f.node(720, 1810, 320, 110, 'Final result', role='shipped')
f.connect(write, 'right', output, 'left', kind='shipped')
f.connect(verify, 'bottom', apply, 'top')

last = f.legend(80, 2030, [('agent','Work'),('feedback','Retry'),('shipped','Checked')])
f.caption(80, last+54, [('Gather facts in parallel.', 'agent'), (' Keep edits here.', None)])
f.write(Path(__file__).with_suffix('.svg'))
