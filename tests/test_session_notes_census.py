"""Hold the four prose files against the shard files on disk, on every CI run.

WHY THIS EXISTS (Session 247, closing Session 246's what's-next #1).

``SESSION_NOTES.md`` is trimmed periodically: retired records move into frozen,
write-once shards under ``docs/architecture-history/``, each beside a
``.verify.sh`` proof. Those proofs carry fourteen ``L``-assertions that hold four
prose files -- ``CLAUDE.md``, ``README.md``, ``BACKLOG.md`` and
``docs/methodology/PROJECT_CONVENTIONS.md`` -- against the shard set.

**But every one of them resolves its prose operands from its OWN trim commit**
(``blob("%s:%s" % (sha, path))``). Only the shards and the proof scripts are read
from disk. Session 246 measured this with a control: corrupt any of the four
files in the working tree and all nine proofs stay GREEN; edit an ancestor shard
on disk and they go RED. So from the moment a trim commit lands, **no prose copy
the apparatus exists to keep in step is checked by anything** until the next trim
-- and 33 of the 42 commits that have touched these files since the first trim
fell in such a window.

Measured evidence that the gap is real, not theoretical: of the 19 literals the
SEVENTH trim's proof requires in these files, only **3** are still present in the
working tree. The eighth trim legitimately rewrote the rest. That proof is green
because it reads them at its own commit.

THE DESIGN, AND THE TWO RULINGS BEHIND IT (operator, 2026-08-25)

1. **pytest-in-CI, not another standalone ``.verify.sh``.** ``uv run pytest -q``
   already runs on every push and pull request, so this needs no ``ci.yml``
   change. It also means the guard must NOT touch git: ``actions/checkout@v4``
   is used here without ``fetch-depth``, i.e. a depth-1 shallow clone, so a
   git-derived fact would behave differently in CI than on a developer machine.
   **Everything below is derived from files on disk.**

2. **Fail-closed allowlist, not region markers.** Region markers would make a
   census claim written OUTSIDE a marked region invisible -- the same hole,
   relocated. Here every number token near shard vocabulary is in scope BY
   DEFAULT and must be either composed from the shards or explicitly frozen in
   ``FROZEN``. Forgetting is the failure mode this lineage keeps hitting
   (learnings #126, #186, #188), and only fail-closed catches forgetting.

Computed fields (Quarto ``.qmd``) were considered and ruled out: ``CLAUDE.md`` is
loaded raw by the agent harness, every session hand-edits these files, and eight
write-once proofs match literal byte strings inside them. More fundamentally a
computed field is fail-OPEN -- it fixes the numbers an author remembered to
template, and every incident here has been a number nobody noticed.

WHAT IS AND IS NOT GUARANTEED

``test_composed_census_claims_are_present`` COMPOSES each expected sentence from
the measured shards rather than comparing a declared integer against the prose
(learning #196), so a failure prints the exact sentence the file must contain.

``test_every_number_near_shard_vocabulary_is_classified`` is the fail-closed net.
It is fail-closed **for the claim shapes it scans** -- a number within
``WINDOW`` characters of "shard", or quantifying a shard-set head noun. A census
claim written with none of that vocabulary is NOT caught; that is the residual
hole and it is named here rather than papered over (learning #175).

Every entry in ``FROZEN`` is a per-OCCURRENCE string, never a whole-file
exemption: learning #135 records that exempting a file lets every live line
inside it ride in free.

NEUTER LOOP, published rather than merely run (learnings #125, #141, #198). Remove one
check; do any mutants then survive?  Re-derived after the last edit to this file.

    check_tiling         LOAD-BEARING, sole catcher of M16
    check_proofs         LOAD-BEARING, sole catcher of M14
    check_banners        LOAD-BEARING, sole catcher of M17
    check_composed       LOAD-BEARING, sole catcher of M03, M05, M06, M08, M11, M12, M15
    check_filename_sets  LOAD-BEARING, sole catcher of M02
    check_scan           LOAD-BEARING, sole catcher of M09
    check_frozen         LOAD-BEARING, sole catcher of M10

    mutants: 17      checks: 7      survivors with all checks present: none

M16 and M17 exist only to isolate check_tiling and check_banners. Every other way of
breaking a span or a banner also makes the prose disagree with the filenames, so
check_composed catches it first and those two could be deleted with the suite still
green. Both mutants therefore make the MISTAKE CONSISTENT -- they rewrite all four
prose files to agree with the broken tree -- which is the realistic failure: a trim
that mis-cuts and then documents its own mistake faithfully.

A CONTROL, run both ways so a green result means something. With CLAUDE.md's
shard count corrupted 8 to 5 and one routing clause widened, all nine
docs/architecture-history/*.verify.sh proofs stay GREEN and this module goes RED
on check_composed and check_scan. That is the hole this file exists to close,
measured in both directions rather than asserted.
"""

from __future__ import annotations

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
ARCHIVE_SUBDIR = pathlib.PurePosixPath("docs/architecture-history")

CLAUDE = "CLAUDE.md"
README = "README.md"
BACKLOG = "BACKLOG.md"
CONVENTIONS = "docs/methodology/PROJECT_CONVENTIONS.md"
PROSE_FILES = (CLAUDE, README, BACKLOG, CONVENTIONS)

