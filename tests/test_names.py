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


def test_long_non_ascii_names_fit_the_file_system_limit(run_export):
    # 255 bytes per file name on ext4/APFS; dataset "id_name_" prefix plus a long Cyrillic image
    # name went over it and the export crashed with "File name too long"
    ds_name = "датасет_" * 12  # 96 chars, 180 bytes
    long_a = "изображение_" * 8 + "a.jpg"  # 101 chars, 189 bytes
    long_b = "изображение_" * 8 + "a.png"
    images = {10: [(1, long_a, ann(rect(0, 0, 9, 19))), (2, long_b, ann()), (3, "short.jpg", ann())]}
    result_dir, _ = run_export(FakeApi(META, [(10, ds_name, None)], images))
    imgs = list_images(result_dir, "train")
    labels = read_labels(result_dir, "train")
    assert len(imgs) == 3 and len(labels) == 3
    assert all(len(n.encode()) <= 255 for n in imgs + list(labels))
    assert sorted(n.rsplit(".", 1)[0] for n in imgs) == sorted(n[: -len(".txt")] for n in labels)
    assert f"10_{ds_name}_short.jpg" in imgs
    assert sum(len(lines) for lines in labels.values()) == 1
