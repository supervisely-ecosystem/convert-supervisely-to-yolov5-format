"""Tiny in-memory SDK objects for the tests."""

import numpy as np
import supervisely as sly

H, W = 100, 200

BOX = sly.ObjClass("box", sly.Rectangle)
POLY = sly.ObjClass("poly", sly.Polygon)
ANY = sly.ObjClass("any", sly.AnyGeometry)
TRAIN = sly.TagMeta("train", sly.TagValueType.NONE)
VAL = sly.TagMeta("val", sly.TagValueType.NONE)
META = sly.ProjectMeta(obj_classes=[BOX, POLY, ANY], tag_metas=[TRAIN, VAL])


def ann(*labels, tags=(), size=(H, W)):
    return sly.Annotation(
        img_size=size,
        labels=list(labels),
        img_tags=sly.TagCollection([sly.Tag({"train": TRAIN, "val": VAL}[t]) for t in tags]),
    )


def rect(top, left, bottom, right, cls=BOX):
    return sly.Label(sly.Rectangle(top, left, bottom, right), cls)


def poly(points, cls=POLY):
    return sly.Label(sly.Polygon([sly.PointLocation(r, c) for r, c in points]), cls)


def bitmap(cls=ANY):
    return sly.Label(sly.Bitmap(np.ones((4, 4), bool), origin=sly.PointLocation(10, 20)), cls)
