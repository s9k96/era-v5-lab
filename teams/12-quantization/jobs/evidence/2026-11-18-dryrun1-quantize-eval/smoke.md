# Dry run 1 quantize and eval flow: local smoke on the p1536 tokenizer (test log for the job request)

This is a test log. It is not a score result and it is not a speed measurement. The model has random weights.

## What was run

- Code under test: bc2bd33 + therahulbhati/era-v5-lab#1 (014744e4) + c79bb624 (no output ids or text for Team 10 rows, agreement per source). That is PR #508's head (`quantize_eval.py`, `flow_fixed_prompts.py` with `--gguf-dir`, `export_hf.py`, `check_gguf_logits.py`) plus one commit that makes `flow_fixed_prompts.py --gguf-dir` record the tokenizer sha256 and one that keeps Team 10 token ids out of the written files; `tokenizer/convert_frozen.py` and `tokenizer/gguf_roundtrip.py` are the ones in #508's tree. Run from the repository root. The main run (`quantize_eval.py`) used bc2bd33 as it is; the `flow_fixed_prompts.py` outputs in this folder are from the rerun on c79bb624, which also rebuilt the GGUFs (same sha256 values) because the first run had deleted them.
- Machine: Apple M5, 16 GB, macOS 26.6.2, Metal. llama.cpp b11669 (`620d2225c`) from Homebrew (`llama-quantize`, `llama-server`) and a b11669 checkout made by the script.
- Python that runs the two scripts: 3.12.15. The script's own converter venv (made by the script with `uv`): torch 2.11.0, transformers 4.57.6, tokenizers 0.22.2, gguf 0.19.0, pyarrow 18.1.0, llama-cpp-python 0.3.36, datasets 4.8.5.
- Checkpoint: random G5 model from `scripts/make_random_checkpoint.py` (2 layers, width 64, 16 + 1 experts, 131,072 ids, 9,775,424 parameters, 17,639,744 parameters after the Granite MoE export). Weights are random, so every score is 0.
- Tokenizer: p1536, sha256 `e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b`, a local copy, `./inputs/tokenizer.json` below. The file is not in the repository.
- Eval for the scores: `--eval` with 20 items written for this smoke (10 multiple-choice, 10 arithmetic; no benchmark text). **This differs from the job request's command**, which has no `--eval`; see "What was not tested".
- Prompts for the second step: `prompts/fixed_100.jsonl` (our 100, sha256 `da3f6851467d5ac57ff9577fa3d341ee98c0bf82293d32da9b5f3fecc90f4919`). The `--manifest` path was not run with real data (see below); its fill and per-source logic was run with synthetic text for the 55 Team 10 slots. `--max-tokens 64`.

## Commands

```bash
python teams/12-quantization/scripts/make_random_checkpoint.py --tokenizer ./inputs/tokenizer.json --out ./inputs/random-g5

python teams/12-quantization/scripts/quantize_eval.py --checkpoint ./inputs/random-g5 --tokenizer ./inputs/tokenizer.json --tokenizer-sha256 e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b --formats bf16,Q8_0,Q4_K_M --roundtrip --eval ./eval_own.json --work ./out/work --runs-csv ./out/runs.csv --scores-out ./out/scores.json

python teams/12-quantization/scripts/flow_fixed_prompts.py --gguf-dir ./out/work --scores ./out/scores.json --formats Q8_0,Q4_K_M --out ./out/prompts --max-tokens 64 --delete-ggufs
```

The 014744e4 rerun built the GGUFs again with `quantize_eval.py` (same command without `--roundtrip`, scores file in the work folder) and ran `flow_fixed_prompts.py --gguf-dir ./out/work --formats Q8_0,Q4_K_M --out ./out/prompts --max-tokens 64`, finding the scores file by its default name; `--scores ./out/scores.json` is what the job request uses and gives the same result.

The work folder was empty before the second command (cold start: llama.cpp clone, converter venv, held-out text all fetched).

Exit codes: `quantize_eval.py` 0, `flow_fixed_prompts.py` 0 (both runs).

## Results