# The first shard's banner predates the "(Session N, date)" convention that every
# later banner carries, so its trim session is the one fact here that cannot be
# read off an artifact. It is declared once, and
# ``test_only_the_first_shard_banner_omits_its_trim_session`` fails if any OTHER
# banner ever omits one -- so this exception cannot silently widen.
FIRST_SHARD_TRIM_SESSION = 222

SPELLED = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
    8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
    13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen",
}
ORDINAL = {
    1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth",
    7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth", 11: "eleventh",
    12: "twelfth", 13: "thirteenth", 14: "fourteenth", 15: "fifteenth",
    16: "sixteenth",
}

_RECORD_HEADING = re.compile(r"^### What Session \S+ Did$")
_RANGE_NAME = re.compile(r"^SESSION_NOTES-S(\d+)-through-S(\d+)\.md$")
_FIRST_NAME = re.compile(r"^SESSION_NOTES-through-S(\d+)\.md$")
_BANNER_TRIM = re.compile(r"\(Session (\d+),")

# A shard filename, excluding the ``.verify.sh`` proof beside it. The negative
# lookahead is load-bearing and is inherited from the proof lineage: without it
# this also matches the ``.md`` PREFIX inside ``...-S224-through-S221.md.verify.sh``.
SHARD_NAME = re.compile(r"SESSION_NOTES-[A-Za-z0-9-]*\.md(?!\.verify)")


class Shard:
    """One frozen shard, with every fact measured from the file itself."""

    def __init__(self, path: pathlib.Path) -> None:
        self.path = path
        self.name = path.name
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.lines = len(lines)
        self.records_lines = next(
            (len(lines) - index for index, line in enumerate(lines)
             if _RECORD_HEADING.match(line)), None)
        ranged = _RANGE_NAME.match(self.name)
        if ranged:
            self.newest, self.oldest = int(ranged.group(1)), int(ranged.group(2))
            self.is_first = False
        else:
            first = _FIRST_NAME.match(self.name)
            assert first, f"shard filename matches no declared naming rule: {self.name}"
            self.newest, self.oldest, self.is_first = int(first.group(1)), 1, True
        banner = _BANNER_TRIM.search("\n".join(text.splitlines()[:14]))
        self.banner_trim_session = int(banner.group(1)) if banner else None
        self.proof = path.with_name(path.name + ".verify.sh")

    @property
    def trim_session(self) -> int:
        if self.banner_trim_session is not None:
            return self.banner_trim_session
        return FIRST_SHARD_TRIM_SESSION


def shards(root: pathlib.Path = REPO_ROOT) -> list[Shard]:
    """Every shard on disk, oldest cut first. Globbed, never hand-declared."""
    archive = root / ARCHIVE_SUBDIR
    found = sorted(archive.glob("SESSION_NOTES-*.md"))
    assert found, f"no SESSION_NOTES shards under {archive}"
    return sorted((Shard(p) for p in found), key=lambda s: s.oldest)


def _n(value: int) -> str:
    """Thousands-separated, matching how these files print every line count."""
    return format(value, ",")


def _article(word: str) -> str:
    return "an" if word[0] in "aeiou" else "a"


def _join_and(parts: list[str]) -> str:
    """``a, b and c`` -- the serial form these files use (no Oxford comma)."""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]



def _records_lines(shard: Shard) -> int:
    """Lines in the shard's RECORDS zone -- first record heading to EOF.

    The declared grammar of this lineage: a record is a heading-delimited byte
    span, ``\\S+`` not ``\\d+`` (else Sessions 20B and 20A merge) and ``Did$``
    anchored (else ``### What Session N should do`` headings become phantoms).
    """
    lines = shard.path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if _RECORD_HEADING.match(line):
            return len(lines) - index
    raise AssertionError(f"no record heading found in {shard.name}")


class Expectation:
    """One sentence the prose must contain, COMPOSED from the shards on disk."""

    def __init__(self, path: str, pattern: str, *, literal: bool = True,
                 count: int = 1, why: str = "") -> None:
        self.path = path
        self.pattern = pattern
        self.literal = literal
        self.count = count
        self.why = why

    def finditer(self, text: str):
        if self.literal:
            start = 0
            while True:
                found = text.find(self.pattern, start)
                if found < 0:
                    return
                yield found, found + len(self.pattern)
                start = found + 1
        else:
            for match in re.finditer(self.pattern, text):
                yield match.start(), match.end()

    def spans(self, text: str) -> list[tuple[int, int]]:
        return list(self.finditer(text))

    def __repr__(self) -> str:
        kind = "literal" if self.literal else "regex"
        return f"<{self.path} {kind} {self.pattern[:60]!r}>"


