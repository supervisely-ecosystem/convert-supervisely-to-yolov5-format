from conftest import FakeApi, read_labels
from helpers import META, ann, rect


def test_rectangle_outside_the_image_is_cropped_by_the_sdk(run_export):
    # sly.Annotation crops labels to the image on load, so plain boxes never leave [0, 1]
    images = {10: [(1, "a.jpg", ann(rect(-10, -20, 9, 19), rect(150, 250, 160, 260)))]}
    result_dir, _ = run_export(FakeApi(META, [(10, "ds", None)], images))
    assert read_labels(result_dir, "train")["10_ds_a.txt"] == ["0 0.045 0.04 0.1 0.1"]

