import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from delivery_partition_check import CanonicalBuffer, canonical_trace, partitions


class DeliveryPartitionTests(unittest.TestCase):
    def test_every_partition_preserves_exact_events_and_order(self):
        for size in range(1, 9):
            events = tuple(range(size))
            seen = list(partitions(events))
            self.assertEqual(len(seen), 2 ** (size - 1))
            self.assertEqual(len(set(seen)), len(seen))
            for packets in seen:
                self.assertEqual(tuple(x for p in packets for x in p), events)
                self.assertTrue(all(packets))

    def test_exhaustive_trace_invariance_including_empty_stream(self):
        for size in range(9):
            events = tuple(range(size))
            for width in range(1, 6):
                target = canonical_trace((events,), width)
                for packets in partitions(events):
                    self.assertEqual(canonical_trace(packets, width), target)

    def test_no_early_flush_and_empty_delivery_is_noop(self):
        chunks = []
        buffer = CanonicalBuffer(3, chunks.append)
        buffer.accept(["a", "b"])
        buffer.accept([])
        self.assertEqual(chunks, [])
        buffer.accept(["c", "d"])
        self.assertEqual(chunks, [("a", "b", "c")])
        buffer.finish()
        self.assertEqual(chunks, [("a", "b", "c"), ("d",)])

    def test_repeated_events_are_preserved_not_deduplicated(self):
        chunks, _ = canonical_trace((("a",), ("a", "b"), ("a",)), 2)
        self.assertEqual(chunks, (("a", "a"), ("b", "a")))

    def test_one_end_marker_and_no_post_end_delivery(self):
        buffer = CanonicalBuffer(2, lambda chunk: None)
        buffer.finish()
        with self.assertRaises(ValueError):
            buffer.finish()
        with self.assertRaises(ValueError):
            buffer.accept([1])

    def test_invalid_widths(self):
        for width in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                CanonicalBuffer(width, lambda chunk: None)


if __name__ == "__main__":
    unittest.main()
