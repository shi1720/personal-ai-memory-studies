# Native extraction resource results

Protocol and code were committed at 784d060 before this run. All three specified
fitting users completed through the unmodified Mem0 extraction and storage path.
There were three actual generations, zero truncations and no retries. No random-
item target matrix was loaded; no preference accuracy was scored.

| Fitting user row | Prompt tokens | Output tokens | Stored memories | UTF-8 text bytes | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| 165 | 8904 | 464 | 1 | 1089 | 25.36 |
| 159 | 8902 | 528 | 5 | 1055 | 26.10 |
| 153 | 8909 | 812 | 5 | 1861 | 37.71 |

The writer receives 24 observed rating records per user. It can consolidate
multiple records into one memory, so stored-memory counts are not recall scores.
The prompt includes native extraction instructions and runtime dates, captured
in the raw traces. Timing includes native add and get_all, using a warmed local
server with substantial prefix-cache reuse. It is not a cold-start latency or
cross-system speed comparison. Text bytes exclude vectors, database metadata,
entity links and stored message history, so they are not total memory costs.

All results are resource/preflight observations, not evidence of faithfulness,
causality, preference-prediction gains or novelty. Full-history and retrieval
controls, downstream reader configuration, independent evaluation and a
substantive contribution remain necessary. The 200 reserved users are unscored.

The exact data-derived input/output traces are retained locally under ignored
data/ with SHA256 references in results/coat-native-resource-preflight.json.
No raw third-party ratings are redistributed. Source/protocol and all three
trace hashes were validated after completion. NLP, BM25 and dense embeddings
were enabled. The local Qdrant payload-index warning affects indexes, while
user filtering was separately checked in the fictional preflight.
