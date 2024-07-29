import supervisely as sly


def check_compatibility(func):
    def wrapper(self, *args, **kwargs):
        if self.is_compatible is None:
            try:
                self.is_compatible = self.check_instance_ver_compatibility()
            except Exception as e:
                sly.logger.error(
                    "Can not check compatibility with Supervisely instance. "
                    f"Workflow features will be disabled. Error: {repr(e)}"
                )
                self.is_compatible = False
        if not self.is_compatible:
            return
        return func(self, *args, **kwargs)

    return wrapper


class Workflow:
    def __init__(self, api: sly.Api, min_instance_version: str = None):
        self.is_compatible = None
        self.api = api
        self._min_instance_version = (
            "6.9.31" if min_instance_version is None else min_instance_version
        )

    def check_instance_ver_compatibility(self):
        if not self.api.is_version_supported(self._min_instance_version):
            sly.logger.info(
                f"Supervisely instance version {self.api.instance_version} does not support workflow features."
            )
            if not sly.is_community():
                sly.logger.info(
                    f"To use them, please update your instance to version {self._min_instance_version} or higher."
                )
            return False
        return True

    @check_compatibility
    def add_input(self, project_id: int):
        self.api.app.workflow.add_input_project(project_id)
        sly.logger.debug(f"Workflow: Input project - {project_id}")

    @check_compatibility
    def add_output(self, file_info: sly.api.file_api.FileInfo):
        try:
            meta = {
                "customRelationSettings": {
                    "icon": {
                        "icon": "zmdi-archive",
                        "color": "#33c94c",
                        "backgroundColor": "#d9f7e4",
                    },
                    "mainLink": {"url": f"{file_info.full_storage_url}", "title": "Download"},
                }
            }
            self.api.app.workflow.add_output_file(file_info, meta)
            sly.logger.debug(f"Workflow: Output file - {file_info.id if file_info else None}")
        except Exception as e:
            sly.logger.debug(f"Workflow: Can not add output file. Error: {repr(e)}")
