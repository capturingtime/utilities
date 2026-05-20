# ctp-utilities — Architecture

## Purpose

`ctp-utilities` is a Python library providing cloud-provider-agnostic abstractions
for file system operations and cloud storage interactions. It underpins two CTP
applications:

- **Photobooth** — uploads captured images to S3 and returns a download URL printed
  on a thermal-printer receipt.
- **RAW Image Archive** — packages shoot sessions into 7z archives, extracts previews,
  and uploads to tiered S3 storage.

The central design principle is **provider agnosticism through layered abstraction**:
application code only touches abstract interfaces; concrete provider implementations
are injected at initialization time.

---

## Abstraction Layers

```
┌────────────────────────────────────────────────────────────┐
│                     Application Layer                       │
│       photobooth.booth_main · archive_script · scripts.*    │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│                       Client Layer                          │
│      clients/aws/      clients/tave/    clients/archive/    │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│                    Concrete Class Layer                      │
│       classes/path/        classes/file/                    │
│      (File, Dir)       (Archive, RawImage)                  │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│                   Abstract Base Layer                        │
│          Cloud · Bucket · BucketItem · Path                 │
└────────────────────────────────────────────────────────────┘
```

---

## Component Reference

### Abstract Base Classes (`classes/abstract/`)

These define the *interface contracts* every concrete implementation must fulfill.
Violating a contract (missing an abstract method) raises `TypeError` at class
definition time — bugs are caught on import, not at runtime.

#### `Cloud` — `abstract/cloud.py`

Root of the cloud provider hierarchy. Concrete subclasses must:

- Expose a `cloud` property (string identifier, e.g. `"aws"`)
- Implement `load_bucket(name, bucket_role)` to instantiate and register a `Bucket`

#### `Bucket` — `abstract/bucket.py`

Represents one cloud storage container (e.g., an S3 bucket). All CRUD operations are
declared here; providers implement them.

**Bucket Roles** are a semantic classification that map to S3 storage class tiers:

| Role          | S3 Storage Class | Use Case                                       |
|---------------|-----------------|------------------------------------------------|
| `archive`     | GLACIER_IR      | RAW image files — cold storage, rare retrieval |
| `meta_archive`| STANDARD_IA     | Previews, thumbnails, sidecars — used occasionally |
| `standard`    | (default)       | Public downloads, general purpose              |

Bucket role is validated at construction. Mismatches between the declared role and the
bucket's actual S3 lifecycle policy raise `ValueError` at init — not silently on the
first upload.

#### `BucketItem` — `abstract/bucketitem.py`

Represents a single object inside a bucket. Must expose:

- `item` — the object key (full path within the bucket)
- `exists` — boolean presence check
- `data` — raw object body
- `metadata` — object attribute dict

#### `Path` — `abstract/path.py`

Filesystem path abstraction shared by `File` and `Dir`. Wraps `os.path.*` as typed
properties and declares the `copy / delete / create / mv` lifecycle interface.

---

### File System Classes (`classes/path/`, `classes/file/`)

#### `File` — `classes/path/file.py`

Concrete `Path` for regular files.

- **SHA-256 hashing** — computed fresh each call via `sha256` property. Intentionally
  not cached: callers need a current hash to detect content changes or verify uploads.
- **Chunked copy** — `_copy_bar()` uses an 8192-byte read buffer with a `tqdm`
  progress bar; `_copy()` is the silent variant. Both write with `"wb"` (not append)
  because `copy()` pre-checks `dst.exists` and raises `FileExistsError` first.
- Used by `S3.put_item` to upload local files with end-to-end checksum verification.

#### `Dir` — `classes/path/dir.py`

Concrete `Path` for directories.

- `create(p=True)` mirrors `mkdir -p` via `os.makedirs(exist_ok=True)`. Without
  `p=True` it uses `os.mkdir` (single level only, fails if parent missing).
- `delete()` removes only *empty* directories (`os.rmdir`) — by design, not a
  recursive delete. Caller is responsible for emptying first.

#### `Archive` — `classes/file/archive.py`

Extends `File` for 7-Zip archives using `py7zr`.

- `isarchive` — validates the file is a readable 7z container, not just any file with
  a `.7z` extension.
- `check_crc()` — full archive integrity check via `py7zr.testzip()`, returns `None`
  on success.
- `add(src)` — appends `File` or `Dir` objects using `"a"` (append) mode. `_create()`
  is called automatically if the archive doesn't exist yet.
- `_create()` — opens a new archive in `"w"` mode and immediately closes it to produce
  a valid empty container. Refuses to overwrite a file that exists but is not a valid
  archive.

#### `RawImage` — `classes/file/rawimage.py`

Extends `File` for camera RAW files using `rawpy`.

- `rawpy.imread()` is called at init — this is the expensive decode step. **Cache the
  `RawImage` instance** when exporting multiple formats from the same file.
- `save_preview(dst)` — extracts the embedded JPEG thumbnail (byte-for-byte copy of
  the camera-generated preview) or falls back to converting a BITMAP preview via
  `imageio`.
- `save_tiff(dst)` — saves the full-resolution postprocessed image as a TIFF.

---

### AWS Client (`clients/aws/`)

