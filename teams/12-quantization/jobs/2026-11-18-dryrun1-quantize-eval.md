# Dry run 1 checkpoint: quantize, score and 100 fixed prompts (Gate 3 evidence)

DRAFT, to be sent on Wed 18 Nov. The checkpoint is the dry run 1 run folder that TSAI kept (#475, `./out/dryrun1-1234`:
`checkpoint.pt`, `manifest.json`, `summary.json`). It was trained with the frozen p1536 tokenizer (TSAI's result comment
on #475, 16 Nov). The export reads the model settings from the run folder's `manifest.json`, so no `--spec` is needed.

```
Team:            12-quantization
Owner:           Rahul Bhati (therahulbhati), Shubham Saxena (s9k96)
Lead approval:   SreekanthZipsy
Question:        Does the G12 flow take the dry run 1 checkpoint to bf16, Q8_0 and Q4_K_M GGUF files with no manual step, and how far do Q8_0 and Q4_K_M move from bf16 in score and on 100 fixed prompts?
Script:          teams/12-quantization/scripts/quantize_eval.py, then teams/12-quantization/scripts/flow_fixed_prompts.py (with export_hf.py, check_gguf_logits.py, tokenizer/gguf_roundtrip.py and Team 10's eval/effort_suite.py)
Command:         python teams/12-quantization/scripts/quantize_eval.py --checkpoint inputs/dryrun1-1234 --tokenizer inputs/tokenizer.json --tokenizer-sha256 e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b --formats bf16,Q8_0,Q4_K_M --roundtrip --work out/work --runs-csv out/runs.csv --scores-out out/scores.json && python teams/12-quantization/scripts/flow_fixed_prompts.py --gguf-dir out/work --scores out/scores.json --formats Q8_0,Q4_K_M --manifest teams/10-post-training/eval/effort_manifest.json --source-dir code_contests=inputs/code_contests --source-dir hendrycks_math=inputs/hendrycks_math --out out/prompts --delete-ggufs
Config:          none (every setting is on the command line)
Inputs:          see "Inputs and pins" below
Hardware:        1 GPU
Max time:        60 minutes (ESTIMATE: the random 10M-parameter test took 6.5 min on an Apple M1, most of it package installs; dry run 1 is about 300M parameters)
Precision:       bf16 (baseline), Q8_0 and Q4_K_M weights; router F32, output Q8_0
Measures:        A1 (export logits vs G5's model), A3 (llama.cpp vs G5), round-trip exit code; per format: size, bpw, router/output type, score, eval time, tok/s; on the 100 prompts per format: finish reasons, tok/s, outputs identical to bf16, mean shared prefix with bf16
Expected result: A1 and A3 PASS; round trip exit 1 or 2 (known limits of the GGUF tokenizer, #467); Q8_0 within noise of bf16 and close to bf16 on the prompts; Q4_K_M within about 2 points. No score level is assumed for a 1,221-step model.
Outputs:         out/runs.csv, out/scores.json, out/work/*-roundtrip/*.md, out/work/*.json, out/prompts/summary.json, out/prompts/prompts_<format>.jsonl (ids, output token ids, sha256s; text only for our own prompts), logs. GGUF files deleted at the end.
Test log:        teams/12-quantization/jobs/evidence/2026-11-18-dryrun1-quantize-eval/smoke.md (own machine, random G5 checkpoint, p1536 tokenizer)
```

## Inputs and pins

| Input | Where TSAI gets it | Pin |
|---|---|---|
| Run folder `inputs/dryrun1-1234/` | #475 output, kept by TSAI | `summary.json` `final_model_sha256` |
| Tokenizer `inputs/tokenizer.json` | p1536, the one dry run 1 used. Not in the repository: TSAI stages it, and checks it against `teams/03-tokenizer/release/SHA256SUMS` | sha256 `e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b` |
| `inputs/code_contests/` | `deepmind/code_contests` @ `802411c3010c`, the 24 `train-*.parquet` files the manifest names (about 4.6 GB) | each file's sha256 in `effort_manifest.json`, checked by `effort_suite.py` |
| `inputs/hendrycks_math/` | `EleutherAI/hendrycks_math` @ `21a5633873b6`, the 7 `<subject>/train-*.parquet` files (3 MB) | as above |
| 100 prompts | Team 10's `eval/effort_manifest.json` (in the repo): 30 code and 25 math slots from the files above; its 45 unavailable slots (20 tool, 15 Indic, 10 general) filled from our `prompts/fixed_100.jsonl` | manifest `d6190b2d…`, `fixed_100.sha256` |
| llama.cpp | b11669 binaries (`llama-quantize`, `llama-server`) | build number checked by the script |

Team 10's prompt texts, the model's answers and the output token ids are not written to `out/`, only slot ids, token counts, sha256s, the finish reason and speed. `summary.json` reports agreement with bf16 separately for Team 10's 55 slots and our 45 fill slots.

## Test run (18 Nov, Apple M5 16 GB, Metal, llama.cpp b11669)

Full log: `evidence/2026-11-18-dryrun1-quantize-eval/smoke.md`. Random G5 checkpoint from `scripts/make_random_checkpoint.py`
(2 layers, width 64, 16 + 1 experts, 131,072 ids, 9.8M parameters), the p1536 tokenizer (`e6b93a93…`), 20 own eval
items instead of the stand-in. `quantize_eval.py` exit 0 in 295 s; `flow_fixed_prompts.py --gguf-dir` exit 0 in 16 s.

| Step | Result |
|---|---|
| A1 export | max logit difference 1.91e-06, same top-1 on 4,096 of 4,096 positions: PASS |
| A3 llama.cpp vs G5 | same top-1 on 16 of 16 prompts, max log-probability difference 0.0065: PASS |
| Round trip | 3,075 of 20,400 held-out lines differ (3,074 the dropped normalizer, 1 not); 6 single tokens wrong in the whole-vocabulary check: exit 1 |
| bf16 / Q8_0 / Q4_K_M | built (41.2, 24.7 and 21.3 MB), router F32 and output Q8_0 checked, scored (score 0: random weights) |
| 100 prompts | all three formats ran; Q8_0 identical to bf16 on 15 of 100, Q4_K_M on 2 of 100 (random weights) |

## Open before sending

1. **No network in a job (JOB_REQUEST.md rule 1).** `quantize_eval.py` downloads at run time: the llama.cpp checkout,
   the converter venv (`uv pip install`), llama-cpp-python and `datasets` for the round trip, the held-out text for the
   round trip and the stand-in eval. Either TSAI's machine has these, or `inputs/` carries them (a prepared `--work`
   folder with `llama.cpp-b11669/`, `heldout/lines.json` and the eval file). The work folder also holds the converter
   venv and the exported model, so it should not count toward the 50 MB of `out/`. To agree with TSAI.
2. **Eval set for the scores.** `quantize_eval.py` scores its own items file (default: the 25 Oct stand-in). Decide
   whether to pass G9's eval-mini items with `--eval` instead, so the numbers can be compared with week 2.
