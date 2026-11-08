#!/usr/bin/env python3
"""Copy this example, retain measured boxes/ports, then replace the content.
Run: python3 render.py example.py --svg factory.svg
"""
from pathlib import Path
from blueprint import Fig, C

f = Fig(1200, 1920)
f.header('FIG. 1. HOW WORK GETS DONE', 'THE SOFTWARE FACTORY',
         'A request becomes a task. Check the result before it ships.', title_size=44)
LX, RX = 122, 1078

# Reserve columns and routing lanes before placing text.
inputs = f.panel('01', 'NEW REQUESTS', LX, 250, RX-LX, 330, return_shape=True)
source = f.node(200, 390, 360, 100, 'A new request', role='human')
respond = f.node(720, 330, 300, 80, 'Reply', role='item')
mission = f.node(720, 470, 300, 80, 'Create a task', role='agent')
f.fan_out(source, [respond, mission], spine_x=640)

workflow = f.panel('02', 'WORKFLOW', LX, 660, RX-LX, 760, return_shape=True)
implement = f.node(240, 760, 260, 80, 'Do the work', role='agent', marker='diamond')
review = f.node(240, 900, 260, 80, 'Review it', role='agent', marker='square')
f.connect(implement, 'bottom', review, 'top')
gate = f.decision(370, 1190, label='OK?')
f.connect(review, 'bottom', gate, 'top')
f.connect(gate, 'left', implement, 'left', via=[(170,1190),(170,800)],
          kind='feedback', dashed=True, label='No')
f.vlabel(150, 1000, 'Try again', fill=C['purple'])
passed = f.node(740, 1150, 300, 80, 'Verified', role='shipped')
f.connect(gate, 'right', passed, 'left', kind='shipped', label='Yes')
f.text(740, 735, 'EVIDENCE', 20, C['dim'])
f.kv(740, 770, 300, 64, 'Build', 'Seconds')
f.kv(740, 870, 300, 64, 'Tests', 'Minutes')
f.kv(740, 970, 300, 64, 'Human', 'Review', role='human')
f.connect(inputs, 'bottom', workflow, 'top')

outputs = f.panel('03', 'OUTPUTS', LX, 1500, RX-LX, 260, return_shape=True)
f.card(200, 1580, 340, 110, 'SOFTWARE', ['Artifact or service'])
f.card(700, 1580, 340, 110, 'KNOWLEDGE', ['Reports and findings'])
f.connect(workflow, 'bottom', outputs, 'top')
# A semantic feedback loop gets its own outside lane and exact panel ports.
f.rail([outputs.port('right').xy,(1140,1630),(1140,415),inputs.port('right').xy],
       'What people report', (1174,1010))
last = f.legend(80, 1820, [('agent','Agent'),('human','Human'),
                          ('feedback','Try again'),('shipped','Verified')])
f.caption(80, last+54, [('Check the result', 'shipped'), (' before it ships.', None)])
f.write(Path(__file__).with_name('factory.svg'))