#### `AWS` — `clients/aws/client.py`

Concrete `Cloud` for Amazon Web Services.

- Maintains an internal `dict` of `S3` instances keyed by bucket name.
- `load_bucket(name, **kwargs)` — constructs an `S3`, validates it against AWS, and
  registers it. `**kwargs` flows through to `Bucket.__init__` (accepts `bucket_role`,
  `bucket_desc`).
- `get_bucket(name)` — retrieves a previously registered bucket by name.

#### `S3` — `clients/aws/s3.py`

Concrete `Bucket` backed by `boto3`.

- **Init validation** — on construction, verifies the bucket exists
  (`get_bucket_location`) and that its lifecycle policy matches the declared
  `bucket_role` (`get_bucket_lifecycle_configuration`). A 404 on the lifecycle config
  is tolerated for `standard` buckets (they have no lifecycle requirement).
- **Object cache** — tracks known `Object` instances in `__objects` dict to avoid
  redundant `GetObjectAttributes` calls within a session.
- **`put_item(key, body)`** — accepts a `File`, raw `bytes`, or a filepath `str`.
  Attaches `ChecksumAlgorithm: sha256` so AWS rejects uploads with mismatched content.
- **`list_items()`** — handles paginated `list_objects_v2` responses using
  `NextContinuationToken`. Reconciles the local cache against the remote list,
  pruning objects that were deleted out-of-band.

#### `Object` — `clients/aws/object.py`

Concrete `BucketItem` for a single S3 object.

- **Caching** — when `caching=True` (default), attributes fetched from
  `GetObjectAttributes` are held in `__obj_attrs` and reused. Toggle off with
  `toggle_caching()` to force a fresh fetch on every property access.
- **Typed properties** — all `GetObjectAttributes` fields (`Checksum`, `ETag`,
  `ObjectSize`, `StorageClass`, etc.) are exposed as typed Python properties with
  automatic lazy-fetch via `__resolve_attr`.
- `refresh_data()` — forces a `GetObject` call regardless of caching state, updating
  both the body stream and attribute dict.

---

### Tave CRM Client (`clients/tave/`)

#### `Tave` — `clients/tave/client.py`

HTTP client for the Tave photography CRM REST API (v2).

- **Spec-driven validation** — fetches the live OpenAPI spec at init. Every `get /
  post / put / delete` call validates the path and HTTP method against the spec before
  sending, returning a clear error for unknown endpoints.
- **Path ID handling** — replaces 26-character Tave IDs in URL paths with `{id}` /
  `{jobId}` placeholders for spec lookup, then restores the real ID in the actual
  request URL.
- Thin wrapper: `get()`, `post()`, `put()`, `delete()` format and dispatch requests
  through a shared `requests.Session`.

---

### Utility Scripts (`scripts/`, `utilities/`)

#### `archive_script.py` — `scripts/`

Interactive CLI for creating 7z archives from RAW shoot sessions.

- Prompts for shoot metadata (date, customer ID, session name) with sensible defaults.
- Date input accepts many human-readable formats (`2022Sep15`, `2022-09-15`, etc.)
  tried in order from most to least specific.
- Extracts JPEG previews alongside archive creation.
- Output path pattern: `<archive_root>/<NNNN>_<CustomerName>/<NNNN_YYYYMonDD_SessionName>.7z`

#### `raw_archive.py` — `utilities/`

Standalone lower-level functions for path parsing, RAW extraction, and preview
generation. Used by `archive_script.py`.

---

## AWS Credential Strategy

Credentials are resolved via the standard `boto3` chain — no credentials are stored or
managed within this library:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. `~/.aws/credentials` profile
3. IAM instance role (recommended for production deployments on EC2 / Lambda)

---

## Making `ctp-utilities` a Dependency

The canonical distribution channel is **pip install from a git tag** (public repo, no
PyPI listing). Pin a specific version in a consumer's `pyproject.toml`:

```toml
dependencies = [
    "ctp-utilities @ git+https://github.com/capturingtime/utilities.git@v0.4.0",
]
```

For local development of a consumer alongside utilities, an editable install still
works:

```bash
pip install -e /path/to/utilities
```

### Optional `[raw]` extra

RAW image processing (`rawpy`, `imageio` — used by `classes/file/rawimage.py` and
the `scripts/` archive tools) is gated behind an optional `[raw]` extra. The base
install pulls only the deps needed by the AWS / file / Tave clients.

```bash
pip install "ctp-utilities[raw] @ git+https://github.com/capturingtime/utilities.git@v0.4.0"
```

Reason: `rawpy` has no wheel for armv7 + Python 3.7 (the photobooth Pi target), so
shipping it as a hard dep blocks the booth install. Consumers that don't import
`rawimage` or the `scripts/` modules need nothing beyond the base install.

---

## Known Limitations / Open Work

| Area | Status |
|---|---|
| `S3.del_item()` | Not implemented — raises `NotImplementedError` |
| `S3.copy_item()` | Not implemented |
| `S3.rename_item()` | Not implemented |
| `Dir.copy()` | Not implemented |
| `File.mv()` | Stub only — no-op, path object not updated |
| `Tave.put()` / `Tave.post()` body | `body` param formatted but not yet sent in request |
