import unittest

from lymph.core.monitoring.global_metrics import ProcessMetrics


class GlobalMetricsTests(unittest.TestCase):
    def setUp(self):
        self.process_metrics = ProcessMetrics()

    def test_process_metrics(self):
        metric_names = [m[0] for m in self.process_metrics]

        self.assertIn('proc.files.count', metric_names)
        self.assertIn('proc.threads.count', metric_names)
        self.assertIn('proc.mem.rss', metric_names)
        self.assertIn('proc.cpu.system', metric_names)
