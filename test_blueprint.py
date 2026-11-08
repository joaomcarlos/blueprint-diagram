"""Geometry regressions. Run: python3 -m unittest -v test_blueprint.py"""
import tempfile
import unittest
from pathlib import Path
from blueprint import Fig


class GeometryTests(unittest.TestCase):
    def write(self, fig):
        with tempfile.TemporaryDirectory() as d:
            return fig.write(Path(d) / 'test.svg')

    def test_long_node_is_rejected_before_export(self):
        f = Fig()
        f.node(160, 285, 360, 96, 'your prompt in a T3 thread',
               sub='any provider or model')
        with self.assertRaises(ValueError):
            self.write(f)

    def test_short_subtitle_box_is_rejected(self):
        f = Fig()
        f.node(100, 100, 200, 40, 'title', sub='subtitle')
        with self.assertRaises(ValueError):
            self.write(f)

    def test_small_decision_is_rejected(self):
        f = Fig()
        f.decision(300, 300, 52, 'verification failed?')
        with self.assertRaises(ValueError):
            self.write(f)

    def test_kv_collision_is_rejected(self):
        f = Fig()
        f.kv(100, 100, 240, 60, 'verification', 'integration')
        with self.assertRaises(ValueError):
            self.write(f)

    def test_diagonal_edge_is_rejected(self):
        f = Fig()
        f.edge([(100, 100), (200, 150)])
        with self.assertRaises(ValueError):
            self.write(f)

    def test_wrapped_autoheight_node_fits(self):
        f = Fig()
        n = f.node(100, 100, 300, None, 'a long title that needs wrapping',
                   sub='a subtitle with enough room')
        self.assertGreater(n.h, 80)
        self.write(f)

    def test_marker_and_subtitle_share_indent(self):
        f = Fig()
        f.node(100, 100, 320, None, 'title', sub='subtitle', marker='diamond')
        import xml.etree.ElementTree as ET
        labels = [ET.fromstring(p) for p in f.parts if p.startswith('<text')]
        self.assertEqual(labels[0].attrib['x'], labels[1].attrib['x'])
        self.write(f)

    def test_decision_autosizes(self):
        f = Fig()
        d = f.decision(400, 300, label='citations verified?')
        self.assertGreater(d.w, 104)
        self.write(f)

    def test_wrong_decision_exit_axis_is_rejected(self):
        f = Fig()
        d = f.decision(400, 400, label='ok?')
        n = f.node(100, 100, 240, 80, 'retry')
        f.edge([d.port('top').xy, (60, d.y), (60, 140), n.port('left').xy])
        with self.assertRaisesRegex(ValueError, 'axis|normal'):
            self.write(f)

    def test_named_ports_make_clean_branch(self):
        f = Fig()
        d = f.decision(300, 300, label='ok?')
        n = f.node(620, 260, 320, 80, 'verified', role='shipped')
        f.connect(d, 'right', n, 'left', kind='shipped', label='yes')
        self.write(f)

    def test_route_through_unrelated_node_is_rejected(self):
        f = Fig()
        a = f.node(100, 100, 200, 80, 'input')
        b = f.node(700, 100, 200, 80, 'output')
        f.node(400, 100, 200, 80, 'obstacle')
        f.connect(a, 'right', b, 'left')
        with self.assertRaisesRegex(ValueError, 'clearance|crosses'):
            self.write(f)

    def test_close_elbow_is_rejected(self):
        f = Fig()
        a = f.node(100, 100, 200, 80, 'input')
        b = f.node(500, 300, 200, 80, 'output')
        f.connect(a, 'right', b, 'left', via=[(310, 140), (310, 340)])
        with self.assertRaisesRegex(ValueError, 'stub|segment'):
            self.write(f)

    def test_floating_endpoints_are_rejected(self):
        f = Fig()
        f.node(100, 100, 200, 80, 'input')
        f.node(500, 100, 200, 80, 'output')
        f.edge([(300, 140), (492, 140)])
        with self.assertRaisesRegex(ValueError, 'port|endpoint'):
            self.write(f)

    def test_panel_header_and_tag_have_separate_rows(self):
        f = Fig()
        x, y = f.panel('01', 'LONG SECTION TITLE', 100, 100, 500, 260,
                       tag='a long explanatory tag')
        self.assertGreaterEqual(y, 184)
        f.node(x, y, 400, 90, 'content')
        self.write(f)

    def test_edge_label_uses_segment_midpoint(self):
        f = Fig()
        a = f.node(100, 100, 200, 80, 'input')
        b = f.node(600, 300, 200, 80, 'output')
        f.connect(a, 'right', b, 'left', via=[(450, 140), (450, 340)], label='yes')
        self.write(f)

    def test_fan_derives_different_target_widths_and_centers(self):
        f = Fig()
        a = f.node(100, 260, 220, 80, 'input')
        b = f.node(600, 100, 260, 80, 'first')
        c = f.node(680, 400, 300, 100, 'second')
        f.fan_out(a, [b,c], spine_x=450)
        self.write(f)

    def test_legacy_fan_with_wrong_stub_is_rejected(self):
        f = Fig()
        f.node(100, 260, 220, 80, 'input')
        f.node(600, 100, 260, 80, 'output')
        f.fan(320, 300, 540, [140])
        with self.assertRaisesRegex(ValueError, 'endpoint'):
            self.write(f)

    def test_route_cannot_cross_loose_annotation(self):
        f = Fig()
        a = f.node(100, 100, 200, 80, 'input')
        b = f.node(700, 100, 200, 80, 'output')
        f.text(400, 146, 'annotation')
        f.connect(a, 'right', b, 'left')
        with self.assertRaisesRegex(ValueError, 'crosses text'):
            self.write(f)

    def test_node_cannot_cross_panel_padding(self):
        f = Fig()
        f.panel('01', 'SECTION', 100, 100, 500, 300)
        f.node(110, 200, 260, 80, 'content')
        with self.assertRaisesRegex(ValueError, 'panel.*padding'):
            self.write(f)

    def test_legend_wraps_before_canvas_edge(self):
        f = Fig(700, 500)
        last = f.legend(80, 100, [('agent','agent / flow'),('human','human review'),
                                  ('feedback','retry'),('shipped','verified')])
        self.assertGreater(last, 100)
        self.write(f)

    def test_failed_export_does_not_create_file(self):
        f = Fig()
        f.decision(100, 100, 20, 'much too long')
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'bad.svg'
            with self.assertRaises(ValueError):
                f.write(path)
            self.assertFalse(path.exists())

    def test_prose_punctuation_rule_blocks_export(self):
        for label in ['Heat; rinse', 'Heat — rinse', 'Heat – rinse',
                      'Heat | rinse', 'Heat · rinse']:
            with self.subTest(label=label):
                f = Fig()
                f.text(100, 100, label)
                with self.assertRaisesRegex(ValueError, 'punctuation'):
                    self.write(f)


if __name__ == '__main__':
    unittest.main()
