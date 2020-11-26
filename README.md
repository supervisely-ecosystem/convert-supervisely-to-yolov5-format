<div align="center" markdown>
<img src="https://i.imgur.com/UeObs7R.png"/>

# From supervisely to Yolo5 format


<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a>
</p>

[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/convert-supervisely-to-yolov5-format)
[![views](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/convert-supervisely-to-yolov5-format&counter=views&label=views)](https://supervise.ly)
[![used by teams](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/convert-supervisely-to-yolov5-format&counter=downloads&label=used%20by%20teams)](https://supervise.ly)
[![runs](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/convert-supervisely-to-yolov5-format&counter=runs&label=runs&123)](https://supervise.ly)

</div>

## Overview

Transform images project in Supervisely ([link to format](https://docs.supervise.ly/data-organization/00_ann_format_navi)) to [YOLO v5 format](https://github.com/ultralytics/yolov5/wiki/Train-Custom-Data) and prepares downloadable `tar` archive.


## Preparation

Supervisely project have to contain only classes with shape `Rectangle`. It means that all labeled objects have to be bouning boxes. If you project has classes with other shapes and you would like to convert the shapes of these classes and all corresponding objects (e.g. bitmaps or polygons to rectangles), we recommend you to use [`Convert Class Shape`](https://ecosystem.supervise.ly/apps/convert-class-shape) app. 

## How To Run 
**Step 1**: Add app to your team from Ecosystem if it is not there.

**Step 2**: Open context menu of project -> `Download as` -> `Convert Supervisely to YOLO v5 format` 

![](https://i.imgur.com/bOUC5WH.png)


## How to use

1. Check project you want to convert to yolo5 format.

2. Click three point on project and choise "Download as" option.

3. In popup menu choise "Convert Supervisely into YOLO v5 format".

<img src="https://i.imgur.com/ZTYhihF.png"/>

4. Open "files" menu. Here in directory "yolov5_format" you can find tar archive with project in YOLOv5 format.

<img src="https://i.imgur.com/pu9snon.png"/>



