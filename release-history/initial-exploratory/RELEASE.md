# Research-in-progress release

This repository is a snapshot of exploratory research by Shivam Gupta. The
initial public release follows data collection. Local Git commit identifiers
in study documents refer to the development log, not prior public registrations.
The snapshot's source commit and file hashes are in release-manifest.json.

The completed native-memory study contains 30 writers and 90 readers over 30
Coat development users. Its primary mean-error interval crosses zero. A separate
MemoryCD audit reports simple controls and timestamp boundaries. Earlier pilots,
corrections and rejected hypotheses are retained as part of the research record.
No paper submission, acceptance, externally reviewed novelty or universal
failure of any memory library is claimed.

The released figure can be recreated from saved measurements without downloading
models or datasets. Fully rerunning observed-data analyses requires acquiring
the licensed sources and producing local raw traces. The main README distinguishes
these levels of reproduction. No private customer data were used.

## Release verification

The 97-test suite passed in a fresh Python 3.12 analysis environment containing
NumPy and Matplotlib, without source datasets, models or native memory services.
The latest figure regenerated successfully from the saved measurements. Original
visually checked figure bytes are retained in the release. Results do not depend
on rendering metadata or font-cache timestamps.
