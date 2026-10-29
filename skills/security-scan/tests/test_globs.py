import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from globs import glob_to_regex, path_matches_any  # noqa: E402


def test_doublestar_matches_nested():
    rx = glob_to_regex("**/app/**")
    assert rx.match("app/services/auth.ts")
    assert rx.match("packages/x/app/y/z.ts")
    assert not rx.match("supabase/functions/x.ts")


def test_single_star_does_not_cross_slash():
    rx = glob_to_regex("app/*.ts")
    assert rx.match("app/index.ts")
    assert not rx.match("app/sub/index.ts")


def test_test_file_glob():
    rx = glob_to_regex("**/*.test.*")
    assert rx.match("app/db.test.ts")
    assert rx.match("a/b/c.test.tsx")
    assert not rx.match("app/db.ts")


def test_path_matches_any_and_none():
    globs = ["**/app/**"]
    assert path_matches_any("app/x.ts", globs)
    assert not path_matches_any("supabase/functions/x.ts", globs)
    assert not path_matches_any("app/x.ts", [])