def expectations(found: list[Shard]) -> list[Expectation]:
    """Every census sentence, composed from the measured shard set."""
    total = len(found)
    word, prior_word = SPELLED[total], SPELLED[total - 1]
    trims = [shard.trim_session for shard in found]
    trim_list = ", ".join(str(session) for session in trims)
    live_from = found[-1].newest + 1
    out: list[Expectation] = []

    def add(path: str, pattern: str, why: str, **kw) -> None:
        out.append(Expectation(path, pattern, why=why, **kw))

    # ---- how many shards there are, stated five ways in CLAUDE.md -----------
    add(CLAUDE, f"**Trimmed {word} times (Sessions {trim_list}):**",
        "the Key Files line's trim count and session list")
    add(CLAUDE, f"### `SESSION_NOTES.md` is trimmed (Sessions {trim_list})",
        "the trimmed-file section heading")
    add(CLAUDE, f"Retired records live in **{word}** write-once shards",
        "the shard count in the Key Files line")
    add(CLAUDE, f"grep *all {word}*",
        "the instruction to grep every shard")
    add(CLAUDE, f"there are {word.upper()}, and a lookup must consult all of them",
        "the shard-census sentence the routing table hangs off")
    add(CLAUDE, f"(The {prior_word} newer shards are under the 2,000-line cap today;",
        "the count of shards newer than the first (N-1), not N")
    add(README, f"older in the {word} shards above",
        "the repo map's pointer from the live ledger to the shards")
    add(BACKLOG, f"there are now **{word}** unwatched shards",
        "the read-cap item's shard count")
    add(BACKLOG, f"the {prior_word} newer ones read whole today",
        "the read-cap item's N-1 count")
    add(CONVENTIONS, f"**{word.capitalize()} instances so far**",
        "the shard-naming rule's instance count")

    # ---- which sessions performed a trim ------------------------------------
    add(BACKLOG, f"**Sessions {_join_and([str(s) for s in trims[1:]])} widened this:**",
        "the read-cap item's list of widening trims (every trim after the first)")
    chain = [f"Session {trims[1]} made it two archives"]
    for index in range(3, total + 1):
        ordinal = ORDINAL[index]
        chain.append(f"Session {trims[index - 1]} {_article(ordinal)} {ordinal}")
    add(BACKLOG, _join_and(chain) + "**",
        "the read-cap item's ordinal chain -- its LAST element is the live count")
    conv_chain = _join_and([ORDINAL[i] for i in range(3, total + 1)])
    add(CONVENTIONS, f"**the {conv_chain} trims all did**",
        "the naming rule's evidence chain -- its last ordinal is the live count")

    # ---- per-shard span and size, one shard at a time ------------------------
    for shard in found:
        span = (f"Sessions {shard.newest}→1" if shard.is_first
                else f"{shard.newest}→{shard.oldest}")
        add(CLAUDE, f"`{shard.name}` ({span}, {_n(shard.lines)} lines)",
            f"CLAUDE.md's shard list entry for {shard.name}")
        add(CONVENTIONS,
            f"`{shard.name}` (Session {shard.trim_session}, "
            f"Sessions {shard.newest}→{shard.oldest})",
            f"the naming rule's entry for {shard.name}")
        arrow = f"{shard.newest}->{shard.oldest}" if not shard.is_first else f"{shard.newest}->1"
        add(README,
            re.escape(shard.name) + r" +# frozen SESSION_NOTES records, Sessions "
            + re.escape(arrow),
            f"README.md's repo-map line for {shard.name}", literal=False)
        if shard.is_first:
            add(BACKLOG,
                f"**{_n(_records_lines(shard))} record lines** ({_n(shard.lines)} total)",
                "BACKLOG.md's record-lines/total pair for the first shard")
        else:
            add(BACKLOG, f"`{shard.name}` ({_n(shard.lines)} lines)",
                f"BACKLOG.md's size entry for {shard.name}")

    # ---- the aggregate size list in BACKLOG.md's read-cap item ---------------
    middle = _join_and([_n(s.lines) for s in found[1:-1]])
    add(BACKLOG,
        f"({middle} lines for the second through {ORDINAL[total - 1]}, "
        f"{_n(found[-1].lines)} for the {ORDINAL[total]})",
        "the read-cap item's aggregate size list for shards 2..N")

    # ---- the routing table --------------------------------------------------
    for shard in found:
        clause = (f"**N ≤ {shard.newest}** → `{shard.name}`" if shard.is_first
                  else f"**{shard.oldest} ≤ N ≤ {shard.newest}** → `{shard.name}`")
        add(CLAUDE, clause, f"routing clause for {shard.name}")
    add(CLAUDE, f"**N ≥ {live_from}** → `SESSION_NOTES.md`",
        "routing clause sending the newest sessions to the live ledger")
    return out


# ---------------------------------------------------------------------------
# The fail-closed net.
# ---------------------------------------------------------------------------

NUMBER = re.compile(
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen)\b|\b\d[\d,]*\b", re.I)

# "shard" is the head noun of every census claim. WINDOW was chosen by
# measurement, not taste: at +-60 characters the scan returns 127 candidates in
# these four files, most of them numbers that merely sit in a paragraph about
# trims (section references, the 2,000-line read cap, "shape 5 of the 20
# proofs") -- allowlisting those as "frozen census prose" would empty the word
# allowlist of meaning (learning #135). At +-30 it returns 22, and every one is
# a real statement about the shard set or a nearby historical record.
VOCABULARY = re.compile(r"shard", re.I)
WINDOW = 30

