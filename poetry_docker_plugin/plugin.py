# Types
from typing import Any, Dict, List, NoReturn, Optional

# Standard Library
import re
import sys

# Dependencies
import git
from cleo.application import Application
from cleo.commands.command import Command
from cleo.helpers import option
from poetry.plugins.application_plugin import ApplicationPlugin

from .docker_builder import (
    COMMANDS,
    Arg,
    Cmd,
    Copy,
    DockerFile,
    EntryPoint,
    Env,
    Expose,
    From,
    Labels,
    Run,
    User,
    Volume,
    WorkDir,
)


class DockerBuild(Command):
    name = "docker"
    description = "Builds docker image."

    # list of command options
    options = [
        option(
            long_name="dockerfile-only",
            description="Creates Dockerfile, but does not build the image.",
            flag=True,
            value_required=False,
        ),
        option(
            long_name="build-only",
            description="Builds only selected images.",
            flag=False,
            value_required=False,
            multiple=True,
        ),
        option(
            short_name="p",
            long_name="platform",
            description="Sets a target platform.",
            flag=False,
            value_required=False,
            multiple=True,
        ),
        option(
            long_name="exclude-package",
            description="Does not install project package inside docker container.",
            flag=True,
            value_required=False,
        ),
        option(
            long_name="push",
            description="Pushes the image to the registry.",
            flag=True,
            value_required=False,
        ),
        option(
            short_name="r",
            long_name="var",
            description="Declares a custom variable using the syntax 'name:value'. "
            "Then, the variable can be used in the docker configuration using: @(name).",
            flag=False,
            value_required=False,
            multiple=True,
        ),
        option(
            short_name="a",
            long_name="arg",
            description="Declares a build argument using the syntax 'name:value'",
            flag=False,
            value_required=False,
            multiple=True,
        ),
    ]

    def info(self, message: str) -> None:
        self.io.write_line(f"<info>[INFO]:</info> {message}")

    def debug(self, message: str) -> None:
        self.io.write_line(f"<debug>[DEBUG]:</debug> {message}")

    def warning(self, message: str) -> None:
        self.io.write_line(f"<warning>[WARN]:</warning> {message}")

    def error(self, message: str) -> NoReturn:
        self.io.write_error_line(f"<error>[ERROR]:</error> {message}")
        raise RuntimeError(message)

    def handle(self) -> int:
        pyproject_config = self.application.poetry.pyproject.data  # type: ignore
        config: Dict[str, Any] = pyproject_config.get("tool", dict()).get("docker", dict())

        # if no configuration exists, then stop execution
        if not config:
            self.error("No configuration found in [tool.docker] in pyproject.toml")

        # infer image(s) structure
        multiple_images = {None}
        if all(entry not in COMMANDS for entry in set(config)):
            if all(entry in COMMANDS for image in set(config) for entry in config[image]):
                multiple_images = set(config)  # type: ignore
                self.info(f"Detected '{len(set(config))}' image(s): {list(set(config))}.")

                # check if only a subset of images should be build
                if self.option("build-only"):
                    selected = set(self.option("build-only"))
                    multiple_images = multiple_images.intersection(selected)
                    self.warning(f"Building only image(s): {list(multiple_images)}.")
            else:
                for image in set(config):
                    if any(entry not in COMMANDS for entry in config[image]):
                        self.error(
                            f"Image [{image}] has unknown commands: {','.join(set(config[image]).difference(COMMANDS))}"
                        )

        elif any(entry not in COMMANDS for entry in set(config)):
            self.error(f"Unknown commands: {','.join(set(config).difference(COMMANDS))}")

        # extract project name, version, authors and python version
        project_name = pyproject_config.get("tool").get("poetry").get("name")
        project_version = pyproject_config.get("tool").get("poetry").get("version")
        project_authors = pyproject_config.get("tool").get("poetry").get("authors")
        full_python_version = pyproject_config.get("tool").get("poetry").get("dependencies").get("python")
        package_mode = pyproject_config.get("tool").get("poetry").get("package-mode", True)  # if None assume to be True

        # parse Python version
        if full_python_version == "*":
            self.warning("Python version is too generic, using system's running version.")
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        elif re.match("[\\^~]?(\\d\\.\\d+)(\\.\\d+)?", full_python_version) is not None:
            python_version = re.match("[\\^~]?(\\d\\.\\d+)(\\.\\d+)?", full_python_version).group(1)  # type: ignore
        elif re.match("[\\^~]?(\\d)(\\.\\*)?", full_python_version) is not None:
            python_version = re.match("[\\^~]?(\\d)(\\.\\*)?", full_python_version).group(1)  # type: ignore
        else:
            match = re.match(">=?(\\d\\.\\d+)(\\.\\d+)?,<=?(\\d\\.\\d+)(\\.\\d+)?", full_python_version)
            python_version = match.group(1)  # type: ignore
            self.warning(
                f"Found a range of compatible Python versions '{full_python_version}', "
                f"using the oldest for building the image '{python_version}'."
            )

        # try to retrieve commit SHA-256
        commit_sha = None
        try:
            commit_sha = git.Repo(search_parent_directories=True).head.object.hexsha[:7]
        except git.InvalidGitRepositoryError:
            self.warning("Invalid git repository. Cannot retrieve commit SHA.")

        # collect variables
        user_variables = {}
        for var in self.option("var"):
            _var = var.split(":")
            if _var[0] in {"name", "version", "py_version", "sha"}:
                self.error(f"Variable name @({_var[0]}) is already in use by the plugin and cannot be redefined.")
            user_variables[_var[0]] = _var[1]

        # collect arguments
        user_arguments = {}
        for arg in self.option("arg"):
            _arg = arg.split(":")
            user_arguments[_arg[0]] = _arg[1]

        # package the project, unless exclude-package option is specified
        if not self.option("exclude-package") and package_mode:
            self.call("build")

        for config_name in multiple_images:
            image_config = config if config_name is None else config.get(config_name)
            self._build_image(
                project_name,
                project_version,
                project_authors,
                python_version,
                package_mode,
                commit_sha,
                user_variables,
                user_arguments,
                image_config,
                config_name,
            )

        return 0

    def _build_image(
        self,
        project_name: str,
        project_version: str,
        project_authors: List[str],
        python_version: str,
        package_mode: bool,
        commit_sha: Optional[str],
        variables: Dict[str, str],
        user_arguments: Dict[str, str],
        image_config: Dict[str, Any],
        config_name: Optional[str],
    ) -> None:
        def replace_build_in_vars(text: str) -> str:
            _text = (
                text.replace("@(name)", project_name.replace("-", "_"))
                .replace("@(version)", project_version)
                .replace("@(py_version)", python_version)
                .replace("@(sha)", "" if commit_sha is None else commit_sha)
            )

            for var, val in variables.items():
                _text = _text.replace(f"@({var})", val)

            undeclared_vars = re.findall(r"@\([a-zA-Z_]+\)", _text)
            if undeclared_vars:
                self.error(f"No value found for variables '{', '.join(undeclared_vars)}'.")

            return _text

        exclude_package: bool = self.option("exclude-package")

        image_tags = [replace_build_in_vars(tag) for tag in image_config.get("tags", list())]
        if not image_tags or any([re.search(".*/.*?(:.*)", tag) is None for tag in image_tags]):
            author_name = re.match("([\\w+\\s*]+)(<.*>)?", project_authors[0])
            if author_name is None:
                self.error("Author name cannot be matched.")

            org: str = author_name.group(1).strip().lower().replace(" ", ".")
            name: str = project_name if config_name is None else f"{project_name}-{config_name}"
            image_tags = [f"{org}/{name}:latest"]
            self.info(f"Image tags are not defined or are invalid, using '{image_tags}'.")
        else:
            self.info(f"Found images tags: {list(image_tags)}")

        # Create docker file
        docker_file = DockerFile(self.io)

        # Collect all docker ARG and validate that all user arguments exist in the configuration
        args = image_config.get("args", dict())
        for arg, _ in user_arguments.items():
            if arg not in args:
                self.error(f"Argument '{arg}' does not exist in docker config.")

        def __check_and_pre_append_args(*commands: str) -> None:
            for command in commands:
                for arg_name, default_value in args.items():
                    arg_var = f"${{{arg_name}}}"
                    if arg_var in command:
                        docker_file.add(Arg(arg_name, default_value))

        # Append FROM command
        base_image: Optional[str] = image_config.get("from")
        if base_image is None:
            self.warning(
                f"No 'from' statement found in [tool.docker] in pyproject.toml, "
                f"using 'python:{python_version}' as base image."
            )
            docker_file.add(From(f"python:{python_version}"))
        else:
            __check_and_pre_append_args(base_image)
            docker_file.add(From(base_image))

        # Append all docker LABEL
        labels: Dict[str, str] = image_config.get("labels", dict())
        docker_file.add(Labels(labels))

        # Append COPY commands
        copy_statements: List[Dict[str, str]] = image_config.get("copy", dict())
        # unless excluded copy the distribution package into the container
        if not exclude_package and package_mode:
            docker_file.add(
                Copy(
                    f"{project_name.replace('-', '_')}-{project_version}.tar.gz",
                    f"/package/{project_name.replace('-', '_')}-{project_version}.tar.gz",
                )
            )
        for statement in copy_statements:
            if "source" not in statement or "target" not in statement:
                self.error(f"Source/target not present in copy command: {str(statement)}")

            __check_and_pre_append_args(statement["source"], statement["target"])
            docker_file.add(
                Copy(replace_build_in_vars(statement["source"]), replace_build_in_vars(statement["target"]))
            )

        # Append ENV commands
        env = image_config.get("env", dict())
        for env_name, value in env.items():
            __check_and_pre_append_args(value)
            docker_file.add(Env(env_name, value))

        # Append VOLUME commands
        volumes = image_config.get("volume", list())
        for vol in volumes:
            docker_file.add(Volume(vol))

        # Append WORKDIR, USER, and RUN commands
        flow = image_config.get("flow", list())
        # unless excluded, install package
        if not exclude_package and package_mode:
            docker_file.add(Run(f"pip install /package/{project_name.replace('-', '_')}-{project_version}.tar.gz"))
        for instruction in flow:
            if "work_dir" in instruction:
                __check_and_pre_append_args(instruction["work_dir"])
                docker_file.add(WorkDir(replace_build_in_vars(instruction["work_dir"])))
            elif "user" in instruction:
                __check_and_pre_append_args(instruction["user"])
                docker_file.add(User(replace_build_in_vars(instruction["user"])))
            elif "run" in instruction:
                __check_and_pre_append_args(instruction["run"])
                docker_file.add(Run(replace_build_in_vars(instruction["run"])))
            else:
                self.error(f"Unknown command '{instruction}'")

        # Append EXPOSE command
        ports = image_config.get("expose", list())
        for port in ports:
            docker_file.add(Expose(port))

        # Append CMD command
        cmd = image_config.get("cmd")
        if cmd is not None:
            __check_and_pre_append_args(cmd)
            docker_file.add(Cmd(list(cmd)))

        # Append ENTRYPOINT command
        entry_point = image_config.get("entrypoint")
        if entry_point is not None:
            __check_and_pre_append_args(entry_point)
            docker_file.add(EntryPoint(list(entry_point)))

        dockerfile_name = "Dockerfile" if config_name is None else f"Dockerfile_{config_name}"
        if self.option("dockerfile-only"):
            docker_file.create(dockerfile_name)
        else:
            if self.option("platform") is not None:
                self.info(f"Building docker image for platforms: '{self.option('platform')}'.")
            docker_file.build(image_tags, self.option("platform"), user_arguments, dockerfile_name, self.option("push"))
        self.info(f"Dockerfile is located in 'dist/{dockerfile_name}'.")


def factory() -> DockerBuild:
    return DockerBuild()


class DockerPlugin(ApplicationPlugin):
    def activate(self, application: Application) -> None:
        application.command_loader.register_factory("docker", factory)  # type: ignore
