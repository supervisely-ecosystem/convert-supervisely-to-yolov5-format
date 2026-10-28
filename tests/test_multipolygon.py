"""Projects with a Multipolygon class (instance 6.17+, e.g. dev project 9390) — raw JSON, because
SDK 6.73.x cannot even build such a class: ProjectMeta.from_json raised "Unknown shape:
'multipolygon'" and the export crashed before writing anything."""

import pytest
from conftest import FakeApi, read_labels

META_JSON = {
    "classes": [
        {"title": "box", "shape": "rectangle", "color": "#FF0000", "geometry_config": {}},
        {"title": "parcel", "shape": "multipolygon", "color": "#0F7C8A", "geometry_config": {}},
    ],
    "tags": [],
}
ANN_JSON = {
    "size": {"height": 100, "width": 200},
    "tags": [],
    "description": "",
    "objects": [
        {"classTitle": "box", "tags": [], "geometryType": "rectangle",
         "points": {"exterior": [[0, 0], [19, 9]], "interior": []}},
        {"classTitle": "parcel", "tags": [], "geometryType": "multipolygon",
         "parts": [{"exterior": [[1, 1], [9, 1], [9, 9]], "interior": []},
                   {"exterior": [[20, 20], [40, 20], [40, 40]], "interior": []}]},
    ],
}


@pytest.mark.parametrize("mode,expected", [
    ("skip", ["0 0.045 0.04 0.1 0.1"]),
    ("transform", ["0 0.045 0.04 0.1 0.1", "1 0.1 0.2 0.2 0.4"]),
])
def test_project_with_a_multipolygon_class(run_export, mode, expected):
    api = FakeApi(META_JSON, [(10, "ds", None)], {10: [(1, "a.jpg", ANN_JSON)]})
    result_dir, _ = run_export(api, process_shapes=mode)
    assert read_labels(result_dir, "train")["10_ds_a.txt"] == expected
