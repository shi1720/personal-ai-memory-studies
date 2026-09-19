"""Exact sanity check for delivery boundaries, without any language model.

This is an engineering control, not a new memory method or a benchmark result.
The writer deliberately depends on its input chunk. A persistent canonical
buffer removes delivery partition dependence while preserving that writer.
"""
from itertools import combinations
import json
from pathlib import Path


def partitions(events):
    """All contiguous, nonempty partitions, preserving event order."""
    events = tuple(events)
    if not events:
        yield ()
        return
    for count in range(len(events)):
        for cuts in combinations(range(1, len(events)), count):
            endpoints = (0,) + cuts + (len(events),)
            yield tuple(events[a:b] for a, b in zip(endpoints, endpoints[1:]))


class CanonicalBuffer:
    """Buffer by event count; delivery boundaries never trigger a flush.

    Call finish only at the same logical end of stream across comparisons.
    Durable persistence, exactly-once delivery, clocks and retries are outside
    this deliberately small control. The callback must complete successfully.
    """

    def __init__(self, width, emit):
        if not isinstance(width, int) or isinstance(width, bool) or width < 1:
            raise ValueError("width must be a positive integer")
        self.width = width
        self.emit = emit
        self.pending = []
        self.closed = False

    def accept(self, events):
        if self.closed:
            raise ValueError("stream is closed")
        for event in events:
            self.pending.append(event)
            if len(self.pending) == self.width:
                self.emit(tuple(self.pending))
                self.pending.clear()

    def finish(self):
        if self.closed:
            raise ValueError("stream is closed")
        if self.pending:
            self.emit(tuple(self.pending))
            self.pending.clear()
        self.closed = True


def packet_trace(deliveries):
    """Toy lossy writer: retain only the last event of each supplied chunk."""
    return tuple(packet[-1] for packet in deliveries if packet)


def canonical_trace(deliveries, width):
    chunks = []
    buffer = CanonicalBuffer(width, chunks.append)
    for packet in deliveries:
        buffer.accept(packet)
    buffer.finish()
    return tuple(chunks), packet_trace(chunks)


def main():
    # Exhaustion over eleven distinct events means 2**10 = 1,024 partitions.
    # Number of partitions is combinatorial coverage, not a sample of users.
    events = tuple(range(11))
    deliveries = list(partitions(events))
    target_chunks, target_trace = canonical_trace((events,), 3)
    canonical_mismatches = []
    packet_mismatches = 0
    for packets in deliveries:
        chunks, trace = canonical_trace(packets, 3)
        if chunks != target_chunks or trace != target_trace:
            canonical_mismatches.append(packets)
        packet_mismatches += packet_trace(packets) != packet_trace((events,))
    record = {
        "status": "deterministic engineering control; no LLM or user evaluation",
        "events": list(events), "canonical_width": 3,
        "partitions_checked": len(deliveries),
        "canonical_chunks": target_chunks, "canonical_writer_trace": target_trace,
        "canonical_trace_mismatches": len(canonical_mismatches),
        "packet_writer_mismatches_against_single_packet": packet_mismatches,
        "interpretation": "Buffering solves delivery invariance under the stated contract; it says nothing about answer accuracy, latency or best chunking.",
    }
    if canonical_mismatches:
        raise AssertionError("Canonical buffer changed its writer inputs")
    root = Path(__file__).resolve().parents[1]
    (root / "results/delivery-partition-control.json").write_text(
        json.dumps(record, indent=2) + "\n"
    )
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
