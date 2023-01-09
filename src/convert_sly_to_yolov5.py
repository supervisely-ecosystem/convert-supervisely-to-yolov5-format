import os
import sys
import yaml

import supervisely as sly
from supervisely.app.v1.app_service import AppService

app_root_directory = os.path.dirname(os.getcwd())
sys.path.append(app_root_directory)
sys.path.append(os.path.join(app_root_directory, "src"))
print(f"App root directory: {app_root_directory}")
sly.logger.info(f'PYTHONPATH={os.environ.get("PYTHONPATH", "")}')

# order matters
# from dotenv import load_dotenv
# load_dotenv(os.path.join(app_root_directory, "secret_debug.env"))
# load_dotenv(os.path.join(app_root_directory, "debug.env"))

my_app = AppService()

TEAM_ID = int(os.environ['context.teamId'])
WORKSPACE_ID = int(os.environ['context.workspaceId'])
PROJECT_ID = int(os.environ['modal.state.slyProjectId'])

TRAIN_TAG_NAME = 'train'
VAL_TAG_NAME = 'val'


def transform_label(class_names, img_size, label: sly.Label):
    class_number = class_names.index(label.obj_class.name)
    rect_geometry = label.geometry.to_bbox()
    center = rect_geometry.center
    x_center = round(center.col / img_size[1], 6)
    y_center = round(center.row / img_size[0], 6)
    width = round(rect_geometry.width / img_size[1], 6)
    height = round(rect_geometry.height / img_size[0], 6)
    return f'{class_number} {x_center} {y_center} {width} {height}'


