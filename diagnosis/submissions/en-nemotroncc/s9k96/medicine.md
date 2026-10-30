# Medicine sheet: en-nemotroncc (s9k96)

Pack `en-nemotroncc`, 500 documents. Counts below come from the 250 documents I have reviewed and accepted so far (`diagnosis/submissions/en-nemotroncc/s9k96/labels.csv`). Five diseases occur more than five times: C1 (39 documents), C4 (26), C3 (23), C5 (16) and D3 (6). Every rule is a short Python function. The same code is in `medicine.py` (a function returns the fixed text, or `None` to drop the document).

**Harm test.** The gold set is pending: run by Data A/B. Until then each section gives a proxy test: the rule run on my 167 reviewed documents labelled `clean`. The limit is 1% of 167, so at most 1 document may change or be dropped. The proxy also says how many reviewed documents of that disease the rule touches. The proxy sample is small, so read it as a sanity check, not as the gold result.

## Medicine 1: C1 boilerplate

1. **Disease:** C1, 39 documents. Examples:
   - `17f4af14c04c9fde`: `Primary tabs` (offset 39)
   - `b787548f4655559b`: `Search for:` (offset 1952)
   - `ca32200e3729539d`: `Click to expand...` (offset 1231)
2. **Medicine:** delete every line that is only a known widget or menu label (`Primary tabs`, `Search for:`, `Related posts`, `Share this:`, `Read more`, `Link copied`, `Quantity`, and a few more). A whole-line match is required, so a sentence that contains these words is never touched.
```python
WIDGET = re.compile(r"(?i)(?:primary tabs|search for:?|related (?:documents|posts|articles):?|click to expand\W*|read more\W*|\[?read more\W*\]?|share this:?|share on (?:other sites|[a-z ]+)|previous|next|menu|contents|advertisement|loading\W*|link copied|the link has been copied!?|post navigation|quantity|breadcrumb|logged|registered|banned|show more|you may also like[a-z ]*|subscribe to [a-z ]+|skip to (?:main )?content|back to top)")

def c1(t):
    """Delete lines that consist only of a known widget or menu label ('Primary tabs', 'Search for:', 'Related posts', 'Share this:' ...)."""
    return "\n".join(l for l in t.split("\n") if not WIDGET.fullmatch(l.strip()))
```
3. **Action:** fix the text (delete the label line); the document is kept.
4. **Harm test:**

   | Test set | Documents changed | Documents dropped |
   |---|---|---|
   | Gold set (Data A/B) | pending: run by Data A/B | pending: run by Data A/B |
   | Proxy: 167 reviewed `clean` documents | 0 | 0 |

   The rule changes 9 of the 39 reviewed C1 documents.
5. **Side effects:** most reviewed C1 lines are not on the label list. Examples are `Store Information`, `Featured Manchester Subdivision Real Estate Properties`, `Posted by ... October 2, 2013` and `source: easemytrip`, which are site-specific. The list needs more labels as more packs are read. A real section titled `Contents` or `Next` on its own line would lose that line.

## Medicine 2: C4 two documents joined

1. **Disease:** C4, 26 documents. Examples:
   - `a79b9132feb9c66f`: `WikipediaMining is one` (offset 49)
   - `b8e726ed25bf4dfa`: `Related articlesPerfect time management` (offset 11813)
   - `73a72cdf38011c79`: `Each week we send a customized newsletter` (offset 3630)
2. **Medicine:** there is no safe fix, because the join point does not show where one text ends. Texts joined with no break leave one visible trace: a word run straight into the next one (`WikipediaMining`). The rule drops a document with two or more such places.
```python
def c4(t):
    """Drop a document with two or more places where one text is glued to the next with no break ('fansApril', 'WikipediaMining')."""
    glued = re.findall(r"\b[a-z]{3,}[.!?)\"]?[A-Z][a-z]{2,}\b", t)
    return None if len(glued) >= 2 else t
```
3. **Action:** drop the document. Splitting it would need the seam position and a quality decision on each half.
4. **Harm test:**

   | Test set | Documents changed | Documents dropped |
   |---|---|---|
   | Gold set (Data A/B) | pending: run by Data A/B | pending: run by Data A/B |
   | Proxy: 167 reviewed `clean` documents | 0 | 1 (`43c65ec608a359bf`) |

   The rule drops 6 of the 26 reviewed C4 documents.
5. **Side effects:** it misses most C4 documents, because many joins have a space or a line break at the seam. It drops a clean document that misses the space after a full stop twice (`video.With`).

## Medicine 3: C3 truncated document

1. **Disease:** C3, 23 documents. Examples:
   - `c5d61b53df104867`: ends `Example of operation [Read More >>>]` (offset 207)
   - `fb909c1fb77f3f90`: ends `She was actually one of my first...` (offset 136)
   - `87c9a4cea626e330`: ends `by using the following link:` (offset 977)
