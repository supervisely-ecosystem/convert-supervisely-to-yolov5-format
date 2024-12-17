import os
import yaml
from typing import List, Tuple
from dotenv import load_dotenv
import supervisely as sly
from workflow import add_input, add_output
import asyncio

# region constants
TRAIN_TAG_NAME = "train"
VAL_TAG_NAME = "val"
DATA_DIR = os.path.join(os.getcwd(), "data")
# endregion
sly.fs.mkdir(DATA_DIR, remove_content_if_exists=True)

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

# region envvars
team_id = sly.env.team_id()
workspace_id = sly.env.workspace_id()
project_id = sly.env.project_id()
process_shapes = os.environ.get("modal.state.processShapes", "transform")
process_shapes_message = "skipped" if process_shapes == "skip" else "transformed to rectangles"
# endregion
sly.logger.info(f"Team: {team_id}, Workspace: {workspace_id}, Project: {project_id}")
sly.logger.info(f"Process shapes: {process_shapes}")


def transform_label(class_names: List[str], img_size: Tuple[int, int], label: sly.Label) -> str:
    """Transforms label to YOLOv5 format.

    :param class_names: list of class names
    :type class_names: List[str]
    :param img_size: image size
    :type img_size: Tuple[int, int]
    :param label: label to transform
    :type label: sly.Label
    :return: transformed label
    :rtype: str
    """
    class_number = class_names.index(label.obj_class.name)
    rect_geometry = label.geometry.to_bbox()
    center = rect_geometry.center
    x_center = round(center.col / img_size[1], 6)
    y_center = round(center.row / img_size[0], 6)
    width = round(rect_geometry.width / img_size[1], 6)
    height = round(rect_geometry.height / img_size[0], 6)
    return f"{class_number} {x_center} {y_center} {width} {height}"


