# Types
from typing import Any, Dict, List, NoReturn, Optional

# Standard Library
import re

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
            long_name="build-only" ,
            description="Builds only selected images.",
            flag=False,
            value_required=False,
            multiple=True,
        ),
        option(
            short_name="p",
            long_name="platform",
            description="Sets the target platform.",
            flag=False,
            value_required=False,
            default="linux/amd64",
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

        # extract project name, version, authors and python
        project_name = pyproject_config.get("tool").get("poetry").get("name")
        project_version = pyproject_config.get("tool").get("poetry").get("version")
        project_authors = pyproject_config.get("tool").get("poetry").get("authors")
        full_python_version = pyproject_config.get("tool").get("poetry").get("dependencies").get("python")

        try:
            commit_sha = git.Repo(search_parent_directories=True).head.object.hexsha[:7]
        except git.InvalidGitRepositoryError:
            self.error("Invalid git repository. Cannot retrieve commit SHA.")

        # package the project
        if not self.option("exclude-package"):
            self.call("build")

        for image_suffix in multiple_images:
            image_config = config if image_suffix is None else config[image_suffix]  # type: ignore
            self._build_image(
                project_name,
                project_version,
                project_authors,
                full_python_version,
                commit_sha,
                image_config,
                image_suffix,  # type: ignore
            )

        return 0

    def _build_image(
        self,
        project_name: str,
        project_version: str,
        project_authors: List[str],
        full_python_version: str,
        commit_sha: str,
        image_config: Dict[str, Any],
        image_suffix: str,
    ) -> None:
        def replace_build_in_vars(text: str) -> str:
            return (
                text.replace("@(name)", project_name.replace("-", "_"))
                .replace("@(version)", project_version)
                .replace("@(pyversion)", full_python_version.removeprefix("^").removeprefix("~"))
                .replace("@(sha)", commit_sha)
            )

        exclude_package: bool = self.option("exclude-package")

        image_tags = [replace_build_in_vars(tag) for tag in image_config.get("tags", list())]
        if not image_tags or any([re.search(".*/.*?(:.*)", tag) is None for tag in image_tags]):

            author_name = re.match("([\\w+\\s*]+)(<.*>)?", project_authors[0])
            if author_name is None:
                self.error("Author name cannot be matched.")

            org: str = author_name.group(1).strip().lower().replace(" ", ".")
            name: str = project_name if image_suffix is None else f"{project_name}-{image_suffix}"
            image_tags = [f"{org}/{name}:latest"]
            self.info(f"Image tags are not defined or are invalid, using '{image_tags}'.")
        else:
            self.info(f"Found images tags: {list(image_tags)}")

        # Create docker file
        docker_file = DockerFile(self.io)

        # Append all docker ARG
        args = image_config.get("args", dict())
        for arg, default_value in args.items():
            docker_file.add(Arg(arg, default_value))

        # Append FROM command
        base_image: Optional[str] = image_config.get("from")
        if base_image is None:
            python_version = re.match("\\^?(\\d\\.\\d+)(\\.\\d+)?", full_python_version)
            if python_version is not None:
                python_version = python_version.group(1)  # type: ignore
            self.warning(
                f"No 'from' statement found in [tool.docker] in pyproject.toml, "
                f"using 'python:{python_version}' as base image."
            )
            docker_file.add(From(f"python:{python_version}"))
        else:
            docker_file.add(From(base_image))

        # Append all docker LABEL
        labels: Dict[str, str] = image_config.get("labels", dict())
        docker_file.add(Labels(labels))

        # Append COPY commands
        copy_statements: List[Dict[str, str]] = image_config.get("copy", dict())
        # unless excluded copy the distribution package into the container
        if not exclude_package:
            docker_file.add(
                Copy(
                    f"{project_name.replace('-', '_')}-{project_version}.tar.gz",
                    f"/package/{project_name.replace('-', '_')}-{project_version}.tar.gz",
                )
            )
        for statement in copy_statements:
            if "source" not in statement or "target" not in statement:
                self.error(f"Source/target not present in copy command: {str(statement)}")

            docker_file.add(
                Copy(replace_build_in_vars(statement["source"]), replace_build_in_vars(statement["target"]))
            )

        # Append ENV commands
        env = image_config.get("env", dict())
        for env_name, value in env.items():
            docker_file.add(Env(env_name, value))

        # Append VOLUME commands
        volumes = image_config.get("volume", list())
        for vol in volumes:
            docker_file.add(Volume(vol))

        # Append WORKDIR, USER, and RUN commands
        flow = image_config.get("flow", list())
        # unless excluded, install package
        if not exclude_package:
            docker_file.add(Run(f"pip install /package/{project_name.replace('-', '_')}-{project_version}.tar.gz"))
        for instruction in flow:
            if "work_dir" in instruction:
                docker_file.add(WorkDir(replace_build_in_vars(instruction["work_dir"])))
            elif "user" in instruction:
                docker_file.add(User(replace_build_in_vars(instruction["user"])))
            elif "run" in instruction:
                docker_file.add(Run(replace_build_in_vars(instruction["run"])))
            else:
                self.io.write_error_line(f"Unknown command '{instruction}'")

        # Append EXPOSE command
        ports = image_config.get("expose", list())
        for port in ports:
            docker_file.add(Expose(port))

        # Append CMD command
        cmd = image_config.get("cmd")
        if cmd is not None:
            docker_file.add(Cmd(list(cmd)))

        # Append ENTRYPOINT command
        entry_point = image_config.get("entrypoint")
        if entry_point is not None:
            docker_file.add(EntryPoint(list(entry_point)))

        dockerfile_name = "Dockerfile" if image_suffix is None else f"Dockerfile_{image_suffix}"
        if self.option("dockerfile-only"):
            docker_file.create(dockerfile_name)
        else:
            self.info(f"Building docker image for platforms: '{self.option('platform')}'.")
            docker_file.build(image_tags, self.option("platform"), dockerfile_name, self.option("push"))
        self.info(f"Dockerfile is located in 'dist/{dockerfile_name}'.")


def factory() -> DockerBuild:
    return DockerBuild()


class DockerPlugin(ApplicationPlugin):
    def activate(self, application: Application) -> None:
        application.command_loader.register_factory("docker", factory)  # type: ignore