2. **Medicine:** drop a document whose last text ends in an ellipsis, `[...]` or `Read more`. These are the cuts that are safe to detect by code. An earlier rule dropped every document that does not end in `.`, `!` or `?`; it dropped 151 of 500 documents and failed. Adding a rule on the last word (`the`, `of`, `to`), which dropped 2 reviewed `clean` documents, or on a lowercase first letter, which brought the total to 2, went over the 1% limit, so both were left out.
```python
def c3(t):
    """Drop a document whose last text is cut off: it ends in an ellipsis, '[...]' or 'Read more'."""
    e = t.rstrip()
    return None if re.search(r"(?:\.\.\.|\u2026|\[\u2026\]|\[\.\.\.\])\W*$|(?i:read more)\W*$", e) else t
```
3. **Action:** drop the document.
4. **Harm test:**

   | Test set | Documents changed | Documents dropped |
   |---|---|---|
   | Gold set (Data A/B) | pending: run by Data A/B | pending: run by Data A/B |
   | Proxy: 167 reviewed `clean` documents | 0 | 1 (`d57d424ce49c5526`) |

   The rule drops 2 of the 23 reviewed C3 documents.
5. **Side effects:** it catches only 2 of 23. Cuts in the middle of a sentence (`...the remaining item`), cuts after a colon, and texts that start in the middle of a sentence stay in. A clean document that ends in `...` as a style choice is dropped.

## Medicine 4: C5 lists of keywords or links

1. **Disease:** C5, 16 documents. Examples:
   - `a79b9132feb9c66f`: `Comments About mining industry in sarawak` (offset 794)
   - `73a72cdf38011c79`: `transitional words comparing contrasting essay` (offset 1566)
   - `b8e726ed25bf4dfa`: `Animal abuse persuasive essay list thomas jefferson` (offset 12719)
2. **Medicine:** no safe fix. Reviewed C5 documents are search-snippet and essay-mill spam. The rule drops a document whose first line is a lowercase keyword string of three or more words, which is the typical title of that spam. Rules on repeated phrases and on the title repeated in the text were tested and flagged at least 9 reviewed `clean` documents, so they fail.
```python
def c5(t):
    """Drop a document whose first line is a lowercase keyword string of 3+ words ('mining industry in sarawak') - the title line of search-snippet spam."""
    first = next((l.strip() for l in t.split("\n") if l.strip()), "")
    return None if len(first.split()) >= 3 and first[0].islower() else t
```
3. **Action:** drop the document. Deleting the spam lines would leave almost nothing.
4. **Harm test:**

   | Test set | Documents changed | Documents dropped |
   |---|---|---|
   | Gold set (Data A/B) | pending: run by Data A/B | pending: run by Data A/B |
   | Proxy: 167 reviewed `clean` documents | 0 | 1 (`8f9a2abd4df5ce33`) |

   The rule drops 2 of the 16 reviewed C5 documents.
5. **Side effects:** it misses 14 of 16. A good document whose title starts in lowercase (`iPhone tips for beginners`) is dropped. C5 needs a model or a quality score, not a pattern.

## Medicine 5: D3 mixed language

1. **Disease:** D3, 6 documents. The guide says to label D3 and not to judge it, because mixing can be natural. Examples:
   - `29160f1b6b0823cf`: `行程速览` (offset 0), a Chinese tour-card header in front of English text
   - `3a8b5ee847c1afbc`: `продолжительность` (offset 4178), a Russian video line inside English text
   - `ae8a5a4fdf8d3351`: `коментариев` (offset 74), Russian comment counts inside English text
2. **Medicine:** do not fix real code-switching. The rule deletes only whole lines in which more than half of the letters are not Latin, in an English pack. A foreign word inside an English sentence stays.
```python
def d3(t):
    """Delete lines whose letters are mostly non-Latin (CJK, Cyrillic, Hangul, Devanagari ...) in an English document."""
    import unicodedata
    def foreign(l):
        letters = [c for c in l if c.isalpha()]
        return len(letters) >= 3 and sum(unicodedata.name(c, "").split(" ")[0] != "LATIN" for c in letters) / len(letters) > 0.5
    return "\n".join(l for l in t.split("\n") if not foreign(l))
```
3. **Action:** fix the text (delete the foreign lines); the document is kept.
4. **Harm test:**

   | Test set | Documents changed | Documents dropped |
   |---|---|---|
   | Gold set (Data A/B) | pending: run by Data A/B | pending: run by Data A/B |
   | Proxy: 167 reviewed `clean` documents | 0 | 0 |

   The rule changes 2 of the 6 reviewed D3 documents.
5. **Side effects:** a quoted line in another language, or a bilingual example, is deleted from a good document. Mixed sentences such as `3da0a9bbeeac1a6a` (Spanish and English in one sentence) are not fixed; they need a human decision.

## Diseases seen five times or fewer (no medicine sheet)

| Code | Documents | Note |
|---|---|---|
| B4 | 5 | the rule `b4` in `medicine.py` removes template slots; borderline, not counted as more than five |
| C2 | 5 | `c2` keeps the first copy of a line that occurs three or more times |
| F1 | 3 | all three are phone numbers or e-mail addresses; under the private-persons-only rule only `fab230d1a3b03a77` is clearly private, the others are spam or a business number. No medicine until the count is above five |
| A1 | 2 | `a1` deletes ZWSP, BOM, soft hyphen and bidi marks and keeps ZWJ/ZWNJ next to Indic letters |
| B5 | 2 | no automatic fix |
| A3, B2, D4 | 1 each | A3 can be re-decoded with `a3` |
