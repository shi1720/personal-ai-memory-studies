# Delivery boundaries are not yet a research contribution

Status: bounded candidate screen, 2026-09-19. No LLM experiment or new method
claim. ICML remains the target level; this note is not a submission manuscript.

## Question and distinctions

Let an ordered history be H = (e1, ..., en), with immutable speaker, content,
event time and session metadata. A delivery partition P divides H into
contiguous nonempty packets without modifying or reordering events. Compare
the final memory and answers after all events have arrived.

Three different interventions must not be conflated:

1. **Transport:** change API packet boundaries while retaining the same logical
   sessions and extraction inputs.
2. **Consolidation:** change which events are jointly supplied to a writer, or
   when the writer runs. This changes the information and computation available
   at each update even when final history is identical.
3. **Chronology:** change event order or timestamps. This can change the intended
   answer and is not the proposed meaning-preserving intervention.

Equal numbers of calls do not imply equal token costs or equivalent information.
Permuting a multiset of batch lengths preserves call count and batch-size
distribution, but it does not preserve the actual extraction prompts. End-state
invariance also does not imply identical answers to queries arriving midstream.

## Closest work and reading depth

- [LycheeMemory V2](https://arxiv.org/html/2608.12990v1): read Sections 3.1-3.3,
  selected construction-cost discussion and Section 4.4's construction ablation,
  plus the displayed encoding settings. It already compares eager, fixed-window
  and semantic consolidation. Thus a generic result that consolidation boundaries
  affect accuracy or cost is insufficient differentiation. Its cross-segment
  reference context also rules out presenting simple context carryover as new.
- [SegTreeMem](https://arxiv.org/html/2606.04555v1): read problem definition,
  related-work comparison, tree representation, selected construction/results
  text and Appendix G.1's compatibility descriptions. Its batch mode compares
  frontier candidates in one call; this is not batching multiple incoming user
  events. Its temporal permutation experiment changes order. Neither term should
  be used as evidence of a delivery-partition experiment without further reading.
- [MemTrace](https://arxiv.org/html/2605.28732v1): read the displayed decisive-error
  definition and Sections 3 through 4.2. It tracks dependencies between memory
  operations and attributes failures. Generic tracing or source-level failure
  diagnosis is already covered. Its annotated setting must not be equated with
  arbitrary causal identifiability in other systems.
- [LiveMem](https://arxiv.org/abs/2608.02515): primary abstract only. Persistent
  intrinsic state under context turnover is related, but its detailed relation
  to ingestion boundaries is not established by this reading.

This is a nonexhaustive screen. Search results without exact phrase matches do
not establish novelty. Secondary commentary was used only to locate primary
sources. No reported paper result was reproduced here.

## Actual Mem0 path inspected

Pinned revision: `a39a802bbc93e85b820078cd3c4dbaf53af25dbe`.
Source hash and URL: `references/mem0-parser-screen.json`.
Read the synchronous `_add_to_vector_store` implementation through its return,
including retrieval, extraction, deduplication, persistence and entity linking.

The inferred-add path retrieves ten existing memories and ten recent messages,
then calls the additive extraction prompt once for the supplied new messages.
It deduplicates extracted text hashes against the retrieved memories and within
the current extracted batch, persists records, links entities, and saves messages.
The prompt builder supports explicit dates; the inspected call omits those
arguments. That is a source observation, not a demonstrated temporal bug.

Changing incoming packet boundaries therefore may change extraction inputs,
recent context, retrieval candidates and invocation count. No invariance contract
was established. A failure of an altered component would not demonstrate failure
of the deployed service. The earlier exported-prompt experiment is not a test
of this active path. See `pilot-004-source-correction.md`.

## Cheap control: persistent canonical buffering

Choose a positive integer b. Preserve incomplete events in a buffer across
delivery calls. Emit the next b events whenever available. Flush the final short
chunk only at a common logical end marker, not at every delivery boundary.

**Elementary proposition, no novelty claimed.** For every contiguous delivery
partition of the same H, this procedure emits exactly

    (e1,...,eb), (e[b+1],...,e[2b]), ..., final remainder.

Proof: after any k events have been consumed, the emitted prefix consists of
floor(k/b) complete chunks and the pending buffer is exactly the remaining
k mod b events. The invariant starts true at k=0 and is preserved by appending
one event, with a flush precisely when the buffer reaches b. Delivery boundaries
perform no operation. The common final marker emits the same remainder.

Consequently any deterministic writer receives the same ordered inputs and
states by induction, provided all its other inputs are the same. For stochastic
writers, equality requires coupled random draws or is only distributional under
identical state-dependent kernels. Wall-clock dates, provider drift, external
retrieval state, concurrent updates and failures violate those assumptions unless
controlled. The buffer does not make an inaccurate writer accurate.

`src/delivery_partition_check.py` exhausts all 1,024 contiguous partitions of an
eleven-event sequence using a deliberately nonassociative toy writer that retains
each input chunk's last event. There are zero canonical writer-trace mismatches.
Processing the delivery packets directly changes that toy trace in 1,023 cases
relative to a single packet. These are exact program checks, not empirical LLM
failure rates or independent user samples. Six tests additionally cover event
conservation, repeated events, no premature flush, empty input and finalization.
Results: `results/delivery-partition-control.json`.

## Decision

Do not launch a large language-model study merely to show transport sensitivity.
Do not claim canonical buffering as a new memory algorithm. The unrestricted
end-of-history delivery-invariance requirement has a simple engineering solution,
and the broader accuracy/cost consequences of semantic consolidation have close
prior work.

A stronger research question would have to specify a constraint that this control
cannot satisfy, such as strict intermediate-answer deadlines with bounded state,
and demonstrate a new accuracy/latency/storage tradeoff against established
online semantic segmentation. No such result or novel algorithm exists in this
repository yet. This candidate does not pass the main-contribution gate in its
current form. It remains a useful evaluation control for later work.

## Reproduce

```sh
python3 -m unittest discover -s tests -p 'test_delivery_partition_check.py' -v
python3 src/delivery_partition_check.py
```
