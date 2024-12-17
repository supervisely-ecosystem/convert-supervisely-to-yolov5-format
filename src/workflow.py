import supervisely as sly


def add_input(api: sly.Api, project_id: int):
    api.app.workflow.add_input_project(project_id)
    sly.logger.debug(f"Workflow: Input project - {project_id}")


def add_output(api: sly.Api, file_info: sly.api.file_api.FileInfo):
    try:
        meta = {
            "customRelationSettings": {
                "icon": {
                    "icon": "zmdi-archive",
                    "color": "#33c94c",
                    "backgroundColor": "#d9f7e4",
                },
                "title": f"<h4>{file_info.name}</h4>",
                "mainLink": {
                    "url": f"/files/{file_info.id}/true/?teamId={file_info.team_id}",
                    "title": "Download",
                },
            }
        }
        api.app.workflow.add_output_file(file_info, meta=meta)
        sly.logger.debug(f"Workflow: Output file - {file_info.id if file_info else None}")
    except Exception as e:
        sly.logger.debug(f"Workflow: Can not add output file. Error: {repr(e)}")