# A number quantifying a shard-set head noun, wherever it sits. This arm catches
# "Eight instances so far", which says nothing about "shards" within WINDOW.
HEAD_NOUN = re.compile(
    r"(?:\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen)\b|\b\d[\d,]*\b)"
    r"[*_` ]{0,4}\s*(?:newer\s+|unwatched\s+|write-once\s+|older\s+)*"
    r"(?:shards?|instances so far)\b", re.I)

# Every occurrence that is in scope BY PROXIMITY but is not a claim about the
# current shard census. Three kinds live here, and each entry says which it is:
# a frozen historical record (true when written and true now), a number about a
# different subject that happens to sit near the word "shard", and a count this
# repository states about something other than the shard set. Per-OCCURRENCE
# strings, never whole-file exemptions (learning #135). Each is asserted to still
# be present by test_frozen_entries_are_still_present, so the list cannot rot --
# reword the sentence and the companion test sends you back here.
FROZEN: tuple[tuple[str, str, str], ...] = (
    (CLAUDE, "(The seven newer shards are under the 2,000-line cap today; that is luck",
     "the 2,000-line read cap is a constant, not a shard count; the 'seven' in "
     "this same sentence IS composed above"),
    (CLAUDE, "never appends to an existing one — which is why every shard after the first",
     "'one' is a pronoun for a shard file, not a count of shards"),
    (CLAUDE, "drops both), and two cite shard filenames inside frozen historical",
     "frozen: Session 239's sweep result, a count of FILES not shards"),
    (CLAUDE, "the S220 shard's banner says `N ≥ 221` → the live file",
     "frozen: quotes the S220 banner's own (now falsified, unrepairable) clause"),
    (CLAUDE, "the S224 shard's routes Sessions 225 and up to the live file",
     "frozen: records what the S224 banner says, not what routing is now"),
    (CLAUDE, "the S227 shard's routes Sessions 228 and up there too",
     "frozen: records what the S227 banner says"),
    (CLAUDE, "the S231 shard's routes Sessions 232 and up",
     "frozen: records what the S231 banner says"),
    (CLAUDE, "the S235 shard's routes Sessions 236 and up",
     "frozen: records what the S235 banner says"),
    (CLAUDE, "just the newest shard). Session 235 added **L10**",
     "frozen: which session added which assertion"),
    (CLAUDE, "any other). Session 242 added **L13** (a shard's own FILENAME",
     "frozen: which session added which assertion"),
    (CLAUDE, "a misnamed shard satisfies L5/3, L5/4 and L8/set together",
     "'L5/3' and 'L5/4' are assertion names, not counts"),
    (CLAUDE, "corrects the gotcha Session 245 left: every shard proof resolves",
     "frozen: a session number, not a count"),
    (CLAUDE, "`CLAUDE.md` (this one) included. Only the shards and the proof scripts",
     "'one' is a pronoun for this file"),
    (README, "L9 (write-once for all four shards)",
     "frozen: describes what the FOURTH trim's proof does, and that proof guards "
     "four shards. Not stale -- a count word is stale only if it claims the present"),
    (BACKLOG, "(The 924 figure this item carried for the\nthird shard was wrong; "
     "933 is the measured `wc -l`.)",
     "frozen: records that Session 228 typed 924 where the measured value is 933. "
     "Both numerals are part of that historical correction; the 933 is separately "
     "composed above as this shard's live size"),
    (CONVENTIONS, "**Ledger shards are the one exception (Session 222).**",
     "'one exception' counts exceptions to a convention, not shards"),
    (README, "test_session_notes_census.py          # shard-census guard: the four "
     "prose files vs the shards on disk (25 tests)",
     "this guard's own README row: 'four' counts prose files and '25' counts "
     "tests, neither is a shard census. Adding a mutant makes this literal stale "
     "and the companion test then requires both numbers to be brought back "
     "into step -- which is the README count policing itself"),
)


def _read(path: str, root: pathlib.Path = REPO_ROOT) -> str:
    return (root / path).read_text(encoding="utf-8")


class Census:
    """One snapshot of a tree: its shards, the composed sentences, the prose.

    Built once and passed to every check. The shards are read exactly once --
    the first is 24,590 lines, and rebuilding this per check turned a 3-second
    suite into a multi-minute one.
    """

    def __init__(self, root: pathlib.Path) -> None:
        self.root = root
        self.shards = shards(root)
        self.expectations = expectations(self.shards)
        self.texts = {path: _read(path, root) for path in PROSE_FILES}