@my_app.callback("transform")
@sly.timeit
def transform(api: sly.Api, task_id, context, state, app_logger):
    project = api.project.get_info_by_id(PROJECT_ID)
    result_dir_name = "{}_{}".format(project.id, project.name)

    RESULT_DIR = os.path.join(my_app.data_dir, result_dir_name)
    sly.fs.mkdir(RESULT_DIR)
    ARCHIVE_NAME = f"{result_dir_name}.tar"
    RESULT_ARCHIVE = os.path.join(my_app.data_dir, ARCHIVE_NAME)
    CONFIG_PATH = os.path.join(RESULT_DIR, 'data_config.yaml')

    TRAIN_IMAGES_DIR = os.path.join(RESULT_DIR, 'images/train')
    TRAIN_LABELS_DIR = os.path.join(RESULT_DIR, 'labels/train')
    sly.fs.mkdir(TRAIN_IMAGES_DIR)
    sly.fs.mkdir(TRAIN_LABELS_DIR)

    VAL_IMAGES_DIR = os.path.join(RESULT_DIR, 'images/val')
    VAL_LABELS_DIR = os.path.join(RESULT_DIR, 'labels/val')
    sly.fs.mkdir(VAL_IMAGES_DIR)
    sly.fs.mkdir(VAL_LABELS_DIR)

    meta_json = api.project.get_meta(PROJECT_ID)
    meta = sly.ProjectMeta.from_json(meta_json)
    class_names = [obj_class.name for obj_class in meta.obj_classes]
    class_colors = [obj_class.color for obj_class in meta.obj_classes]

    if meta.get_tag_meta(TRAIN_TAG_NAME) is None:
        app_logger.warn('Tag {!r} not found in project meta. Images without special tags will be marked as train'
                        .format(TRAIN_TAG_NAME))

    if meta.get_tag_meta(VAL_TAG_NAME) is None:
        app_logger.warn('Tag {!r} not found in project meta. Images without special tags will be marked as train'
                        .format(VAL_TAG_NAME))

    error_classes = []
    for obj_class in meta.obj_classes:
        if obj_class.geometry_type != sly.Rectangle:
            error_classes.append(obj_class.name)
    if len(error_classes) > 0:
        raise RuntimeError("Project has unsupported classes: {}. All classes in project must have shape 'Rectangle'. "
                           "Use 'Convert Class Shape' app to transform shapes to Rectangles or clone project and remove "
                           "unnecessary classes.".format(error_classes))

    def _write_new_ann(path, content):
        with open(path, 'a') as f1:
            f1.write("\n".join(content))

    def _add_to_split(image_id, img_name, split_ids, split_image_paths, labels_dir, images_dir):
        split_ids.append(image_id)
        ann_path = os.path.join(labels_dir, f'{sly.fs.get_file_name(img_name)}.txt')
        _write_new_ann(ann_path, yolov5_ann)
        img_path = os.path.join(images_dir, img_name)
        split_image_paths.append(img_path)

    train_count = 0
    val_count = 0

    progress = sly.Progress("Transformation ...", api.project.get_images_count(PROJECT_ID))
    for dataset in api.dataset.get_list(PROJECT_ID):
        images = api.image.get_list(dataset.id)

        train_ids = []
        train_image_paths = []
        val_ids = []
        val_image_paths = []

        for batch in sly.batched(images):
            image_ids = [image_info.id for image_info in batch]
            image_names = [f"{dataset.name}_{image_info.name}" for image_info in batch]
            ann_infos = api.annotation.download_batch(dataset.id, image_ids)


            for image_id, img_name, ann_info in zip(image_ids, image_names, ann_infos):
                ann_json = ann_info.annotation
                ann = sly.Annotation.from_json(ann_json, meta)

                yolov5_ann = []
                for label in ann.labels:
                    yolov5_ann.append(transform_label(class_names, ann.img_size, label))

                image_processed = False
                if ann.img_tags.get(TRAIN_TAG_NAME) is not None:
                    _add_to_split(image_id, img_name, train_ids, train_image_paths, TRAIN_LABELS_DIR, TRAIN_IMAGES_DIR)
                    image_processed = True
                    train_count += 1

                if ann.img_tags.get(VAL_TAG_NAME) is not None:
                    val_ids.append(image_id)
                    ann_path = os.path.join(VAL_LABELS_DIR, f'{sly.fs.get_file_name(img_name)}.txt')

                    _write_new_ann(ann_path, yolov5_ann)
                    img_path = os.path.join(VAL_IMAGES_DIR, img_name)
                    val_image_paths.append(img_path)
                    image_processed = True
                    val_count += 1

                if not image_processed:
                    app_logger.warn("Image does not have train or val tags. It will be placed to training set.",
                                    extra={"image_id": image_id, "image_name": img_name, "dataset": dataset.name})
                    _add_to_split(image_id, img_name, train_ids, train_image_paths, TRAIN_LABELS_DIR, TRAIN_IMAGES_DIR)
                    train_count += 1

        api.image.download_paths(dataset.id, train_ids, train_image_paths)
        api.image.download_paths(dataset.id, val_ids, val_image_paths)

        progress.iters_done_report(len(batch))

    data_yaml = {
        "train": "../{}/images/train".format(result_dir_name),
        "val": "../{}/images/val".format(result_dir_name),
        "nc": len(class_names),
        "names": class_names,
        "colors": class_colors
    }
    with open(CONFIG_PATH, 'w') as f:
        data = yaml.dump(data_yaml, f, default_flow_style=None)

    app_logger.info("Number of images in train == {}".format(train_count))
    app_logger.info("Number of images in val == {}".format(val_count))

    sly.fs.archive_directory(RESULT_DIR, RESULT_ARCHIVE)
    app_logger.info("Result directory is archived")

    remote_archive_path = os.path.join(
        sly.team_files.RECOMMENDED_EXPORT_PATH, "yolov5_format/{}/{}".format(task_id, ARCHIVE_NAME))

    #@TODO: uncomment only for debug
    #api.file.remove(TEAM_ID, remote_archive_path)

    upload_progress = []
    def _print_progress(monitor, upload_progress):
        if len(upload_progress) == 0:
            upload_progress.append(sly.Progress(message="Upload {!r}".format(ARCHIVE_NAME),
                                                total_cnt=monitor.len,
                                                ext_logger=app_logger,
                                                is_size=True))
        upload_progress[0].set_current_value(monitor.bytes_read)

    file_info = api.file.upload(TEAM_ID, RESULT_ARCHIVE, remote_archive_path, lambda m: _print_progress(m, upload_progress))
    app_logger.info("Uploaded to Team-Files: {!r}".format(file_info.storage_path))
    api.task.set_output_archive(task_id, file_info.id, ARCHIVE_NAME, file_url=file_info.storage_path)

    my_app.stop()


def main():
    sly.logger.info("Script arguments", extra={
        "context.teamId": TEAM_ID,
        "context.workspaceId": WORKSPACE_ID,
        "modal.state.slyProjectId": PROJECT_ID,
        "CONFIG_DIR": os.environ.get("CONFIG_DIR", "ENV not found")
    })

    api = sly.Api.from_env()

    # Run application service
    my_app.run(initial_events=[{"command": "transform"}])


#@TODO: add information to modal window
if __name__ == "__main__":
    #@TODO: uncomment only for debug
    #sly.fs.clean_dir(my_app.data_dir)

    sly.main_wrapper("main", main)
