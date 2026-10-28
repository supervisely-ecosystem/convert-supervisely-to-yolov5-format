from conftest import FakeApi, list_images, read_labels
from helpers import META, ann, rect


def test_same_stem_different_extension_keeps_labels_apart(run_export):
    # a.jpg and a.png in one dataset used to share labels/train/10_ds_a.txt; the file was
    # opened in append mode without a trailing newline, so both images got one merged, broken line
    images = {
        10: [
            (1, "a.jpg", ann(rect(0, 0, 9, 19))),
            (2, "a.png", ann(rect(50, 100, 59, 119))),
        ]
    }
    result_dir, _ = run_export(FakeApi(META, [(10, "ds", None)], images))
    imgs = list_images(result_dir, "train")
    labels = read_labels(result_dir, "train")
    assert len(imgs) == 2
    assert len(labels) == 2
    stems = sorted(name.rsplit(".", 1)[0] for name in imgs)
    assert stems == sorted(name[: -len(".txt")] for name in labels)
    for lines in labels.values():
        assert len(lines) == 1
        assert len(lines[0].split()) == 5


def test_label_files_end_with_newline(run_export):
    images = {10: [(1, "a.jpg", ann(rect(0, 0, 9, 19), rect(10, 10, 19, 19)))]}
    result_dir, _ = run_export(FakeApi(META, [(10, "ds", None)], images))
    with open(f"{result_dir}/labels/train/10_ds_a.txt") as f:
        text = f.read()
    assert text.endswith("\n") and text.count("\n") == 2
