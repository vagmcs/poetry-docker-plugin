# Types
from typing import Any

# Standard Library
import re

# Dependencies
from cleo.application import Application
from cleo.commands.command import Command
from poetry.plugins.application_plugin import ApplicationPlugin

from .docker_builder import *


class DockerBuild(Command):
    name = "docker"
    description = "Builds docker image."

    def handle(self) -> int:
        pyproject_config = self.application.poetry.pyproject.data
        config: Optional[Dict[str, Any]] = pyproject_config.get("tool", dict()).get("docker")

        if config is None:
            message = "<b>poetry-docker-plugin</b>: No configuration found in [tool.docker] in pyproject.toml"
            self.io.write_error_line(message)
            raise RuntimeError(message)

        image_name = config.get("image_name")
        if image_name is None or re.search(".*/.*?(:.*)", image_name) is None:
            org: str = (
                re.match("(.*)<.*>", pyproject_config.get("tool").get("poetry").get("authors")[0])
                .group(1)
                .strip()
                .lower()
                .replace(" ", ".")
            )
            name: str = pyproject_config.get("tool").get("poetry").get("name")
            image_name = f"{org}/{name}:latest"
            self.io.write_line(f"Image name is not defined, using '{image_name}'.")

        # Create docker file
        docker_file = DockerFile(self.io)

        # Append all docker ARG
        args = config.get("args", dict())
        for arg, default_value in args.items():
            docker_file.add(Arg(arg, default_value))

        # Append FROM command
        base_image: Optional[str] = config.get("from")
        if base_image is None:
            message = "<b>poetry-docker-plugin</b>: No from statement found in [tool.docker] in pyproject.toml"
            self.io.write_error_line(message)
            raise RuntimeError(message)
        else:
            docker_file.add(From(base_image))

        # Append all docker LABEL
        labels: Dict[str, str] = config.get("labels", dict())
        docker_file.add(Labels(labels))

        # Append COPY commands
        copy_statements: List[Dict[str, str]] = config.get("copy", dict())
        for statement in copy_statements:

            if "source" not in statement or "target" not in statement:
                message = f"<b>poetry-docker-plugin</b>: Source/target not present in copy command '{str(statement)}'"
                self.io.write_error_line(message)
                raise RuntimeError(message)

            docker_file.add(Copy(statement.get("source"), statement.get("target")))

        # Append ENV commands
        env = config.get("env", dict())
        for env_name, value in env.items():
            docker_file.add(Env(env_name, value))

        # Append EXPOSE command
        ports = config.get("expose", list())
        for port in ports:
            docker_file.add(Expose(port))

        # Append VOLUME commands
        volumes = config.get("volume", list())
        for vol in volumes:
            docker_file.add(Volume(vol))

        # Append WORKDIR, USER, and RUN commands
        flow = config.get("flow", list())
        for instruction in flow:
            if "work_dir" in instruction:
                docker_file.add(WorkDir(instruction["work_dir"]))
            elif "user" in instruction:
                docker_file.add(User(instruction["user"]))
            elif "run" in instruction:
                docker_file.add(Run(instruction["run"]))
            else:
                self.io.write_error_line(f"Unknown command '{instruction}'")

        # Append CMD command
        cmd = config.get("cmd")
        if cmd is not None:
            docker_file.add(Cmd(list(cmd)))

        # Append ENTRYPOINT command
        entry_point = config.get("entrypoint")
        if entry_point is not None:
            docker_file.add(EntryPoint(list(entry_point)))

        docker_file.build(image_name)
        return 0


def factory():
    return DockerBuild()


class DockerPlugin(ApplicationPlugin):
    def activate(self, application: Application) -> None:
        application.command_loader.register_factory("docker", factory)
