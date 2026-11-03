r"""hooks/_lib/tree.py — "is this tree ours": the one ownership test for hooks that WRITE into a tree.

Born 2026-10-14 (retro P7, reports/dispatch-and-shell-timeout-retro-2026-10-13.md §3.3): a
derived ~/.claude tree (a peer's rebuild) carries the same marker files, so "the root holds
hooks/project_registry_gist.py" also matched the peer's tree and registry_order_normalize
rewrote its views.json. Ownership is a git fact, not a file-shape fact:

  * is_own_tree(root) — True only when `root` resolves to the same git COMMON dir as our home
    (this file's tree), which covers the home itself and every linked worktree of it. A root
    that is not in a git repo, or where git cannot answer, is NOT ours (a writer skips it).
  * CLAUDE_OWN_TREE_ROOT (env) overrides which tree counts as "our home"; tests only.

review-when: our home moves out of git, or a writing hook must act on a tree that is not a
worktree of this repo.
"""
import os
import stat
import subprocess
from pathlib import Path

HOME_TREE = Path(__file__).resolve().parents[2]


def is_reparse(p, on_error: bool = False) -> bool:
    """True for a symlink or an NTFS reparse point (junction): a walk whose results are written
    never enters one (rules/tree-walk-reparse.md). `on_error` is the answer when the entry cannot
    be read: False (default) walks on; True treats it as a link and skips it (cc-delta, mod-review).
    The one copy for every tool that ships with hooks/_lib (AP-74, 2026-10-30)."""
    try:
        st = os.lstat(p)
    except OSError:
        return on_error
    if stat.S_ISLNK(st.st_mode):
        return True
    return bool(getattr(st, "st_file_attributes", 0) & 0x400)   # FILE_ATTRIBUTE_REPARSE_POINT


def git_common_dir(root) -> Path | None:
    try:
        p = subprocess.run(["git", "-C", str(root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                           capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    out = p.stdout.strip()
    if p.returncode != 0 or not out:
        return None
    return Path(os.path.normcase(str(Path(out).resolve())))


def is_linked_worktree(root) -> bool | None:
    """True when `root` is a LINKED worktree (its git dir differs from the common dir), False in
    the main working tree, None when git cannot answer. A linked worktree carries tracked files
    only, so a verdict over live machine data (untracked corpora, derived indexes) measured
    there is a verdict over a different, smaller corpus: such a gate reports UNDETERMINED
    (2026-10-19, recall golden probe: a worktree run showed a false loss of G1)."""
    try:
        p = subprocess.run(["git", "-C", str(root), "rev-parse", "--path-format=absolute",
                            "--git-dir", "--git-common-dir"], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    lines = p.stdout.strip().splitlines()
    if p.returncode != 0 or len(lines) != 2:
        return None
    gd, cd = (os.path.normcase(str(Path(x).resolve())) for x in lines)
    return gd != cd


def is_own_tree(root) -> bool:
    own = git_common_dir(os.environ.get("CLAUDE_OWN_TREE_ROOT") or HOME_TREE)
    theirs = git_common_dir(root)
    return own is not None and theirs is not None and own == theirs