def transform(api: sly.Api) -> None:
    """Transforms Supervisely project to YOLOv5 format."""
    project = api.project.get_info_by_id(project_id)

    # Preparing result directory.
    result_dir_name = "{}_{}".format(project.id, project.name)
    result_dir = os.path.join(DATA_DIR, result_dir_name)
    sly.fs.mkdir(result_dir)
    config_path = os.path.join(result_dir, "data_config.yaml")
    sly.logger.debug(f"Data will be saved to {result_dir}, path to the config file: {config_path}")

    # Preparing directories for images and labels.
    train_images_dir = os.path.join(result_dir, "images/train")
    train_labels_dir = os.path.join(result_dir, "labels/train")
    sly.fs.mkdir(train_images_dir)
    sly.fs.mkdir(train_labels_dir)
    val_images_dir = os.path.join(result_dir, "images/val")
    val_labels_dir = os.path.join(result_dir, "labels/val")
    sly.fs.mkdir(val_images_dir)
    sly.fs.mkdir(val_labels_dir)

    # Retrieving project meta and creating class names and colors lists.
    meta_json = api.project.get_meta(project_id)
    meta = sly.ProjectMeta.from_json(meta_json)
    class_names = [obj_class.name for obj_class in meta.obj_classes]
    class_colors = [obj_class.color for obj_class in meta.obj_classes]
    sly.logger.debug(
        f"Project meta retrieved. Class names: {class_names}, class colors: {class_colors}"
    )

    missing_tags = []
    if meta.get_tag_meta(TRAIN_TAG_NAME) is None:
        missing_tags.append(TRAIN_TAG_NAME)
    if meta.get_tag_meta(VAL_TAG_NAME) is None:
        missing_tags.append(VAL_TAG_NAME)
    if len(missing_tags) > 0:
        missing_tags_str = ", ".join([f'"{tag}"' for tag in missing_tags])
        sly.logger.warning(
            f"Tag(s): {missing_tags_str} not found in project meta. Images without special tags will be marked as train"
        )

    error_classes = []
    for obj_class in meta.obj_classes:
        if obj_class.geometry_type != sly.Rectangle:
            error_classes.append(obj_class)
    if len(error_classes) > 0:
        sly.logger.warning(
            f"Project has unsupported classes. "
            f"Objects with unsupported geometry types will be {process_shapes_message}: "
            f"{[obj_class.name for obj_class in error_classes]}"
        )

    def _write_new_ann(path, content):
        with open(path, "a") as f1:
            f1.write("\n".join(content))

    def _add_to_split(image_id, img_name, split_ids, split_image_paths, labels_dir, images_dir):
        split_ids.append(image_id)
        ann_path = os.path.join(labels_dir, f"{sly.fs.get_file_name(img_name)}.txt")
        _write_new_ann(ann_path, yolov5_ann)
        img_path = os.path.join(images_dir, img_name)
        split_image_paths.append(img_path)

    train_count = 0
    val_count = 0

    progress = sly.Progress("Processing project items...", api.project.get_images_count(project_id))
    for dataset in api.dataset.get_list(project_id, recursive=True):
        sly.logger.info(f"Working with dataset: {dataset.name}...")
        images = api.image.get_list(dataset.id)
        sly.logger.debug(f"Dataset contains {len(images)} images.")

        unsupported_shapes = 0
        train_ids = []
        train_image_paths = []
        val_ids = []
        val_image_paths = []

        a_progress = sly.Progress("Transforming annotations...", total_cnt=len(images))
        for batch in sly.batched(images):
            image_ids = [image_info.id for image_info in batch]
            image_names = [f"{dataset.id}_{dataset.name}_{image_info.name}" for image_info in batch]
            ann_infos = api.annotation.download_batch(dataset.id, image_ids)

            for image_id, img_name, ann_info in zip(image_ids, image_names, ann_infos):
                ann_json = ann_info.annotation
                ann = sly.Annotation.from_json(ann_json, meta)

                yolov5_ann = []
                for label in ann.labels:
                    if label.obj_class.geometry_type != sly.Rectangle:
                        unsupported_shapes += 1
                        if process_shapes == "skip":
                            continue
                    yolov5_ann.append(transform_label(class_names, ann.img_size, label))

                image_processed = False
                if ann.img_tags.get(TRAIN_TAG_NAME) is not None:
                    _add_to_split(
                        image_id,
                        img_name,
                        train_ids,
                        train_image_paths,
                        train_labels_dir,
                        train_images_dir,
                    )
                    image_processed = True
                    train_count += 1

                if ann.img_tags.get(VAL_TAG_NAME) is not None:
                    val_ids.append(image_id)
                    ann_path = os.path.join(val_labels_dir, f"{sly.fs.get_file_name(img_name)}.txt")

                    _write_new_ann(ann_path, yolov5_ann)
                    img_path = os.path.join(val_images_dir, img_name)
                    val_image_paths.append(img_path)
                    image_processed = True
                    val_count += 1

                if not image_processed:
                    _add_to_split(
                        image_id,
                        img_name,
                        train_ids,
                        train_image_paths,
                        train_labels_dir,
                        train_images_dir,
                    )
                    train_count += 1
            a_progress.iters_done_report(len(batch))

        ids_to_download = train_ids + val_ids
        paths_to_download = train_image_paths + val_image_paths
        i_rogress = sly.Progress("Downloading images...", total_cnt=len(ids_to_download))
        coro = api.image.download_paths_async(
            ids_to_download, paths_to_download, progress_cb=i_rogress.iters_done_report
        )
        loop = sly.utils.get_or_create_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            future.result()
        else:
            loop.run_until_complete(coro)

        if unsupported_shapes > 0:
            sly.logger.warning(
                f"Dataset {dataset.name}: "
                f"{unsupported_shapes} objects with unsupported geometry types have been {process_shapes_message}"
            )

        progress.iters_done_report(len(ids_to_download))

    data_yaml = {
        "train": "../{}/images/train".format(result_dir_name),
        "val": "../{}/images/val".format(result_dir_name),
        "nc": len(class_names),
        "names": class_names,
        "colors": class_colors,
    }
    with open(config_path, "w") as f:
        yaml.dump(data_yaml, f, default_flow_style=None)

    sly.logger.info("Number of images in train: {}".format(train_count))
    sly.logger.info("Number of images in val: {}".format(val_count))

    # Archiving and uploading the directory to the TeamFiles.
    file_info = sly.output.set_download(result_dir)
    sly.logger.info("File uploaded, app stopped.")
    # --------------------------------- Add Workflow Input And Output -------------------------------- #
    add_input(api, project_id)
    add_output(api, file_info)
    # --------------------------------- Add Workflow Input And Output -------------------------------- #


if __name__ == "__main__":
    api = sly.Api.from_env()
    if api.server_address == "https://app.supervisely.com":
        semaphore = api.get_default_semaphore()
        if semaphore._value == 10:
            api.set_semaphore_size(7)
    transform(api)
