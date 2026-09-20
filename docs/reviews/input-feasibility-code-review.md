# Review of the language-input feasibility screens

Date: 20 September 2026. Scope: `src/lamp_language_screen.py`, `src/amazon_language_feasibility.py`, their thirteen tests, and the completed LaMP and Digital Music reports. No inference, manuscript changes, source edits, or acquisition changes were performed. The ongoing Musical Instruments download was not accessed or modified.

## Verdict

No observed bug invalidates the current Digital Music no-go or the LaMP input-screen findings. Both reports' recorded code hashes match their current source files. All six LaMP tests and seven Amazon tests pass.

A separate one-off implementation, without importing either screen, reconstructed Digital Music from raw archives and independently obtained:

- 130,434 review rows and 100,952 distinct source user IDs.
- 18 eligible users under the fixed 2022 cutoff and current metadata/history requirements.
- 180 candidates lacking twelve earlier plus three later distinct products.
- Three candidates lacking fifteen distinct products after deduplication.

These match the released screen. The pre-filter count of only 202 users with at least fifteen rows is already below the requested sixty development plus two hundred confirmation users. Therefore the category is insufficient even if a later audit makes minor eligibility corrections.

## Actionable hardening

### 1. Bind Amazon provenance to the actual opened inputs

Priority: medium before using this code as the final dataset gate.

`main` verifies hashes for whichever entries appear in the acquisition manifest, then separately constructs and opens the category's review and metadata paths. It does not require the manifest to contain exactly those two files. An empty or unrelated manifest can therefore bypass input provenance verification. The current Digital Music manifest is correct, so the measured result is unaffected.

Require the exact two expected relative file paths, no duplicates, the matching official category URLs, and matching byte sizes as well as SHA-256 hashes. Validate path containment. Add tests rejecting an empty manifest, the wrong category, duplicate source entries, and a missing source. This prevents a future acquisition bookkeeping mistake from producing a report that appears verified.

### 2. Make timestamp units explicit

Priority: low for the existing Digital Music result, medium for reuse with another source.

The code checks positive integer timestamps but assumes milliseconds when comparing with the 2022 cutoff. Seconds would silently produce no later events. The actual Digital Music bounds are 874557536000 to 1694040099945, consistent with milliseconds, so no unit error occurred. Record timestamp units and bounds, and fail on incompatible magnitudes rather than normalize silently. Include a seconds-versus-milliseconds test.

### 3. Keep feasibility claims narrower than final eligibility

The Amazon screen deduplicates parent product IDs only. It does not detect exact or near-duplicate review text, product aliases, repeated human identities under different source IDs, forbidden content embedded inside allowed catalog strings, or token-budget overflow. Its context-related limitation is already explicit. Add the missing review-text deduplication limitation to the report and documentation.

The current selection is the last twelve **first-ever parent-product events** before the date boundary, not the latest review of each parent product. That is coherent and accurately stated in the report, but differs from an informal description of “most recent twelve reviews.” If a later review repeats a known product, it is intentionally discarded. Preserve this exact choice in the eventual protocol.

The code chooses the chronological panel before checking title presence and nonempty earlier text. It rejects a user with a missing selected title instead of skipping that event and filling from another product. This is a stricter support screen, not a bug. Final prose must not describe it as selecting twelve usable earlier records if that implies replacement of missing ones.

### 4. Avoid conflating parsing with exposure to model inputs

The Amazon JSON loader necessarily parses raw records containing ratings and future review text. Its projection never consults the rating value, never exports text, and only uses earlier text length in eligibility. Thus “rating values not used for selection” and “no target text sent to a predictor” are supported. “Target labels were never read from disk” would not be supported by this implementation. No such stronger claim should be introduced.

No predictor ran, so the `target_review_text_visible_to_predictor: false` field is technically true but is not itself a tested inference boundary. A future pipeline needs a separately serialized input whitelist and canary tests proving labels and target reviews cannot enter writer or reader prompts.

## LaMP-specific observations

The streaming parser correctly handles comma and UTF-8 boundaries under the supplied tests and enforces its byte ceiling. It may download a small part of the next object in the final chunk. The recorded downloaded-prefix hash is therefore a hash of received bytes, not of just the sixty-four normalized records and not of the complete remote file. The current provenance language correctly distinguishes these quantities.

Duplicate detection is exact after whitespace normalization and case folding, not byte-identical text and not semantic duplicate detection. The five own-history target matches support the stated normalized-text concern, not a verified count of leaked ground-truth scores. Likewise the three star-expression matches are explicitly lexical flags. The report correctly avoids inferring independent users from opaque task IDs.

Payload token counts exclude target queries, native writer instructions, chat templates, and generation headroom. They are lower bounds for the respective complete prompts, not exact request lengths. Existing wording is correct. For stronger reproduction of these counts, also record the Transformers/tokenizers versions and relevant tokenizer model configuration, in addition to the currently hashed token JSON files.

`audit` hardcodes “first 64 training records” in its scope string even when unit tests or another caller supply fewer records. The public `main` checks exactly sixty-four, so the released report is accurate. Making this string use `len(rows)` is a minor generalization improvement, not a finding-changing fix.

## Information-boundary assessment

The current screens are appropriate pre-inference support audits. They do not establish model performance, human preference validity, complete anonymization, historical catalog availability, or independent confirmation. Their strongest justified outputs are: the actual input sizes and duplicates in a disclosed LaMP train prefix, and insufficient Digital Music cohort support under a specified label-blind eligibility rule. Neither result should be promoted into a criticism of a published benchmark's accuracy.

## Parent implementation response

After this review, the input screen was revised to require the exact two archive paths, category-specific official URLs, byte counts and content hashes. Millisecond timestamps are checked against the source corpus era. Tests reject mismatched/empty source manifests and second-valued timestamps. The report now states that prediction inputs have not yet been constructed and explicitly discloses unchecked review-text duplication. The selection still rejects incomplete selected windows without backfilling. The Digital Music support count remains 18 after these fixes. This addendum records implementation changes, not a new external review.