`quantize_eval.py` (wall time 295 s: about 4 min of it is the round trip's held-out fetch and run):

| Step | Result |
|---|---|
| A1 export | max logit difference 1.91e-06 (limit 0.001), same top-1 on 4,096 of 4,096 positions: PASS |
| A3 llama.cpp vs G5 | same top-1 on 16 of 16 prompts, max log-probability difference 0.0065 (limit 0.05): PASS |
| GGUF tokenizer | pre-tokenizer `granite-embed-multi-97m`, 131,072 ids, 356 specials, 0 bad |
| Round trip (`--roundtrip`) | **exit code 1**, as expected for p1536 (same as the task-2 run): 20,400 held-out lines; 3,075 differ in the raw pass, 3,074 of them explained by the normalizer GGUF cannot carry and 1 not (`rus_Cyrl` line 507); normalized pass 1 different; 0 decode errors; 6 bad ids in the whole-vocabulary check (25312, 30697, 38207, 38969, 55750, 109524). Known granite limits. The script reports the exit code and does not stop. |
| Files | bf16 41,214,176 bytes (16.0 bpw, router F32, output BF16); Q8_0 24,679,136 bytes (9.58 bpw, router F32, output Q8_0); Q4_K_M 21,263,840 bytes (8.25 bpw, router F32, output Q8_0). Sizes are large per weight because the 131,072-id embedding dominates a 10M-parameter model. |
| GGUF sha256 | bf16 `6da1554f3b83…`, Q8_0 `26908e9b55e7…`, Q4_K_M `f64e178a0476…` (full values in `runs/manifest_2026-11-18.json`) |
| Score on the 20 items | 0.0 for all three formats (random weights); eval time 4.1 s, 6.5 s, 7.5 s |

`flow_fixed_prompts.py --gguf-dir` (c79bb624 rerun, wall time 16.3 s; `prompts/summary.json` now has `tokenizer_sha256` e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b), 100 prompts, greedy, seed 0, 64 tokens:

| Format | Finish (stop / length) | Mean tok/s | Outputs identical to bf16 | Mean shared prefix with bf16 |
|---|---|---|---|---|
| bf16 | 0 / 100 | 1776.3 | n/a | n/a |
| Q8_0 | 0 / 100 | 1072.1 | 15 of 100 | 0.431 |
| Q4_K_M | 0 / 100 | 1054.9 | 2 of 100 | 0.117 |

The low agreement is a property of random weights, not of the quantization. The agreement numbers are the same as in the first run; only the speeds moved (the machine was less busy).

`--manifest` with a stub (synthetic text for the 55 Team 10 slots, so no benchmark text and no parquet; same GGUFs, same flags, output not kept): `prompts_<format>.jsonl` has no `output_ids`, `text` or prompt for the 55 Team 10 rows (they keep `id`, `source`, `task_id`, token counts, `text_sha256`, finish reason, speed) and has both for our 45. `summary.json` reports `agreement_with_bf16` as `g10_55` and `g12_fill_45`, never pooled; the numbers are on synthetic prompts, so they say nothing about Team 10's items.

Tests, run beside the smoke with the same Python:

| Test | Result |
|---|---|
| `scripts/test_quantize_eval.py` | 4 tests, OK |
| `scripts/test_export_hf.py` | 13 tests, OK |
| `tokenizer/test_convert_frozen.py` (llama.cpp b11669) | PASS |
| `tokenizer/test_gguf_roundtrip_normalizer.py` (b11669) | PASS |
| `scripts/test_flow_fixed_prompts.py` | 6 tests, OK (tokenizer sha from scores.json; Team 10 rows written without ids or text, kept in memory; agreement split per source; plain run unchanged; fake `llama_cpp`, no model) |
| `scripts/test_flow_fixed_prompts.py` (014744e4) | 3 tests, OK |
| `manifest_prompts()` fill logic, with `resolve_prompts` replaced by a stub that returns synthetic text for the 55 resolved slots | 100 rows, ids unique, 55 from G10 (private) and 45 from our prompts (20 tool_agentic, 15 indic, 10 general); manifest sha256 `d6190b2d…` |

## What was not tested

1. **The real dry run 1 checkpoint** (about 300M parameters, `checkpoint.pt` plus `manifest.json` from #475). The smoke used a 10M random model, so time, memory and tokens per second say nothing about it.
2. **A GPU.** Everything ran on Metal on one laptop. Hardware `1 GPU` in the job (CUDA) is untested, including llama-server `-ngl 99` and llama-cpp-python's GPU path.
3. **The 55 resolved Team 10 slots.** The parquet files (`deepmind/code_contests`, `EleutherAI/hendrycks_math`) are not on this machine, so `--manifest` with real `--source-dir`s was not run. Only the fill logic was checked with synthetic text.
4. **No-network behaviour.** The flow was run with network on, and it uses it (below). It has not been run offline.
5. **The job request's exact command.** It has no `--eval`, so `quantize_eval.py` would fetch MMLU and GSM8K test parquet files to build its stand-in eval. This smoke passed its own 20 items instead, so no benchmark text was written on this machine. The default stand-in path is therefore untested here.
6. **Python for the second command.** `flow_fixed_prompts.py` needs `llama_cpp` in the Python that runs it. Here that was a venv with llama-cpp-python 0.3.36. The job request does not say which Python TSAI uses.

## Network calls at run time

`quantize_eval.py --checkpoint ... --tokenizer ... --roundtrip` calls the network at these points (none were skipped on the cold start):

1. `git ls-remote --tags https://github.com/ggml-org/llama.cpp` (`llama_tag`, to find the tag of the binaries' commit).
2. `git clone --depth 1 --branch b11669 https://github.com/ggml-org/llama.cpp` (converter source).
3. `uv venv --python 3.12` (downloads Python 3.12 if missing) and `uv pip install -r requirements-convert_hf_to_gguf.txt` (PyPI: torch, transformers, numpy, sentencepiece, ...) then `uv pip install` of the local `gguf-py` and `pyarrow<19`.
4. `uv pip install llama-cpp-python==0.3.36 datasets==4.8.5 regex` (PyPI; llama-cpp-python is built or downloaded) for the round trip.
5. The round trip's held-out text: `datasets.load_dataset(..., streaming=True)` from the Hugging Face Hub for `HuggingFaceFW/fineweb-2`, `HuggingFaceFW/fineweb` and `codeparrot/codeparrot-clean-valid`, each at a pinned commit (about 4 minutes, written to `work/heldout/lines.json`).
6. Without `--eval`: `urllib.request.urlretrieve` of the MMLU and GSM8K test parquet files from huggingface.co (`make_standin`). Not called in this smoke.
7. Only with `--model` (not `--checkpoint`): `hf_download` of the model from the Hub. Not called here.

Local only, not network: `llama-server` on 127.0.0.1 (ports chosen per run) for scoring and for test A3.

`flow_fixed_prompts.py --gguf-dir` makes no network call. With `--manifest` it reads local parquet files only.

So the first command needs preparation for a no-network job: a work folder that already holds `llama.cpp-b11669/`, the converter venv (`.venv-convert` with the packages above), `heldout/lines.json`, and either `--eval` with a local file or the stand-in file; `ls-remote` (item 1) has no local fallback in the current code and fails offline.

## Other findings (not fixed)

- On bc2bd33 `flow_fixed_prompts.py` wrote `output_ids` for the Team 10 rows (only `text` was dropped). Team 10 does not allow that (with the public tokenizer the ids are the answer); c79bb624 stops it. Until it lands in #508, a `--manifest` run leaks them.
- The `--gguf-dir` summary had no tokenizer sha256 on bc2bd33; therahulbhati/era-v5-lab#1 adds it (the rerun above).
- `quantize_eval.py` wrote `runs/manifest_<date>.json` next to `--runs-csv` (here `out/manifest_2026-11-18.json`), as designed.

## Files in this folder

`scores.json`, `runs.csv`, `prompts/summary.json`, `roundtrip/` (the round-trip report `.md` and `.json`, ids, counts and hashes only, and `result.json`), `quantize_eval.log`, `flow_fixed.log`, `tests.log`. Local paths are replaced by `.`, `<repo>` and `~`. Not here: the tokenizer, the GGUF files, the exported model, the per-prompt outputs, the llama-server log.
