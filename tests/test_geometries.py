import numpy as np
import pytest
import supervisely as sly
from conftest import FakeApi, read_labels
from helpers import ANY, META, ann, bitmap, rect


def test_skip_mode_keeps_rectangles_of_an_any_shape_class(run_export):
    # class "any" (AnyGeometry) holds a rectangle and a bitmap: the rectangle is a bbox and must
    # be exported; the bitmap and the oriented bbox are unsupported shapes
    obb = sly.Label(sly.OrientedBBox(10, 10, 20, 30, angle=0.3), ANY)
    images = {10: [(1, "a.jpg", ann(rect(0, 0, 9, 19, cls=ANY), bitmap(), obb))]}
    result_dir, _ = run_export(FakeApi(META, [(10, "ds", None)], images), process_shapes="skip")
    assert read_labels(result_dir, "train") == {"10_ds_a.txt": ["2 0.045 0.04 0.1 0.1"]}


def _every_shape():
    from supervisely.geometry.graph import GraphNodes, KeypointsTemplate, Node

    tmpl = KeypointsTemplate()
    tmpl.add_point("n1", row=0, col=0)
    tmpl.add_point("n2", row=5, col=5)
    kp_cls = sly.ObjClass("kp", GraphNodes, geometry_config=tmpl)
    geoms = {
        "rect": (sly.Rectangle, sly.Rectangle(10, 10, 20, 30)),
        "polygon": (sly.Polygon, sly.Polygon([sly.PointLocation(1, 1), sly.PointLocation(1, 9), sly.PointLocation(9, 9)])),
        "bitmap": (sly.Bitmap, sly.Bitmap(np.ones((3, 3), bool), origin=sly.PointLocation(2, 2))),
        "alpha": (sly.AlphaMask, sly.AlphaMask(np.full((3, 3), 255, np.uint8), origin=sly.PointLocation(2, 2))),
        "line": (sly.Polyline, sly.Polyline([sly.PointLocation(1, 1), sly.PointLocation(5, 5)])),
        "point": (sly.Point, sly.Point(3, 4)),
        "obb": (sly.OrientedBBox, sly.OrientedBBox(10, 10, 20, 30, angle=0.3)),
    }
    classes = [sly.ObjClass(n, t) for n, (t, _) in geoms.items()] + [kp_cls]
    labels = [sly.Label(g, c) for (_, g), c in zip(geoms.values(), classes)]
    labels.append(sly.Label(GraphNodes({"n1": Node(sly.PointLocation(3, 3)), "n2": Node(sly.PointLocation(8, 9))}), kp_cls))
    return sly.ProjectMeta(obj_classes=classes), labels


@pytest.mark.parametrize("mode,expected", [("skip", 1), ("transform", 8)])
def test_every_shape_type(run_export, mode, expected):
    meta, labels = _every_shape()
    images = {10: [(1, "a.jpg", ann(*labels))]}
    result_dir, _ = run_export(FakeApi(meta, [(10, "ds", None)], images), process_shapes=mode)
    lines = read_labels(result_dir, "train")["10_ds_a.txt"]
    assert len(lines) == expected
    for line in lines:
        values = [float(v) for v in line.split()[1:]]
        assert len(values) == 4 and all(0 <= v <= 1 for v in values)
