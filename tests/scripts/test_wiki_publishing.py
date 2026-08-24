"""Tests for the wiki-publishing pair: scripts/publish_wiki.sh + .githooks/post-commit.

Both files shipped untested. Both run **unattended, from a git hook**, and both
failed open — which is why the two BACKLOG items they close were filed together
and executed together (Session 241).

What is pinned here:

* ``publish_wiki.sh`` mirrors the wiki clone with ``rsync --delete``. Its source
  guard tested that the directory *existed*, not that it held anything, so an
  emptied or half-populated source published the deletion and pushed it.
* ``post-commit`` decided whether to publish from
  ``git diff-tree --no-commit-id --name-only -r HEAD``, which prints **nothing**
  for a merge commit and nothing for a root commit without ``--root``. Either
  read as "no wiki paths changed", and the hook exited 0 in silence.
* The wiki path is written out in **both** files. Nothing kept them aligned, and
  a rename that updated one of them is the "stale prefix" failure mode itself —
  ``test_hook_prefix_matches_publish_script_source_dir`` is that missing link.

The scripts are exercised as subprocesses against synthetic git repositories: a
bare repo standing in for the wiki remote, a clone of it, and a source repo whose
``git rev-parse --show-toplevel`` is what the script under test resolves. Nothing
touches the network or the real wiki clone.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISH_SH = REPO_ROOT / "scripts" / "publish_wiki.sh"
POST_COMMIT = REPO_ROOT / ".githooks" / "post-commit"

#: The wiki source path, as this repository actually lays it out. Both scripts
#: must agree with it; see ``test_hook_prefix_matches_publish_script_source_dir``.
WIKI_SUBDIR = "docs/wiki/model_project_constructor"

GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.invalid",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
}

#: Skipping is honest on a developer box without rsync, but on CI it would turn
#: the only coverage these two scripts have into an unnoticed bump in the skip
#: count -- a test module for two fail-open bugs, failing open. On CI, absence is
#: a failure instead.
_TOOLS_PRESENT = shutil.which("git") is not None and shutil.which("rsync") is not None
pytestmark = pytest.mark.skipif(
    not _TOOLS_PRESENT and not os.environ.get("CI"),
    reason="the wiki publisher shells out to git and rsync",
)


def test_git_and_rsync_are_available() -> None:
    assert _TOOLS_PRESENT, "git and rsync are prerequisites of the wiki publisher"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def git(*args: str, cwd: Path) -> str:
    """Run git in ``cwd`` with a hermetic identity and return stdout."""
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=GIT_IDENTITY | {"PATH": _path(), "HOME": str(cwd)},
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def _path() -> str:
    import os

    return os.environ.get("PATH", "/usr/bin:/bin")


def run_script(
    script: Path, cwd: Path, extra_env: dict[str, str] | None = None, *args: str
) -> subprocess.CompletedProcess[str]:
    """Invoke a shell script under test. Never raises on non-zero exit."""
    import os

    env = {
        "PATH": _path(),
        "HOME": str(cwd),
        **GIT_IDENTITY,
        **(extra_env or {}),
    }
    if "LANG" in os.environ:
        env["LANG"] = os.environ["LANG"]
    return subprocess.run(
        [str(script), *args], cwd=cwd, env=env, capture_output=True, text=True
    )


class WikiWorld:
    """A synthetic source repo, wiki clone, and bare wiki remote."""

    def __init__(self, root: Path, pages: int = 8) -> None:
        self.root = root
        self.remote = root / "model_project_constructor.wiki.git"
        self.clone = root / "wiki-clone"
        self.repo = root / "repo"
        self.page_names = [f"Page{i}.md" for i in range(1, pages + 1)]

        git("init", "--bare", "-b", "master", str(self.remote), cwd=root)

        self.clone.mkdir()
        git("init", "-b", "master", ".", cwd=self.clone)
        git("remote", "add", "origin", str(self.remote), cwd=self.clone)
        for name in self.page_names:
            (self.clone / name).write_text(f"# {name}\n", encoding="utf-8")
        git("add", "-A", cwd=self.clone)
        git("commit", "-m", "seed wiki", cwd=self.clone)
        git("push", "-u", "origin", "master", cwd=self.clone)

        self.repo.mkdir()
        git("init", "-b", "master", ".", cwd=self.repo)
        self.source = self.repo / WIKI_SUBDIR
        self.source.mkdir(parents=True)
        for name in self.page_names:
            (self.source / name).write_text(f"# {name}\n", encoding="utf-8")
        (self.repo / "README.md").write_text("root\n", encoding="utf-8")
        git("add", "-A", cwd=self.repo)
        git("commit", "-m", "seed repo", cwd=self.repo)

    # -- inspection -------------------------------------------------------- #
    def clone_files(self) -> set[str]:
        return set(git("ls-files", cwd=self.clone).split())

    def published_files(self) -> set[str]:
        """What the bare remote actually holds on master."""
        listing = git("ls-tree", "-r", "--name-only", "master", cwd=self.remote)
        return set(listing.split())

    def keep_only(self, *names: str) -> None:
        """Delete every source page except ``names`` — the half-populated case."""
        for page in self.source.glob("*.md"):
            if page.name not in names:
                page.unlink()

    def publish(self, **env: str) -> subprocess.CompletedProcess[str]:
        return run_script(PUBLISH_SH, self.repo, {"WIKI_CLONE": str(self.clone), **env})


@pytest.fixture
def world(tmp_path: Path) -> WikiWorld:
    return WikiWorld(tmp_path)


@pytest.fixture
def make_world(tmp_path: Path):
    """Build a world with a chosen page count, in its own directory."""
    counter = {"n": 0}

    def _make(pages: int) -> WikiWorld:
        counter["n"] += 1
        root = tmp_path / f"w{counter['n']}"
        root.mkdir()
        return WikiWorld(root, pages=pages)

    return _make


@pytest.fixture
def shim(tmp_path: Path):
    """Put a failing stand-in for a real tool at the front of PATH.

    Used to drive the fail-CLOSED branches, which are otherwise unreachable and
    were therefore deletable with the whole suite still green.
    """
    bin_dir = tmp_path / "shim-bin"
    bin_dir.mkdir()

    def _install(tool: str, fail_when_arg: str, exit_code: int = 23) -> dict[str, str]:
        real = shutil.which(tool)
        assert real, tool
        script = bin_dir / tool
        script.write_text(
            "#!/usr/bin/env bash\n"
            'for a in "$@"; do\n'
            f'  if [ "$a" = "{fail_when_arg}" ]; then\n'
            f'    echo "shim: {tool} refused {fail_when_arg}" >&2; exit {exit_code}\n'
            "  fi\n"
            "done\n"
            f'exec {real} "$@"\n',
            encoding="utf-8",
        )
        script.chmod(0o755)
        return {"PATH": f"{bin_dir}:{_path()}"}

    return _install


# --------------------------------------------------------------------------- #
# publish_wiki.sh — the destructive-sync guards (the filed bug)
# --------------------------------------------------------------------------- #
def test_empty_source_directory_aborts_and_leaves_the_wiki_intact(world: WikiWorld) -> None:
    """The filed bug: an existing-but-empty source used to publish an empty wiki."""
    world.keep_only()  # delete every page
    assert list(world.source.iterdir()) == []

    result = world.publish()

    assert result.returncode == 1
    assert "no *.md files" in result.stderr
    assert "would empty the live wiki" in result.stderr
    # Nothing was deleted, committed, or pushed.
    assert world.clone_files() == set(world.page_names)
    assert world.published_files() == set(world.page_names)


def test_source_holding_no_markdown_aborts(world: WikiWorld) -> None:
    """A directory that is non-empty but holds no pages is still an empty wiki."""
    world.keep_only()
    (world.source / "stray.txt").write_text("not a page\n", encoding="utf-8")

    result = world.publish()

    assert result.returncode == 1
    assert "no *.md files" in result.stderr
    assert world.published_files() == set(world.page_names)


def test_half_populated_source_is_refused_as_a_mass_deletion(world: WikiWorld) -> None:
    """The case the item names but a plain non-empty floor cannot catch."""
    world.keep_only("Page1.md", "Page2.md")  # 6 of 8 deleted

    result = world.publish()

    assert result.returncode == 1
    assert "refusing to publish a mass deletion" in result.stderr
    assert "would delete 6 of 8 published files" in result.stderr
    assert world.clone_files() == set(world.page_names)
    assert world.published_files() == set(world.page_names)


def test_mass_deletion_proceeds_when_explicitly_allowed(world: WikiWorld) -> None:
    """The guard is a speed bump for the unattended path, not a lock."""
    world.keep_only("Page1.md", "Page2.md")

    result = world.publish(MPC_WIKI_ALLOW_MASS_DELETE="1")

    assert result.returncode == 0, result.stderr
    assert world.published_files() == {"Page1.md", "Page2.md"}


def test_a_proportionate_deletion_still_publishes(world: WikiWorld) -> None:
    """Retiring a couple of pages must not need the escape hatch."""
    world.keep_only(*world.page_names[:6])  # 2 of 8 deleted

    result = world.publish()

    assert result.returncode == 0, result.stderr
    assert world.published_files() == set(world.page_names[:6])


def test_the_deletion_guard_fires_at_its_declared_boundary(world: WikiWorld) -> None:
    """3 of 8 trips both arms (>2 deletions AND >25% of the clone); 2 of 8 does not."""
    world.keep_only(*world.page_names[:5])  # 3 of 8 deleted

    result = world.publish()

    assert result.returncode == 1
    assert "would delete 3 of 8 published files" in result.stderr


def test_a_single_new_page_is_published_and_pushed(world: WikiWorld) -> None:
    (world.source / "Brand-New.md").write_text("# new\n", encoding="utf-8")

    result = world.publish()

    assert result.returncode == 0, result.stderr
    assert "published:" in result.stdout
    assert "Brand-New.md" in world.published_files()


def test_parity_is_a_clean_no_op(world: WikiWorld) -> None:
    result = world.publish()

    assert result.returncode == 0, result.stderr
    assert "no changes to publish" in result.stdout
    assert world.published_files() == set(world.page_names)


# --------------------------------------------------------------------------- #
# publish_wiki.sh — guards that already existed, pinned so they stay
# --------------------------------------------------------------------------- #
def test_missing_source_directory_aborts(world: WikiWorld) -> None:
    shutil.rmtree(world.source)

    result = world.publish()

    assert result.returncode == 1
    assert "source directory not found" in result.stderr


def test_missing_clone_aborts(world: WikiWorld) -> None:
    result = run_script(PUBLISH_SH, world.repo, {"WIKI_CLONE": str(world.root / "nope")})

    assert result.returncode == 1
    assert "wiki clone not found" in result.stderr


def test_clone_pointing_elsewhere_aborts(world: WikiWorld) -> None:
    git("remote", "set-url", "origin", "https://example.invalid/other.git", cwd=world.clone)

    result = world.publish()

    assert result.returncode == 1
    assert "does not point to the wiki repo" in result.stderr


def test_clone_on_the_wrong_branch_aborts(world: WikiWorld) -> None:
    git("checkout", "-q", "-b", "sidebar", cwd=world.clone)

    result = world.publish()

    assert result.returncode == 1
    assert "expected 'master'" in result.stderr


def test_dirty_clone_aborts(world: WikiWorld) -> None:
    (world.clone / "Page1.md").write_text("locally edited\n", encoding="utf-8")

    result = world.publish()

    assert result.returncode == 1
    assert "uncommitted changes" in result.stderr


def test_unexpected_argument_is_rejected(world: WikiWorld) -> None:
    result = run_script(PUBLISH_SH, world.repo, {"WIKI_CLONE": str(world.clone)}, "--force")

    assert result.returncode == 1
    assert "unexpected argument" in result.stderr


# --------------------------------------------------------------------------- #
# .githooks/post-commit — the fail-open decision (the second filed bug)
# --------------------------------------------------------------------------- #
class HookWorld:
    """A repo with the hook installed and a *stub* publisher that records its run."""

    def __init__(self, root: Path) -> None:
        self.repo = root / "repo"
        self.repo.mkdir(parents=True)
        git("init", "-b", "master", ".", cwd=self.repo)

        self.source = self.repo / WIKI_SUBDIR
        self.source.mkdir(parents=True)

        self.marker = root / "publisher-ran"
        scripts = self.repo / "scripts"
        scripts.mkdir()
        stub = scripts / "publish_wiki.sh"
        stub.write_text(
            "#!/usr/bin/env bash\n"
            'echo "stub publisher ran"\n'
            'printf "ran\\n" >> "$STUB_MARKER"\n',
            encoding="utf-8",
        )
        stub.chmod(0o755)

        hooks = self.repo / ".githooks"
        hooks.mkdir()
        self.hook = hooks / "post-commit"
        shutil.copy2(POST_COMMIT, self.hook)

    def commit(self, message: str, **files: str) -> None:
        for rel, text in files.items():
            target = self.repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        git("add", "-A", cwd=self.repo)
        git("commit", "--allow-empty", "-m", message, cwd=self.repo)

    def fire(self, **env: str) -> subprocess.CompletedProcess[str]:
        return run_script(self.hook, self.repo, {"STUB_MARKER": str(self.marker), **env})

    @property
    def published(self) -> bool:
        return self.marker.exists()


@pytest.fixture
def hooked(tmp_path: Path) -> HookWorld:
    return HookWorld(tmp_path)


def test_root_commit_carrying_a_wiki_change_publishes(hooked: HookWorld) -> None:
    """'diff-tree -r HEAD' prints nothing for the root commit without --root."""
    hooked.commit("root", **{f"{WIKI_SUBDIR}/Home.md": "# home\n"})

    result = hooked.fire()

    assert result.returncode == 0, result.stderr
    assert hooked.published, result.stderr


def test_merge_commit_carrying_a_wiki_change_publishes(hooked: HookWorld) -> None:
    """The filed bug: 'diff-tree -r HEAD' prints NOTHING for a merge commit."""
    hooked.commit("root", **{"README.md": "root\n"})
    git("checkout", "-q", "-b", "topic", cwd=hooked.repo)
    hooked.commit("wiki page on a branch", **{f"{WIKI_SUBDIR}/Home.md": "# home\n"})
    git("checkout", "-q", "master", cwd=hooked.repo)
    hooked.commit("unrelated work on master", **{"other.txt": "x\n"})
    git("merge", "--no-ff", "-m", "merge topic", "topic", cwd=hooked.repo)

    assert len(git("rev-parse", "HEAD^@", cwd=hooked.repo).split()) == 2, "not a merge"
    assert git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD", cwd=hooked.repo) == "", (
        "the pre-fix command must still print nothing here, or this test proves nothing"
    )

    result = hooked.fire()

    assert result.returncode == 0, result.stderr
    assert hooked.published, result.stderr


def test_ordinary_commit_touching_the_wiki_publishes(hooked: HookWorld) -> None:
    hooked.commit("root", **{"README.md": "root\n"})
    hooked.commit("edit a page", **{f"{WIKI_SUBDIR}/Home.md": "# home\n"})

    result = hooked.fire()

    assert result.returncode == 0, result.stderr
    assert hooked.published


def test_commit_without_wiki_paths_announces_the_skip(hooked: HookWorld) -> None:
    """Declining to publish must be visible; silence is what hid the bugs above."""
    hooked.commit("root", **{"README.md": "root\n"})

    result = hooked.fire()

    assert result.returncode == 0
    assert not hooked.published
    assert "wiki publish skipped" in result.stderr
    assert WIKI_SUBDIR in result.stderr


def test_stale_prefix_is_announced_and_exits_non_zero(hooked: HookWorld) -> None:
    """A prefix naming no directory can never match — report it, don't exit 0."""
    hooked.commit("root", **{"README.md": "root\n"})
    shutil.rmtree(hooked.source)

    result = hooked.fire()

    assert result.returncode == 1
    assert not hooked.published
    assert "STALE" in result.stderr
    assert "wiki source directory not found" in result.stderr