def _covered_spans(census: Census, path: str, text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for expectation in census.expectations:
        if expectation.path == path:
            spans.extend(expectation.spans(text))
    for frozen_path, literal, _why in FROZEN:
        if frozen_path != path:
            continue
        start = 0
        while True:
            found = text.find(literal, start)
            if found < 0:
                break
            spans.append((found, found + len(literal)))
            start = found + 1
    return spans


def _in_scope(text: str, start: int, end: int, head_starts: frozenset[int]) -> bool:
    """``head_starts`` is precomputed per text: scanning for head nouns once per
    CANDIDATE instead of once per file turned this suite from seconds into
    minutes, because these files carry hundreds of number tokens."""
    if VOCABULARY.search(text[max(0, start - WINDOW):end + WINDOW]):
        return True
    return start in head_starts


# ---------------------------------------------------------------------------
# The checks. Each returns a list of human-readable problems; empty means pass.
# They take a root so the mutants further down can run them against a mutated
# mirror of this repository -- a guard that has never been observed to FAIL
# proves less than it appears to (learning #168).
# ---------------------------------------------------------------------------

def check_tiling(census: Census) -> list[str]:
    """The routing table is only usable if the spans partition the sessions."""
    found = census.shards
    problems = []
    for earlier, later in zip(found, found[1:], strict=False):
        if earlier.newest + 1 != later.oldest:
            problems.append(
                f"{earlier.name} ends at {earlier.newest} but {later.name} "
                f"starts at {later.oldest}")
    return problems


def check_proofs(census: Census) -> list[str]:
    missing = [s.name for s in census.shards if not s.proof.exists()]
    return [f"{name} has no .verify.sh beside it" for name in missing]


def check_banners(census: Census) -> list[str]:
    """FIRST_SHARD_TRIM_SESSION is the one hand-declared fact in this module.
    This keeps that exception from widening: every later banner must name its
    own trim session, so the declaration can never come to cover a second shard.
    """
    return [f"{s.name}'s banner does not name the trim session that created it"
            for s in census.shards if s.banner_trim_session is None and not s.is_first]


def check_composed(census: Census) -> list[str]:
    """Each expected sentence is COMPOSED from the shards, then required.

    Not "the prose holds a number equal to a declared integer" -- the whole
    sentence is built from the measurement, so a failure prints the exact text
    the file must carry (learning #196).
    """
    problems = []
    for expectation in census.expectations:
        seen = len(expectation.spans(census.texts[expectation.path]))
        if seen != expectation.count:
            kind = "literal" if expectation.literal else "regex"
            problems.append(
                f"{expectation.path}: expected {expectation.count} occurrence(s) "
                f"of this {kind}, found {seen}\n"
                f"      {expectation.pattern!r}\n"
                f"      ({expectation.why})")
    return problems


def check_filename_sets(census: Census) -> list[str]:
    """Set equality, not membership.

    Requiring each shard on disk to be named leaves a file free to ALSO name a
    shard that does not exist -- the defect Session 246's review found in C3,
    where a fabricated table row passed every assertion because the check
    iterated the declarations and never the document.
    """
    on_disk = {s.name for s in census.shards}
    problems = []
    for path in PROSE_FILES:
        named = set(SHARD_NAME.findall(census.texts[path]))
        if named != on_disk:
            problems.append(
                f"{path}: names {sorted(named - on_disk)} that are not on disk; "
                f"omits {sorted(on_disk - named)}")
    return problems


def check_scan(census: Census) -> list[str]:
    """The fail-closed net: nothing near the census is unaccounted for.

    Every number token within WINDOW characters of "shard", or quantifying a
    shard-set head noun, must fall inside either a COMPOSED expectation or a
    FROZEN entry. A new sentence of either kind therefore fails until someone
    classifies it -- which is the point, because every incident in this lineage
    has been a number nobody noticed rather than a number typed wrong.
    """
    problems = []
    for path in PROSE_FILES:
        text = census.texts[path]
        covered = _covered_spans(census, path, text)
        head_starts = frozenset(m.start() for m in HEAD_NOUN.finditer(text))
        for match in NUMBER.finditer(text):
            start, end = match.start(), match.end()
            if not _in_scope(text, start, end, head_starts):
                continue
            if any(lo <= start and end <= hi for lo, hi in covered):
                continue
            context = text[max(0, start - 70):end + 60].replace("\n", " ")
            problems.append(f"{path} @{start} {match.group(0)!r}\n      …{context}…")
    return problems


def check_frozen(census: Census) -> list[str]:
    """A FROZEN entry that matches nothing is a hole, not a comment.

    Same discipline as tests/test_wiki_no_line_citations.py's stale-allowlist
    companion: an exemption whose subject has been reworded or deleted must be
    removed, or it silently exempts nothing while looking like coverage.
    """
    stale = []
    for path, literal, why in FROZEN:
        seen = census.texts[path].count(literal)
        if seen != 1:
            stale.append(f"{path}: found {seen} occurrence(s), want exactly 1\n"
                         f"      {literal!r}\n      ({why})")
    return stale


CHECKS = {
    "tiling": check_tiling,
    "proofs": check_proofs,
    "banners": check_banners,
    "composed": check_composed,
    "filename_sets": check_filename_sets,
    "scan": check_scan,
    "frozen": check_frozen,
}


# ---------------------------------------------------------------------------
# The live tests -- each check, run against this repository.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def census() -> Census:
    """One snapshot of this repository, shared by every live test."""
    return Census(REPO_ROOT)


def test_shard_spans_tile_without_gap_or_overlap(census) -> None:
    problems = check_tiling(census)
    assert not problems, (
        "Shard spans do not tile -- a session number is routed to two files or "
        "to none:\n  - " + "\n  - ".join(problems))


def test_every_shard_has_its_proof_on_disk(census) -> None:
    problems = check_proofs(census)
    assert not problems, (
        "Shard(s) with no .verify.sh beside them -- the losslessness claim for "
        "these has nothing behind it:\n  - " + "\n  - ".join(problems))


def test_only_the_first_shard_banner_omits_its_trim_session(census) -> None:
    problems = check_banners(census)
    assert not problems, (
        "Shard banner(s) do not name the trim session that created them, so "
        "that trim session is now underivable and this guard would need a "
        "second hand-declared constant:\n  - " + "\n  - ".join(problems))


def test_composed_census_claims_are_present(census) -> None:
    problems = check_composed(census)
    assert not problems, (
        f"{len(problems)} census claim(s) in the prose no longer match the "
        "shards on disk. Each string below was COMPOSED from the shard files -- "
        "update the prose to match it, or fix the shards:\n\n  - "
        + "\n\n  - ".join(problems))


def test_shard_filename_sets_match_disk(census) -> None:
    problems = check_filename_sets(census)
    assert not problems, (
        "Shard filename set(s) in the prose disagree with the shards on disk:"
        "\n  - " + "\n  - ".join(problems))


def test_every_number_near_shard_vocabulary_is_classified(census) -> None:
    problems = check_scan(census)
    assert not problems, (
        f"{len(problems)} number(s) near shard vocabulary are neither composed "
        "from the shards nor listed in FROZEN. Classify each: if it states the "
        "CURRENT shard census, add a composed expectation so it is checked; if "
        "it is a frozen historical record, add it to FROZEN with the reason."
        "\n\n  - " + "\n\n  - ".join(problems))


def test_frozen_entries_are_still_present(census) -> None:
    problems = check_frozen(census)
    assert not problems, (
        "Stale FROZEN entry/entries -- the prose they exempt has been reworded, "
        "duplicated or deleted. Re-read the sentence and either update the entry "
        "or drop it so the scan covers that text again:\n\n  - "
        + "\n\n  - ".join(problems))


# ---------------------------------------------------------------------------
# Mutants. Proof that this guard can FAIL.
#
# These are the pytest equivalent of the ``--self-test`` every proof in
# docs/architecture-history/ ships, and they run in CI rather than on request.
# Each mutant mirrors the repository into a tmp_path, breaks exactly one thing,
# and asserts that the named check reports it.
#
# Every mutation asserts its own anchor text is present before substituting, so
# a later rewording turns the mutant RED rather than silently vacuous -- the
# failure mode recorded as learning #172.
# ---------------------------------------------------------------------------

MIRRORED = PROSE_FILES + (str(ARCHIVE_SUBDIR),)


def _mirror(tmp_path: pathlib.Path) -> pathlib.Path:
    """A copy of every file these checks read. ~25 ms."""
    import shutil

    root = tmp_path / "mirror"
    for relative in PROSE_FILES:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)
    shutil.copytree(REPO_ROOT / ARCHIVE_SUBDIR, root / ARCHIVE_SUBDIR)
    return root


