#!/usr/bin/env python3
"""flow_fixed_prompts.py: the tokenizer sha256 from scores.json, no ids or text for Team 10 rows, agreement per source.

    python test_flow_fixed_prompts.py"""
import json, sys, tempfile, types, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import flow_fixed_prompts as f  # noqa: E402

SHA = "e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b"


class TokenizerShaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def scores(self, name, **kw):
        (self.d / name).write_text(json.dumps(kw), encoding="utf-8"); return self.d / name

    def test_default_file_in_the_gguf_dir(self):
        self.scores("m-scores.json", tokenizer_sha256=SHA)
        self.assertEqual(f.tokenizer_sha_from_scores(self.d, None), (SHA, None))

    def test_explicit_path_wins(self):
        other = self.scores("elsewhere.json", tokenizer_sha256=SHA)
        self.scores("m-scores.json", tokenizer_sha256="0" * 64)
        self.assertEqual(f.tokenizer_sha_from_scores(self.d, other), (SHA, None))

    def test_not_found_or_ambiguous_or_empty_is_noted_not_guessed(self):
        sha, why = f.tokenizer_sha_from_scores(self.d, None)
        self.assertIsNone(sha); self.assertIn("no *-scores.json", why)
        self.scores("a-scores.json", tokenizer_sha256=SHA); self.scores("b-scores.json", tokenizer_sha256=SHA)
        sha, why = f.tokenizer_sha_from_scores(self.d, None)
        self.assertIsNone(sha); self.assertIn("2 *-scores.json", why)
        sha, why = f.tokenizer_sha_from_scores(self.d, self.scores("c.json", tokenizer_sha256=""))
        self.assertIsNone(sha); self.assertIn("no tokenizer_sha256", why)


class FakeLlama:
    """Stands in for llama_cpp.Llama: answers 3 tokens per prompt, the path decides the last one (bf16 vs quantized)."""
    def __init__(self, model_path, **kw): self.last = 9 if "q" in Path(model_path).name else 3
    def token_eos(self): return 0
    def tokenize(self, b, add_bos, special): return [1, 2]
    def generate(self, ids, **kw): yield from (5, 6, self.last, 7)
    def detokenize(self, ids): return b"x" * len(ids)


class PrivateRowsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)
        sys.modules["llama_cpp"] = types.SimpleNamespace(Llama=FakeLlama)
        self.prompts = [{"id": f"s{i}", "source": "g10" if i < 3 else "g12", "task_id": f"t{i}", "prompt": "p", "private": i < 3}
                        for i in range(5)]

    def tearDown(self):
        del sys.modules["llama_cpp"]; self.tmp.cleanup()

    def run_fmt(self, name):
        return f.generate(Path(name), self.prompts, 3, 64, 0, self.d / f"{name}.jsonl")

    def test_private_rows_are_written_without_ids_or_text_but_kept_in_memory(self):
        r = self.run_fmt("bf16.gguf")
        written = [json.loads(x) for x in (self.d / "bf16.gguf.jsonl").read_text().splitlines()]
        for w, p in zip(written, self.prompts):
            self.assertNotIn("private", w)
            self.assertEqual(("output_ids" in w, "text" in w), (not p["private"],) * 2)
            self.assertEqual(w["n_output_tokens"], 3); self.assertIn("text_sha256", w); self.assertEqual(w["finish_reason"], "length")
        self.assertEqual(r["rows"][0]["output_ids"], [5, 6, 3])

    def test_agreement_is_computed_and_split_by_source(self):
        a = f.agreement_by_source(self.run_fmt("bf16.gguf")["rows"], self.run_fmt("q8.gguf")["rows"])
        self.assertEqual(list(a), ["g10_3", "g12_fill_2"])
        # [5,6,3] vs [5,6,9]: not identical, shared prefix 2 of 3
        self.assertEqual(a["g10_3"], {"identical_outputs": 0, "of": 3, "mean_shared_prefix_fraction": 0.6667})
        self.assertEqual(a["g12_fill_2"]["of"], 2)
        same = f.agreement_by_source(self.run_fmt("bf16.gguf")["rows"], self.run_fmt("bf16.gguf")["rows"])
        self.assertEqual(same["g10_3"]["identical_outputs"], 3)

    def test_plain_run_is_unchanged(self):
        self.prompts = [{"id": f"p{i}", "prompt": "p"} for i in range(2)]
        r, q = self.run_fmt("bf16.gguf"), self.run_fmt("q8.gguf")
        self.assertEqual(f.agreement_by_source(r["rows"], q["rows"]), f.agreement(r["rows"], q["rows"]))
        written = [json.loads(x) for x in (self.d / "bf16.gguf.jsonl").read_text().splitlines()]
        self.assertTrue(all("output_ids" in w and "text" in w and "source" not in w for w in written))


if __name__ == "__main__":
    unittest.main()
