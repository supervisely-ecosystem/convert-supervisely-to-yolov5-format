import os

import yaml
from conftest import FakeApi, list_images, read_labels
from helpers import BOX, META, ann, poly, rect


def test_basic_export_layout(run_export):
    api = FakeApi(
        META,
        datasets=[(10, "ds", None)],
        images={10: [(1, "a.jpg", ann(rect(0, 0, 9, 19))), (2, "b.jpg", ann(tags=["val"]))]},
    )
    result_dir, api = run_export(api)
    assert list_images(result_dir, "train") == ["10_ds_a.jpg"]
    assert list_images(result_dir, "val") == ["10_ds_b.jpg"]
    train = read_labels(result_dir, "train")
    assert list(train) == ["10_ds_a.txt"]
    cls, x, y, w, h = train["10_ds_a.txt"][0].split()
    assert cls == "0"
    # Rectangle.center floors ((0 + 19) // 2 = 9): unchanged, see FIXES.md
    assert (float(x), float(y), float(w), float(h)) == (0.045, 0.04, 0.1, 0.1)
    assert read_labels(result_dir, "val") == {"10_ds_b.txt": []}
    with open(os.path.join(result_dir, "data_config.yaml")) as f:
        cfg = yaml.safe_load(f)
    assert cfg["names"] == ["box", "poly", "any"]
    assert cfg["nc"] == 3
    assert api.workflow == [("in", 1), ("out", 7)]


def test_skip_mode_drops_polygons_and_transform_mode_boxes_them(run_export):
    images = {10: [(1, "a.jpg", ann(poly([(10, 10), (10, 30), (30, 30)])))]}
    result_dir, _ = run_export(FakeApi(META, [(10, "ds", None)], images), process_shapes="skip")
    assert read_labels(result_dir, "train") == {"10_ds_a.txt": []}


def test_transform_mode(run_export):
    images = {10: [(1, "a.jpg", ann(poly([(10, 10), (10, 30), (30, 30)])))]}
    result_dir, _ = run_export(FakeApi(META, [(10, "ds", None)], images), process_shapes="transform")
    assert read_labels(result_dir, "train") == {"10_ds_a.txt": ["1 0.1 0.2 0.105 0.21"]}


def test_nested_datasets_and_dataset_selection(run_export):
    images = {
        10: [(1, "a.jpg", ann())],
        11: [(2, "a.jpg", ann())],
        12: [(3, "a.jpg", ann())],
    }
    datasets = [(10, "parent", None), (11, "child", 10), (12, "other", None)]
    result_dir, _ = run_export(FakeApi(META, datasets, images))
    assert list_images(result_dir, "train") == ["10_parent_a.jpg", "11_child_a.jpg", "12_other_a.jpg"]
    result_dir, _ = run_export(FakeApi(META, datasets, images), dataset_id=10)
    assert list_images(result_dir, "train") == ["10_parent_a.jpg", "11_child_a.jpg"]


def test_train_and_val_tags(run_export):
    images = {
        10: [
            (1, "t.jpg", ann(tags=["train"])),
            (2, "v.jpg", ann(tags=["val"])),
            (3, "both.jpg", ann(tags=["train", "val"])),
            (4, "none.jpg", ann()),
        ]
    }
    result_dir, _ = run_export(FakeApi(META, [(10, "ds", None)], images))
    # an image tagged both train and val goes to both splits (unchanged behaviour)
    assert list_images(result_dir, "train") == ["10_ds_both.jpg", "10_ds_none.jpg", "10_ds_t.jpg"]
    assert list_images(result_dir, "val") == ["10_ds_both.jpg", "10_ds_v.jpg"]


def test_class_index_follows_meta_order(run_export):
    images = {10: [(1, "a.jpg", ann(rect(0, 0, 9, 9), rect(0, 0, 9, 9, cls=BOX)))]}
    result_dir, _ = run_export(FakeApi(META, [(10, "ds", None)], images))
    assert [line.split()[0] for line in read_labels(result_dir, "train")["10_ds_a.txt"]] == ["0", "0"]