def test_skip_env_var_announces_and_does_not_publish(hooked: HookWorld) -> None:
    hooked.commit("root", **{f"{WIKI_SUBDIR}/Home.md": "# home\n"})

    result = hooked.fire(MPC_SKIP_WIKI_PUBLISH="1")

    assert result.returncode == 0
    assert not hooked.published
    assert "MPC_SKIP_WIKI_PUBLISH=1" in result.stderr


def test_git_runs_the_hook_and_ignores_its_non_zero_exit(hooked: HookWorld) -> None:
    """Wiring check: core.hooksPath fires the hook, and a hook failure never
    fails the commit — which is what makes the non-zero exits above safe."""
    git("config", "core.hooksPath", ".githooks", cwd=hooked.repo)
    shutil.rmtree(hooked.source)  # force the stale-prefix path

    import os

    env = GIT_IDENTITY | {
        "PATH": _path(),
        "HOME": str(hooked.repo),
        "STUB_MARKER": str(hooked.marker),
    }
    (hooked.repo / "README.md").write_text("root\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=hooked.repo, env=env, check=True)
    commit = subprocess.run(
        ["git", "commit", "-m", "root"],
        cwd=hooked.repo,
        env=env,
        capture_output=True,
        text=True,
    )

    assert commit.returncode == 0, commit.stderr
    assert "STALE" in commit.stderr
    assert not hooked.published
    assert os.path.isdir(hooked.repo / ".git")


# --------------------------------------------------------------------------- #
# The structural fix: the wiki path is duplicated across two files
# --------------------------------------------------------------------------- #
def test_hook_prefix_matches_publish_script_source_dir() -> None:
    """The 'stale prefix' failure mode is this invariant going unenforced.

    ``post-commit`` matches commit paths against a literal prefix; ``publish_wiki.sh``
    builds ``SOURCE_DIR`` from its own literal. A rename that updates one and not
    the other disables publishing silently — the hook now reports it at runtime,
    and this test stops it reaching a commit at all.
    """
    hook = POST_COMMIT.read_text(encoding="utf-8")
    script = PUBLISH_SH.read_text(encoding="utf-8")

    hook_prefix = re.search(r"^WIKI_SUBDIR='([^']+)'$", hook, re.MULTILINE)
    script_source = re.search(r'^SOURCE_DIR="\$REPO_ROOT/([^"]+)"$', script, re.MULTILINE)

    assert hook_prefix, "post-commit no longer declares WIKI_SUBDIR as a single literal"
    assert script_source, "publish_wiki.sh no longer builds SOURCE_DIR from a literal"
    assert hook_prefix.group(1) == script_source.group(1)
    assert hook_prefix.group(1) == WIKI_SUBDIR


def test_the_wiki_source_directory_exists_in_this_repository() -> None:
    """Both scripts are aimed at a path that must actually be here."""
    source = REPO_ROOT / WIKI_SUBDIR
    assert source.is_dir()
    assert list(source.glob("*.md")), "an empty source is exactly what the guards refuse"


# --------------------------------------------------------------------------- #
# Gap closures. Every test below was added because an adversarial review showed
# the behaviour it names could be deleted from the scripts with the suite still
# fully green — a passing assertion no mutant can reach proves nothing.
# --------------------------------------------------------------------------- #
def test_the_deletion_floor_arm_alone_permits_a_small_wiki_shrinking(make_world) -> None:
    """Separates the guard's two arms: here only the ``> 2`` floor holds it off.

    4 published files, 2 deleted: the ratio arm (2*4 > 4) fires, the floor arm
    (2 > 2) does not. Drop the floor and this legitimate publish starts failing.
    """
    small = make_world(4)
    small.keep_only("Page1.md", "Page2.md")

    result = small.publish()

    assert result.returncode == 0, result.stderr
    assert small.published_files() == {"Page1.md", "Page2.md"}


def test_the_deletion_ratio_arm_alone_permits_a_large_wiki_shrinking(make_world) -> None:
    """The mirror image: only the ratio arm holds this one off.

    20 published files, 3 deleted: the floor arm (3 > 2) fires, the ratio arm
    (3*4 > 20) does not. Drop the ratio and retiring 3 of 20 pages starts failing.
    """
    big = make_world(20)
    big.keep_only(*big.page_names[:17])

    result = big.publish()

    assert result.returncode == 0, result.stderr
    assert len(big.published_files()) == 17


def test_retiring_a_small_subdirectory_is_not_a_mass_deletion(world: WikiWorld) -> None:
    """rsync itemises directory deletions; ``git ls-files`` counts files only.

    Counting both in the numerator put the two sides of the ratio in different
    units and refused a change the guard is meant to wave through.
    """
    assets = world.clone / "assets"
    assets.mkdir()
    for name in ("a.png", "b.png"):
        (assets / name).write_bytes(b"x")
    git("add", "-A", cwd=world.clone)
    git("commit", "-m", "add assets", cwd=world.clone)
    git("push", "origin", "master", cwd=world.clone)
    assert len(world.clone_files()) == 10

    # The source never had assets/ — publishing retires 2 files and 1 directory.
    result = world.publish()

    assert result.returncode == 0, result.stderr
    assert world.published_files() == set(world.page_names)


def test_the_escape_hatch_is_only_the_exact_value_one(world: WikiWorld) -> None:
    """``MPC_WIKI_ALLOW_MASS_DELETE=0`` must not read as "allowed"."""
    world.keep_only("Page1.md", "Page2.md")

    result = world.publish(MPC_WIKI_ALLOW_MASS_DELETE="0")

    assert result.returncode == 1
    assert "refusing to publish a mass deletion" in result.stderr
    assert world.published_files() == set(world.page_names)


def test_the_escape_hatch_announces_that_it_suppressed_the_guard(world: WikiWorld) -> None:
    """Silently disabling a guard is the same shape as the bug it guards against."""
    world.keep_only("Page1.md", "Page2.md")

    result = world.publish(MPC_WIKI_ALLOW_MASS_DELETE="1")

    assert result.returncode == 0, result.stderr
    assert "deletion guard disabled" in result.stderr
    assert "6 file(s)" in result.stderr


def test_a_failed_dry_run_refuses_to_publish_rather_than_counting_zero(
    world: WikiWorld, shim
) -> None:
    """The dry run is the guard's only input. If it fails, publish blind or stop.

    Without this the whole ``if ! DRY_RUN=...`` block could be collapsed back to
    the piped ``| grep -c ... || true`` form and every other test stayed green.
    """
    world.keep_only("Page1.md", "Page2.md")
    env = shim("rsync", "--dry-run")

    result = world.publish(**env)

    assert result.returncode == 1
    assert "rsync dry run failed" in result.stderr
    assert world.published_files() == set(world.page_names)


def test_a_symlinked_source_directory_is_not_mistaken_for_an_empty_one(
    world: WikiWorld,
) -> None:
    """``[ -d ]`` and rsync follow a symlink; bare ``find`` does not descend it."""
    real_pages = world.repo / "_pages"
    shutil.move(str(world.source), str(real_pages))
    world.source.symlink_to(real_pages, target_is_directory=True)
    (real_pages / "Brand-New.md").write_text("# new\n", encoding="utf-8")

    result = world.publish()

    assert result.returncode == 0, result.stderr
    assert "Brand-New.md" in world.published_files()


def test_push_failure_exits_two_and_says_how_to_undo(world: WikiWorld) -> None:
    """Exit 2 is documented in the header and was pinned by nothing."""
    git("remote", "set-url", "--push", "origin", str(world.root / "gone.git"), cwd=world.clone)
    (world.source / "Brand-New.md").write_text("# new\n", encoding="utf-8")

    result = world.publish()

    assert result.returncode == 2
    assert "push failed" in result.stderr
    assert "reset --hard HEAD~1" in result.stderr


def test_hook_refuses_to_guess_when_git_cannot_list_the_commit(
    hooked: HookWorld, shim
) -> None:
    """A git failure prints nothing, which used to read as "no wiki paths"."""
    hooked.commit("root", **{f"{WIKI_SUBDIR}/Home.md": "# home\n"})
    env = shim("git", "diff-tree", exit_code=128)

    result = hooked.fire(**env)

    assert result.returncode == 1
    assert not hooked.published
    assert "could not list the files changed" in result.stderr


def test_a_page_with_a_non_ascii_name_is_still_published(hooked: HookWorld) -> None:
    """``core.quotePath`` C-quotes such paths, defeating the anchored match.

    The hook then announced "no wiki paths in <sha>" — a confidently false
    reason, which is precisely the failure class this change set out to close.
    """
    hooked.commit("root", **{f"{WIKI_SUBDIR}/Café-Notes.md": "# cafe\n"})

    quoted = git("diff-tree", "--no-commit-id", "--name-only", "-r", "--root", "HEAD",
                 cwd=hooked.repo)
    assert '"docs/wiki/model_project_constructor/Caf\\303\\251-Notes.md"' in quoted, (
        "core.quotePath did not quote the path; this test would prove nothing"
    )

    result = hooked.fire()

    assert result.returncode == 0, result.stderr
    assert hooked.published, result.stderr


def test_a_sibling_path_sharing_the_prefix_does_not_publish(hooked: HookWorld) -> None:
    """Pins the ``^…/`` anchor: without it a sibling FILE would trigger a publish."""
    hooked.commit("root", **{f"{WIKI_SUBDIR}.md": "not the wiki directory\n"})

    result = hooked.fire()

    assert result.returncode == 0
    assert not hooked.published
    assert "wiki publish skipped" in result.stderr


def test_a_checkout_with_no_wiki_at_all_is_not_reported_as_stale(
    hooked: HookWorld,
) -> None:
    """Only a MISSING page directory under an EXISTING docs/wiki/ means stale.

    Every commit in this repository's history before the wiki existed would
    otherwise fail the hook — routine false alarms teach the reader to ignore it.
    """
    hooked.commit("root", **{"README.md": "root\n"})
    shutil.rmtree(hooked.repo / "docs")

    result = hooked.fire()

    assert result.returncode == 0
    assert not hooked.published
    assert "no docs/wiki/ directory" in result.stderr
    assert "STALE" not in result.stderr


def test_a_conflict_resolved_merge_reaches_the_hook_and_publishes(
    hooked: HookWorld,
) -> None:
    """End-to-end through real git, not a hand-fired hook.

    This is the merge path that actually reaches post-commit: git creates a clean
    merge itself and runs post-merge, but a conflicted merge is finished by the
    user with ``git commit``, which fires post-commit with a two-parent HEAD.
    """
    git("config", "core.hooksPath", ".githooks", cwd=hooked.repo)
    env = GIT_IDENTITY | {
        "PATH": _path(),
        "HOME": str(hooked.repo),
        "STUB_MARKER": str(hooked.marker),
    }

    hooked.commit("root", **{"f.txt": "base\n"})
    git("checkout", "-q", "-b", "topic", cwd=hooked.repo)
    hooked.commit("topic", **{"f.txt": "topic\n", f"{WIKI_SUBDIR}/Home.md": "# home\n"})
    git("checkout", "-q", "master", cwd=hooked.repo)
    hooked.commit("master", **{"f.txt": "master\n"})
    hooked.marker.unlink(missing_ok=True)

    subprocess.run(["git", "merge", "--no-ff", "-m", "merge", "topic"],
                   cwd=hooked.repo, env=env, capture_output=True, text=True)
    (hooked.repo / "f.txt").write_text("resolved\n", encoding="utf-8")
    subprocess.run(["git", "add", "f.txt"], cwd=hooked.repo, env=env, check=True)
    commit = subprocess.run(["git", "commit", "-m", "resolve merge"],
                            cwd=hooked.repo, env=env, capture_output=True, text=True)

    assert commit.returncode == 0, commit.stderr
    assert len(git("rev-parse", "HEAD^@", cwd=hooked.repo).split()) == 2, "not a merge"
    assert hooked.published, commit.stderr


def test_a_clean_merge_never_reaches_this_hook(hooked: HookWorld) -> None:
    """Documents a REAL remaining gap, filed in BACKLOG.md — not a passing fix.

    git runs post-merge, not post-commit, when it creates a merge commit itself,
    and this repository installs no post-merge hook. A clean ``git merge`` or
    ``git pull`` carrying a wiki change therefore still publishes nothing. This
    test exists so the gap is visible and so it goes red if git ever changes.
    """
    git("config", "core.hooksPath", ".githooks", cwd=hooked.repo)
    env = GIT_IDENTITY | {
        "PATH": _path(),
        "HOME": str(hooked.repo),
        "STUB_MARKER": str(hooked.marker),
    }

    hooked.commit("root", **{"README.md": "root\n"})
    git("checkout", "-q", "-b", "topic", cwd=hooked.repo)
    hooked.commit("wiki on a branch", **{f"{WIKI_SUBDIR}/Home.md": "# home\n"})
    git("checkout", "-q", "master", cwd=hooked.repo)
    hooked.commit("unrelated", **{"other.txt": "x\n"})
    hooked.marker.unlink(missing_ok=True)

    merge = subprocess.run(["git", "merge", "--no-ff", "-m", "merge", "topic"],
                           cwd=hooked.repo, env=env, capture_output=True, text=True)

    assert merge.returncode == 0, merge.stderr
    assert len(git("rev-parse", "HEAD^@", cwd=hooked.repo).split()) == 2
    assert not hooked.published, (
        "post-commit fired for a clean merge — git's behaviour changed and the "
        "BACKLOG item about the missing post-merge hook can be closed"
    )
