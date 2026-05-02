"""Тесты для эвал-задачи 01: is_ignored.

Запуск из корня репозитория:
    pytest evals/tasks/test_01_gitignore.py -x

Решение должно лежать в solutions/gitignore.py и экспортировать
функцию is_ignored(patterns, path, *, is_dir=False) -> bool.
"""

from __future__ import annotations

import pytest

from solutions.gitignore import is_ignored

CASES: list[tuple[list[str], str, bool, bool]] = [
    # --- базовое ---
    (["*.log"],                              "a.log",        False, True),
    (["*.log"],                              "src/a.log",    False, True),
    (["*.log"],                              "a.txt",        False, False),

    # --- anchored по leading / ---
    (["/foo"],                               "foo",          False, True),
    (["/foo"],                               "a/foo",        False, False),

    # --- anchored по наличию / в середине ---
    (["doc/readme"],                         "doc/readme",   False, True),
    (["doc/readme"],                         "x/doc/readme", False, False),

    # --- dir-only ---
    (["build/"],                             "build",        False, False),
    (["build/"],                             "build",        True,  True),
    (["build/"],                             "src/build",    True,  True),

    # --- * не ест / ---
    (["doc/*"],                              "doc/a",        False, True),
    (["doc/*"],                              "doc/a/b",      False, False),

    # --- ** ---
    (["doc/**"],                             "doc/a/b",      False, True),
    (["**/build"],                           "x/y/build",    True,  True),
    (["a/**/b"],                             "a/b",          False, True),
    (["a/**/b"],                             "a/x/y/b",      False, True),

    # --- негация: побеждает последний ---
    (["*.log", "!keep.log"],                 "keep.log",     False, False),
    (["!keep.log", "*.log"],                 "keep.log",     False, True),
    (["*.log", "!keep.log", "keep.log"],     "keep.log",     False, True),

    # --- комментарии и пустые ---
    (["", "# comment", "*.log"],             "x.log",        False, True),
    (["#*.log"],                             "x.log",        False, False),

    # --- ? ---
    (["?.log"],                              "a.log",        False, True),
    (["?.log"],                              "ab.log",       False, False),
    (["?.log"],                              "a/b.log",      False, False),
]


@pytest.mark.parametrize(("patterns", "path", "is_dir", "expected"), CASES)
def test_is_ignored(
    patterns: list[str],
    path: str,
    is_dir: bool,
    expected: bool,
) -> None:
    assert is_ignored(patterns, path, is_dir=is_dir) is expected
