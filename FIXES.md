# convert-supervisely-to-yolov5-format: fixes 2026-10

Branch `ecosystem-fixes-2026-10`, from `master` 6f98d0f (v2.2.0). Lifecycle `legacy`, headless,
~280 lines: targeted fixes plus the image move. Not rewritten (no framework change, same
`main_script`, same modal).

## Behaviour contract

- **Launch**: context menu "Download as" on an images project or an images dataset.
- **Input**: `PROJECT_ID`; optional `DATASET_ID` (that dataset plus every dataset nested in it).
- **Option** `modal.state.processShapes`: `skip` (modal default) drops every label that is not a
  plain Rectangle; `transform` writes the bounding box of any shape. When the variable is absent
  (API launch without modal state) the code default is `transform`.
- **Output**: `<project id>_<project name>[_<dataset id>_<dataset name>]` uploaded with
  `sly.output.set_download` as a tar (Team Files, task output "Download"); workflow input = project,
  output = file. Inside:
  - `images/{train,val}/<dataset id>_<dataset name>_<image name>`;
  - `labels/{train,val}/<same stem>.txt`, one `class x_center y_center w h` line per box (6
    decimals, normalised); an image without boxes gets an empty file;
  - `data_config.yaml`: `train`, `val` (`../<dir>/images/...`), `nc`, `names`, `colors`.
- **Class index** = position of the class in the project meta, all classes (unsupported ones too).
- **Split**: tag `val` → val; tag `train` → train; both tags → both splits; no tag → train.
- Labels are cropped to the image by the SDK when the annotation is loaded.

## Fixed

| # | Commit | Problem | Tests old → new |
|---|---|---|---|
| 1 | Fix merged label lines when two images differ only in extension | `a.jpg` and `a.png` in one dataset shared one `.txt`, written in append mode without a newline: one broken 9-value line for both images | 0/2 → 2/2 |
| 2 | Keep rectangles of "any shape" classes in skip mode | skip mode tested the class's shape, so all rectangles of an AnyGeometry class were dropped | 0/1 → 1/1 |
| 3 | Cut over-long file names to the 255-byte file system limit | long or non-ASCII dataset + image names went over 255 bytes: `File name too long` (errno 36 in the Linux image), whole export crashed | 0/1 → 1/1 |
| 4 | Move to SDK 6.74.34 on base-py-sdk-hardened | SDK 6.73.564 cannot parse a `multipolygon` class: the export crashed on any project that has one (dev project 9390) | 0/2 → 2/2 (on 6.73.564 vs 6.74.34) |

Also: offline tests (`tests/`, fake `sly.Api`, 15 tests) and an untracked committed `.pyc`.

## Intentional changes (visible to users)

- Label files end with `\n` (were missing the final newline). Old vs new on dev project 1317
  (22 images): all 45 files identical except that trailing newline.
- Only on a stem clash the second image is renamed `<stem>_1.<ext>`; only names over 255 bytes are
  cut. All other names unchanged.
- In skip mode, rectangles of an AnyGeometry class are now exported (class index of that class).
- Projects with a multipolygon class now export (skip mode: dropped; transform mode: bbox).
- `instance_version` 6.15.60 → 6.17.22 (see Image).

## Found, not fixed

- `Rectangle.center` floors (`(left + right) // 2`), and sizes use the inclusive pixel convention:
  box centres are shifted up to 1 px towards the top-left. The SDK's `rectangle_to_yolo_line` does
  the same; changing it would change every exported box.
- An image tagged both `train` and `val` is copied into both splits (train/val leak). SDK
  `sly_ds_to_yolo` puts it into val only.
- Empty output is still a success: a project without rectangles in skip mode gives an archive of
  empty label files (with a warning in the log).
- Env default `processShapes=transform` differs from the modal default `skip`.
- An OrientedBBox in transform mode becomes its enclosing box, which the SDK does not crop to the
  image (values can leave [0, 1]; rare).
- The result directory/archive name (`<project>_<dataset>`) is not length-limited.
- Images without a stored resolution (links) would divide by `None`.
- `config.json` still has `gui_template: src/gui.html` (file does not exist; app is headless).
  Left as is: removing it changes how the platform treats the app.
- Security: no archive extraction, eval/pickle, shell or secrets; nothing in
  `ecosystem-fleet/audits/ecosystem-security.md` for this repo. Paths come from dataset/image names,
  which cannot contain `/`.

