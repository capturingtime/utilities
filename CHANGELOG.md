# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased] — v0.4.1 (in progress)

Cleanup, minor fixes, and bug fixes following v0.4.0.

### Planned
- Bump `version` to `0.4.1.dev0` once any v0.4.1 code change lands.
- Follow-up cleanup of any rough edges surfaced by the photobooth + RAW
  archive consumers on v0.4.0.

## [v0.4.0] — 2026-05-20

First version distributed via pip-from-git-tag, consumed by `photobooth`
v0.4.0 as `ctp-utilities @ git+https://…/utilities.git@v0.4.0`.

### Added
- `[project.optional-dependencies.raw]` extra grouping `rawpy` and `imageio`.
  Install with `pip install "ctp-utilities[raw] @ git+…"` to enable
  RAW-image-reading code paths.

### Changed
- `rawpy` and `imageio` are no longer hard dependencies. They are required
  only by `utilities/classes/file/rawimage.py` and
  `scripts/archive_script.py`; everything else in the package imports without
  them. This unblocks installs on the photobooth Pi (Buster, armv7,
  Python 3.7.3), where no `rawpy` wheel is published.
- README documents the new `[raw]` extra and the pip-from-git-tag install
  model used by `photobooth`.

### Breaking
- **RAW Archive tooling needs the `[raw]` extra.** Any caller of
  `utilities.classes.file.rawimage` or any execution of
  `scripts/archive_script.py` must install with `"ctp-utilities[raw] @ git+…"`
  (the bare install will not pull `rawpy` / `imageio`).

### Upgrade

For the RAW Archive workflow (desktop):

```sh
pip install --upgrade \
    "ctp-utilities[raw] @ git+https://github.com/capturingtime/utilities.git@v0.4.0"
```

For consumers that do not need RAW image support (e.g. the photobooth Pi),
drop the `[raw]` suffix.

## Pre-v0.4.0 history (untagged)

No releases were tagged before v0.4.0. The repo evolved in three rough
phases:

- **2022-09 — initial archive script (`e645f83`).** `scripts/archive_script.py`
  was the entire codebase at this point: a flat script for archiving
  shoot folders.
- **2023-02 to 2023-03 — class layer (`3d54aac` → `a2057b9`).** Introduced
  the `classes/` package — first `file.py` / `rawimage.py` / `archive.py`,
  then a `Cloud` / `Bucket` / `Client` / `Path` / `Dir` abstraction stack
  with an AWS / S3 implementation. The archive script was rebuilt on top.
- **2024-06 to 2026-05 — pre-v0.4.0 refactor (`300639f` → `c895f24`).**
  Restructured into `classes/abstract`, `classes/file`, `classes/path`, and
  `clients/aws` + `clients/tave` subpackages. Removed the legacy `s3_v1.py`,
  added `conftest.py` + a `tests/` suite (`test_abstract`, `test_archive`,
  `test_aws`, `test_path`), introduced `pyproject.toml`, and wrote
  `ARCHITECTURE.md`. This refactor is what `photobooth` v0.4.0 consumes.

See [project_utilities_architecture.md](../../.claude/projects/-home-ian-git-ctp/memory/project_utilities_architecture.md)
for the package structure, the May 2026 bug fixes, and open follow-up work.
