<div align="center" markdown>
<img src="https://user-images.githubusercontent.com/106374579/183683758-89476d80-de3f-424f-9bfa-f1562703a168.png"/>

# From Supervisely to YOLOv5 format


<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a>
</p>

[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervisely.com/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/convert-supervisely-to-yolov5-format)
[![views](https://app.supervisely.com/img/badges/views/supervisely-ecosystem/convert-supervisely-to-yolov5-format.png)](https://supervisely.com)
[![runs](https://app.supervisely.com/img/badges/runs/supervisely-ecosystem/convert-supervisely-to-yolov5-format.png)](https://supervisely.com)

</div>

## Overview

Transform images project in Supervisely ([link to format](https://docs.supervisely.com/data-organization/00_ann_format_navi)) to [YOLO v5 format](https://github.com/ultralytics/yolov5/wiki/Train-Custom-Data) and prepares downloadable `tar` archive.


## Preparation

Supervisely project have to contain only classes with shape `Rectangle`. It means that all labeled objects have to be bounding boxes. If your project has classes with other shapes and you would like to convert the shapes of these classes and all corresponding objects (e.g. bitmaps or polygons to rectangles), we recommend you to use [`Convert Class Shape`](https://ecosystem.supervisely.com/apps/convert-class-shape) app. 

In addition, YOLO v5 format implies the presence of train/val datasets. Thus, to split images on training and validation datasets you should assign  corresponding tags (`train` or `val`) to images. If image doesn't have such tags, it will be treated as `train`. We recommend to use app [`Assign train/val tags to images`](https://ecosystem.supervisely.com/apps/tag-train-val-test). 


## How To Run 
**Step 1**: Add app to your team from [Ecosystem](https://ecosystem.supervisely.com/apps/convert-supervisely-to-yolov5-format) if it is not there.

**Step 2**: Open context menu of project -> `Download as` -> `Convert Supervisely to YOLO v5 format` 

<img src="https://i.imgur.com/bOUC5WH.png" width="600px"/>


## How to use

App creates task in `workspace tasks` list. Once app is finished, you will see download link to resulting tar archive. 

<img src="https://i.imgur.com/kXnmshv.png"/>

Resulting archive is saved in : 

`Current Team` -> `Files` -> `/yolov5_format/<task_id>/<project_id>_<project_name>.tar`. 

For example our file path is the following: 

`/yolov5_format/1430/1047_lemons_annotated.tar`.

<img src="https://i.imgur.com/hGrAyY0.png"/>

If some images were not tagged with `train` or `val` tags, special warning is printed. You will see all warnings in task logs.

<img src="https://i.imgur.com/O5tshZQ.png"/>


Here is the example of `data_config.yaml` that you will find in archive:


```yaml
names: [kiwi, lemon]            # class names
colors: [[255,1,1], [1,255,1]]  # class colors
nc: 2                           # number of classes
train: ../lemons/images/train   # path to train imgs
val: ../lemons/images/val       # path to val imgs
```
