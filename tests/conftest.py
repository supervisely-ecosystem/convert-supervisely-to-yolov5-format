"""Offline test harness: runs src/convert_sly_to_yolov5.py against a small in-memory fake of sly.Api.

No Supervisely server is contacted. Run from the repo root:
    python -m pytest
with the SDK version from dev_requirements.txt installed (plus pytest), on Python 3.14 like the image.
"""

import importlib
import os
import sys
from types import SimpleNamespace

import pytest
import supervisely as sly

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
APP_MODULES = ("convert_sly_to_yolov5", "workflow")


def _ann_json(ann):
    """Annotations are sly.Annotation or raw JSON (for shapes an older SDK cannot build)."""
    return ann if isinstance(ann, dict) else ann.to_json()


class FakeApi:
    """Just the calls the app makes. `datasets`: [(id, name, parent_id)], `images`: {ds_id: [(id, name, ann)]}."""

    def __init__(self, meta, datasets, images, project_id=1, project_name="proj"):
        self.meta = meta
        self.project_id = project_id
        self.ds = {
            ds_id: sly.DatasetInfo(**{f: None for f in sly.DatasetInfo._fields})._replace(
                id=ds_id, name=name, parent_id=parent, items_count=len(images.get(ds_id, [])), project_id=project_id
            )
            for ds_id, name, parent in datasets
        }
        self.images = images
        self.downloaded = []
        self.workflow = []
        self.project = SimpleNamespace(
            get_info_by_id=lambda id: SimpleNamespace(id=id, name=project_name),
            get_meta=lambda id: meta if isinstance(meta, dict) else meta.to_json(),
            get_images_count=lambda id: sum(len(v) for v in images.values()),
        )
        self.dataset = SimpleNamespace(
            get_list=self._get_list, get_info_by_id=lambda id: self.ds[id], get_nested=self._get_nested
        )
        self.image = SimpleNamespace(get_list=self._image_list, download_paths_async=self._download_paths_async)
        self.annotation = SimpleNamespace(download_batch=self._download_batch)
        self.app = SimpleNamespace(
            workflow=SimpleNamespace(
                add_input_project=lambda pid: self.workflow.append(("in", pid)),
                add_output_file=lambda fi, meta=None: self.workflow.append(("out", fi.id)),
            )
        )

    def _get_list(self, project_id, recursive=False):
        return [d for d in self.ds.values() if recursive or d.parent_id is None]

    def _get_nested(self, project_id, dataset_id):
        out, frontier = [], [dataset_id]
        while frontier:
            children = [d for d in self.ds.values() if d.parent_id in frontier]
            out.extend(children)
            frontier = [d.id for d in children]
        return out

    def _image_list(self, dataset_id):
        return [
            SimpleNamespace(id=i, name=n, height=_ann_json(ann)["size"]["height"], width=_ann_json(ann)["size"]["width"])
            for i, n, ann in self.images.get(dataset_id, [])
        ]

    def _download_batch(self, dataset_id, image_ids):
        by_id = {i: ann for i, _, ann in self.images[dataset_id]}
        return [SimpleNamespace(image_id=i, annotation=_ann_json(by_id[i])) for i in image_ids]

    async def _download_paths_async(self, ids, paths, progress_cb=None):
        for i, p in zip(ids, paths):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as f:
                f.write(f"image-{i}".encode())
            self.downloaded.append((i, p))
            if progress_cb is not None:
                progress_cb(1)


@pytest.fixture
def run_export(tmp_path, monkeypatch):
    """Import the app with the given env and run transform(api). Returns (result_dir, api)."""

    def _run(api, process_shapes="skip", dataset_id=None):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("TEAM_ID", "1")
        monkeypatch.setenv("WORKSPACE_ID", "1")
        monkeypatch.setenv("PROJECT_ID", str(api.project_id))
        monkeypatch.setenv("modal.state.processShapes", process_shapes)
        if dataset_id is None:
            monkeypatch.delenv("DATASET_ID", raising=False)
        else:
            monkeypatch.setenv("DATASET_ID", str(dataset_id))
        monkeypatch.syspath_prepend(SRC_DIR)
        for name in APP_MODULES:
            sys.modules.pop(name, None)
        app = importlib.import_module("convert_sly_to_yolov5")

        uploaded = {}

        def fake_set_download(local_path):
            uploaded["dir"] = local_path
            return SimpleNamespace(id=7, name=os.path.basename(local_path) + ".tar", team_id=1)

        monkeypatch.setattr(sly.output, "set_download", fake_set_download)
        app.transform(api)
        return uploaded["dir"], api

    return _run


def read_labels(result_dir, split):
    """{label file name: [lines]} for one split."""
    labels_dir = os.path.join(result_dir, "labels", split)
    out = {}
    for name in sorted(os.listdir(labels_dir)):
        with open(os.path.join(labels_dir, name)) as f:
            out[name] = f.read().splitlines()
    return out


def list_images(result_dir, split):
    return sorted(os.listdir(os.path.join(result_dir, "images", split)))