def _sub(root: pathlib.Path, relative: str, old: str, new: str) -> None:
    """Substitute, asserting the anchor exists exactly once first."""
    target = root / relative
    text = target.read_text(encoding="utf-8")
    assert text.count(old) == 1, (
        f"mutant anchor is not unique in {relative} ({text.count(old)} "
        f"occurrences) -- the mutant would be vacuous: {old[:70]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def _shard_path(root: pathlib.Path, stem: str) -> pathlib.Path:
    return root / ARCHIVE_SUBDIR / stem


# --- the mutations ---------------------------------------------------------

def _m01_delete_a_shard(root: pathlib.Path) -> None:
    _shard_path(root, "SESSION_NOTES-S227-through-S225.md").unlink()


def _m02_prose_names_a_shard_that_does_not_exist(root: pathlib.Path) -> None:
    _sub(root, README, "older in the eight shards above",
         "older in the eight shards above, and SESSION_NOTES-S999-through-S998.md")


def _m03_a_shard_grows_by_one_line(root: pathlib.Path) -> None:
    target = _shard_path(root, "SESSION_NOTES-S220-through-S217.md")
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")


def _m04_claude_shard_count_is_wrong(root: pathlib.Path) -> None:
    _sub(root, CLAUDE, "Retired records live in **eight** write-once shards",
         "Retired records live in **nine** write-once shards")


def _m05_a_routing_clause_is_wrong(root: pathlib.Path) -> None:
    _sub(root, CLAUDE, "**221 ≤ N ≤ 224**", "**221 ≤ N ≤ 225**")


def _m06_backlog_size_figure_is_wrong(root: pathlib.Path) -> None:
    _sub(root, BACKLOG, "`SESSION_NOTES-S220-through-S217.md` (804 lines)",
         "`SESSION_NOTES-S220-through-S217.md` (805 lines)")


def _m07_conventions_instance_count_is_wrong(root: pathlib.Path) -> None:
    _sub(root, CONVENTIONS, "**Eight instances so far**", "**Seven instances so far**")


def _m08_readme_repo_map_span_is_wrong(root: pathlib.Path) -> None:
    _sub(root, README,
         "SESSION_NOTES-S241-through-S239.md    # frozen SESSION_NOTES records, Sessions 241->239",
         "SESSION_NOTES-S241-through-S239.md    # frozen SESSION_NOTES records, Sessions 241->240")


def _m09_a_new_unclassified_census_sentence(root: pathlib.Path) -> None:
    target = root / CLAUDE
    target.write_text(
        target.read_text(encoding="utf-8")
        + "\n\nThere are three shards, and a lookup must consult all of them.\n",
        encoding="utf-8")


def _m10_a_frozen_entry_loses_its_subject(root: pathlib.Path) -> None:
    _sub(root, README, "L9 (write-once for all four shards)", "L9 (write-once)")


def _m11_a_composed_sentence_is_duplicated(root: pathlib.Path) -> None:
    _sub(root, CLAUDE, "grep *all eight* — none is a prefix of another.",
         "grep *all eight* — none is a prefix of another. grep *all eight*.")


def _m12_a_banner_names_the_wrong_trim_session(root: pathlib.Path) -> None:
    target = _shard_path(root, "SESSION_NOTES-S241-through-S239.md")
    text = target.read_text(encoding="utf-8")
    assert text.count("(Session 245, ") == 1
    target.write_text(text.replace("(Session 245, ", "(Session 244, ", 1), encoding="utf-8")


def _m13_a_banner_loses_its_trim_session(root: pathlib.Path) -> None:
    target = _shard_path(root, "SESSION_NOTES-S238-through-S236.md")
    text = target.read_text(encoding="utf-8")
    assert text.count("(Session 242, ") == 1
    target.write_text(text.replace("(Session 242, ", "(the seventh trim, ", 1),
                      encoding="utf-8")


def _m14_a_proof_is_deleted(root: pathlib.Path) -> None:
    _shard_path(root, "SESSION_NOTES-S231-through-S228.md.verify.sh").unlink()


def _m15_the_aggregate_size_list_is_wrong(root: pathlib.Path) -> None:
    _sub(root, BACKLOG, "1,057 and 644 lines for the second through seventh",
         "1,057 and 645 lines for the second through seventh")


def _m16_a_consistent_mis_cut(root: pathlib.Path) -> None:
    """A trim that mis-cuts AND writes prose agreeing with its own mistake.

    This is the only mutant that isolates check_tiling. Every other break in
    the span structure also makes the prose disagree with the filenames, so
    check_composed or check_filename_sets catches it first and tiling could be
    deleted with the suite still green. Here the shard is renamed to cover
    225-226 instead of 225-227 and ALL FOUR prose files are updated to match,
    so every other check passes and Session 227 is routed to no file at all.
    """
    old_stem = "SESSION_NOTES-S227-through-S225.md"
    new_stem = "SESSION_NOTES-S226-through-S225.md"
    archive = root / ARCHIVE_SUBDIR
    (archive / old_stem).rename(archive / new_stem)
    (archive / (old_stem + ".verify.sh")).rename(archive / (new_stem + ".verify.sh"))
    for relative, pairs in (
        (CLAUDE, ((old_stem, new_stem), ("227→225", "226→225"),
                  ("225 ≤ N ≤ 227", "225 ≤ N ≤ 226"))),
        (README, ((old_stem, new_stem), ("Sessions 227->225", "Sessions 226->225"))),
        (BACKLOG, ((old_stem, new_stem),)),
        (CONVENTIONS, ((old_stem, new_stem), ("Sessions 227→225", "Sessions 226→225"))),
    ):
        target = root / relative
        text = target.read_text(encoding="utf-8")
        for old, new in pairs:
            assert old in text, (
                f"mis-cut mutant anchor {old!r} is absent from {relative} -- the "
                "prose was reworded and this mutant would be vacuous")
            text = text.replace(old, new)
        target.write_text(text, encoding="utf-8")


def _m17_a_bannerless_shard_with_prose_that_agrees(root: pathlib.Path) -> None:
    """A banner stops naming its trim session AND the prose is written to match
    the wrong value the fallback then derives.

    This is the only mutant that isolates check_banners. Strip a banner alone
    and check_composed catches it, because the derived trim list stops matching
    the prose -- so check_banners could be deleted with the suite still green.
    The real risk is subtler: FIRST_SHARD_TRIM_SESSION silently becomes the
    answer for a SECOND shard, and an author who trusts the derivation writes
    prose agreeing with it. Then only check_banners can tell.
    """
    target = _shard_path(root, "SESSION_NOTES-S238-through-S236.md")
    text = target.read_text(encoding="utf-8")
    assert text.count("(Session 242, ") == 1
    target.write_text(text.replace("(Session 242, ", "(the seventh trim, ", 1),
                      encoding="utf-8")
    fallback = str(FIRST_SHARD_TRIM_SESSION)
    for relative, pairs in (
        (CLAUDE, (("**Trimmed eight times (Sessions 222, 224, 228, 231, 235, 239, 242, 245):**",
                   "**Trimmed eight times (Sessions 222, 224, 228, 231, 235, 239, "
                   + fallback + ", 245):**"),
                  ("is trimmed (Sessions 222, 224, 228, 231, 235, 239, 242, 245)",
                   "is trimmed (Sessions 222, 224, 228, 231, 235, 239, "
                   + fallback + ", 245)"))),
        (BACKLOG, (("**Sessions 224, 228, 231, 235, 239, 242 and 245 widened this:**",
                    "**Sessions 224, 228, 231, 235, 239, " + fallback
                    + " and 245 widened this:**"),
                   ("Session 242 a seventh", "Session " + fallback + " a seventh"))),
        (CONVENTIONS, (("`SESSION_NOTES-S238-through-S236.md` (Session 242,",
                        "`SESSION_NOTES-S238-through-S236.md` (Session " + fallback + ","),)),
    ):
        for old, new in pairs:
            _sub(root, relative, old, new)


MUTANTS: tuple[tuple[str, str, object, str], ...] = (
    ("M01", "a shard is deleted from disk", _m01_delete_a_shard, "tiling"),
    ("M02", "prose names a shard that does not exist",
     _m02_prose_names_a_shard_that_does_not_exist, "filename_sets"),
    ("M03", "a shard grows by one line", _m03_a_shard_grows_by_one_line, "composed"),
    ("M04", "CLAUDE.md's shard count is wrong", _m04_claude_shard_count_is_wrong, "composed"),
    ("M05", "a routing clause is wrong", _m05_a_routing_clause_is_wrong, "composed"),
    ("M06", "BACKLOG.md's size figure for a shard is wrong",
     _m06_backlog_size_figure_is_wrong, "composed"),
    ("M07", "PROJECT_CONVENTIONS.md's instance count is wrong",
     _m07_conventions_instance_count_is_wrong, "composed"),
    ("M08", "README.md's repo-map span is wrong", _m08_readme_repo_map_span_is_wrong,
     "composed"),
    ("M09", "a new, unclassified census sentence appears",
     _m09_a_new_unclassified_census_sentence, "scan"),
    ("M10", "a FROZEN entry's subject is reworded away",
     _m10_a_frozen_entry_loses_its_subject, "frozen"),
    ("M11", "a composed sentence is duplicated", _m11_a_composed_sentence_is_duplicated,
     "composed"),
    ("M12", "a shard banner names the wrong trim session",
     _m12_a_banner_names_the_wrong_trim_session, "composed"),
    ("M13", "a non-first banner loses its trim session",
     _m13_a_banner_loses_its_trim_session, "banners"),
    ("M14", "a shard's proof is deleted", _m14_a_proof_is_deleted, "proofs"),
    ("M15", "the aggregate size list is wrong", _m15_the_aggregate_size_list_is_wrong,
     "composed"),
    ("M16", "a mis-cut whose prose agrees with the mistake",
     _m16_a_consistent_mis_cut, "tiling"),
    ("M17", "a bannerless shard whose prose agrees with the fallback",
     _m17_a_bannerless_shard_with_prose_that_agrees, "banners"),
)


def _fired(root: pathlib.Path) -> set[str]:
    """Which checks report a problem against this (mutated) root."""
    fired = set()
    try:
        census = Census(root)
    except AssertionError:
        return set(CHECKS)          # structurally unreadable: every check is void
    for name, check in CHECKS.items():
        try:
            if check(census):
                fired.add(name)
        except AssertionError:
            # A mutation can make the tree structurally unreadable (e.g. every
            # shard removed). That is a caught mutant, not a harness error.
            fired.add(name)
    return fired


@pytest.mark.parametrize(
    ("mutant_id", "description", "mutate", "expected"),
    MUTANTS, ids=[m[0] for m in MUTANTS])
def test_mutant_is_caught(tmp_path, mutant_id, description, mutate, expected) -> None:
    root = _mirror(tmp_path)
    assert not _fired(root), (
        f"{mutant_id}: the pristine mirror is already failing, so this mutant "
        "would prove nothing. The mirror is incomplete.")
    mutate(root)
    fired = _fired(root)
    others = sorted(fired) or ["NONE -- the mutant survived every check, which "
                               "is the failure this suite exists to prevent"]
    assert expected in fired, (
        f"{mutant_id} ({description}) was NOT caught by check_{expected}. "
        f"Checks that did fire: {others}")


def test_every_check_is_reached_by_some_mutant(tmp_path) -> None:
    """No dead checks.

    Session 224 shipped an assertion (``L2/b0``) that no mutant could reach, and
    Session 228 shipped the same defect one level down (``L5/2``); both were
    found only by asking, per assertion, whether anything exercised it. This
    test asks that question mechanically and fails if a check is unreachable --
    a check nothing can trip is decoration, not coverage.
    """
    reached: set[str] = set()
    for mutant_id, _description, mutate, _expected in MUTANTS:
        root = _mirror(tmp_path / mutant_id)
        mutate(root)
        reached |= _fired(root)
    unreached = sorted(set(CHECKS) - reached)
    assert not unreached, (
        f"check(s) {unreached} are reached by no mutant in MUTANTS. Either add "
        "a mutant that breaks what they guard, or delete them -- an assertion "
        "no mutant can reach proves nothing.")