## SDK `to_yolo` divergences (noted, not fixed)

`supervisely/convert/image/yolo/yolo_helper.py` (origin/master):
- SDK detect converts polygons, bitmaps, lines, keypoints to boxes always; the app only in
  `transform` mode. SDK skips Point; the app boxes it (1 px).
- SDK names files `<dataset short name>_<image>` with `generate_free_name` on the full image name,
  so `a.jpg`/`a.png` still collide on the label stem (SDK overwrites, `"w"`); the app now keeps
  both. The SDK does not cut long names.
- SDK writes `f"{v:.6f}"` (fixed 6 decimals); the app `round(v, 6)` (shortest form).
- SDK `data_config.yaml` also has `train_labels`/`val_labels`.
- Train/val: see above (SDK: `val` wins).

## Image

`supervisely/base-py-sdk-hardened:6.73.564` → `supervisely/base-py-sdk-hardened:6.74.34` (bare
hardened base, Python 3.14.7, tag exists on Docker Hub); `dev_requirements.txt`
`supervisely==6.74.34`; `instance_version` 6.15.60 → 6.17.22 (`versions.json`: 6.17.22 allows
[6.74.29, 6.74.35); 6.74.52, the newest release, would need 6.18.3). Same pair as export-to-coco
and download-images. The app needs nothing beyond the SDK. `release.yml` has no build-image job.
Revert that one commit to keep 6.15.60 instances.

## Verification

- Unit: 15/15 in a Python 3.14.3 venv with supervisely 6.74.34 and inside
  `base-py-sdk-hardened:6.74.34` (3.14.7, amd64).
- Read-only run against dev (`transform()` with a real `sly.Api`, upload and workflow stubbed):
  - project 1317, skip: old code + 6.73.564 and new code + 6.74.34 give the same 45 files (labels
    differ only by the trailing newline);
  - project 9390, transform: old code crashes (`Unknown shape: 'multipolygon'`); new code exports
    2 images with 10 + 7 boxes, values in [0, 1].

## Dev-check plan

Run from `workapps/`. Each case: the branch, then the published version for comparison.

```
# 1. Nested project, rectangles
uv run ecosystem-fleet/fleet.py run convert-supervisely-to-yolov5-format --workspace 3 --project 1317 --state processShapes=skip --version ecosystem-fixes-2026-10 --branch
uv run ecosystem-fleet/fleet.py run convert-supervisely-to-yolov5-format --workspace 3 --project 1317 --state processShapes=skip
```
Expected: success; 22 images in `images/train`, 0 in val; 22 label files named
`<ds id>_<ds name>_<image stem>.txt`; `nc: 7`. Published: same files; labels lack the final newline.

```
# 2. Parent dataset with nested datasets only (Tropical, 0 own images)
uv run ecosystem-fleet/fleet.py run convert-supervisely-to-yolov5-format --workspace 3 --project 1317 --dataset 10122 --version ecosystem-fixes-2026-10 --branch
uv run ecosystem-fleet/fleet.py run convert-supervisely-to-yolov5-format --workspace 3 --project 1317 --dataset 10122
```
Expected: success, 16 images (Banana 3, Mango 4, Pineapple 3, Lemon 3, Orange 3); archive name
`1317_..._10122_Tropical`. Published: the same.

```
# 3. Every shape type incl. multipolygon, transform
uv run ecosystem-fleet/fleet.py run convert-supervisely-to-yolov5-format --workspace 733 --project 9390 --state processShapes=transform --version ecosystem-fixes-2026-10 --branch
uv run ecosystem-fleet/fleet.py run convert-supervisely-to-yolov5-format --workspace 733 --project 9390 --state processShapes=transform
```
Expected: success; `48091_root_a.png` with 10 lines, `48092_child_b.png` with 7 lines, every value
in [0, 1]. Published: task fails with `Unknown shape: 'multipolygon'`.

```
# 4. Same project, skip
uv run ecosystem-fleet/fleet.py run convert-supervisely-to-yolov5-format --workspace 733 --project 9390 --state processShapes=skip --version ecosystem-fixes-2026-10 --branch
uv run ecosystem-fleet/fleet.py run convert-supervisely-to-yolov5-format --workspace 733 --project 9390 --state processShapes=skip
```
Expected: success, 2 images, both label files empty (the project has no rectangles), warning about
skipped objects. Published: fails as in case 3.
