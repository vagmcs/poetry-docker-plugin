# Types
from typing import Dict, List, Optional

# Standard Library
import abc
import os
import subprocess

# Dependencies
from cleo.io.io import IO


class Instruction(metaclass=abc.ABCMeta):
    """
    Docker instruction metaclass is extended by every docker command that
    needs to be supported by the plugin.
    """

    pass


class Arg(Instruction):
    def __init__(self, arg_name: str, default_value: Optional[str] = None):
        """
        Creates a docker ARG instruction:

        https://docs.docker.com/engine/reference/builder/#arg

        :param arg_name: the argument name
        :param default_value: a default value (optional)
        """
        self._arg_name = arg_name
        self._default_value = default_value

    def __str__(self):
        return f"ARG {self._arg_name}={self._default_value}" if self._default_value else f"ARG {self._arg_name}"


class Labels(Instruction):
    def __init__(self, labels: Dict[str, str]):
        """
        Creates a docker LABEL instruction:

        https://docs.docker.com/engine/reference/builder/#label

        :param labels: a dictionary of key/value labels
        """
        self._labels = labels

    def __str__(self):
        return "\n".join([f"LABEL {key}={value}" for key, value in self._labels.items()])


class From(Instruction):
    def __init__(self, base_image: str, platform: Optional[str] = None):
        """
        Creates a docker FROM instruction:

        https://docs.docker.com/engine/reference/builder/#from

        :param base_image: the base image tag
        :param platform: the target platform (optional)
        """
        self._base_image = base_image
        self._platform = platform

    def __str__(self):
        return (
            f"FROM {self._base_image}"
            if self._platform is None
            else f"FROM --platform {self._platform} {self._base_image}"
        )


class Copy(Instruction):
    def __init__(self, source: str, destination: str):
        """
        Creates a docker COPY instruction:

        https://docs.docker.com/engine/reference/builder/#copy

        :param source: the source file to copy
        :param destination: the destination inside docker container
        """

        self._source = source
        self._destination = destination

    def __str__(self):
        return f"COPY {self._source} {self._destination}"


class Env(Instruction):
    def __init__(self, env_name: str, value: str):
        """
        Creates a docker ENV instruction:

        https://docs.docker.com/engine/reference/builder/#env

        :param env_name: the name of the environment variable
        :param value: the value assigned to the variable
        """
        self._env_name = env_name
        self._value = value

    def __str__(self):
        return f'ENV {self._env_name}="{self._value}"'


class Expose(Instruction):
    def __init__(self, port: int):
        """
        Creates a docker EXPOSE instruction:

        https://docs.docker.com/engine/reference/builder/#expose

        :param port: a port to expose
        """
        if port < 0:
            raise RuntimeError("Port numbers cannot be negative.")

        self._port = port

    def __str__(self):
        return f"EXPOSE {self._port}"


class Volume(Instruction):
    def __init__(self, path: str):
        """
        Creates a docker VOLUME instruction:

        https://docs.docker.com/engine/reference/builder/#volume

        :param path: path to the volume location
        """
        self._path = path

    def __str__(self):
        return f"VOLUME {self._path}"


class WorkDir(Instruction):
    def __init__(self, path: str):
        """
        Creates a docker WORKDIR instruction:

        https://docs.docker.com/engine/reference/builder/#workdir

        :param path: working directory path inside the container
        """
        self._path = path

    def __str__(self):
        return f"WORKDIR {self._path}"


class User(Instruction):
    def __init__(self, user: str, group: Optional[str] = None):
        """
        Creates a docker USER instruction:

        https://docs.docker.com/engine/reference/builder/#user

        :param user: a default user for the remainder of the stage
        :param group: a default group for the user
        """
        self._user = user
        self._group = group

    def __str__(self):
        return f"USER {self._user}" if self._group is None else f"USER {self._user}:{self._group}"


class Run(Instruction):
    def __init__(self, command: str):
        """
        Creates a docker RUN instruction:

        https://docs.docker.com/engine/reference/builder/#run

        Only shell form commands are supported in RUN instructions because they
        inherit environment variables from the shell, and allow sub commands,
        piping output, chaining commands, and I/O redirection.

        :param command: a shell command to run
        """
        self._command = command

    def __str__(self):
        return f"RUN {self._command}"


class Cmd(Instruction):
    def __init__(self, args: List[str]):
        """
        Creates a docker CMD instruction:

        https://docs.docker.com/engine/reference/builder/#cmd

        Only exec form commands are supported in CMD instructions because most
        shells do not forward process signals to child processes, which means
        the SIGINT generated by pressing CTRL-C may not stop a child process.

        :param args: a list of commands, arguments and parameters
        """
        self._args = args

    def __str__(self):
        return f"CMD {str(self._args)}"


class EntryPoint(Instruction):
    def __init__(self, args: List[str]):
        """
        Creates a docker ENTRYPOINT instruction:

        https://docs.docker.com/engine/reference/builder/#entrypoint

        Only exec form commands are supported in CMD instructions because most
        shells do not forward process signals to child processes, which means
        the SIGINT generated by pressing CTRL-C may not stop a child process.

        :param args: a list of commands, arguments and parameters
        """
        self._args = args

    def __str__(self):
        return f"ENTRYPOINT {str(self._args)}"


class DockerFile(object):
    def __init__(self, io: IO, instructions: Optional[List[Instruction]] = None):
        """
        Creates a docker file from a sequence of instructions.

        :param instructions: a list of instructions to pre-append (optional)
        """
        self._io = io
        self._instructions = [] if instructions is None else instructions

    def add(self, instruction: Instruction) -> None:
        """
        Adds a given docker instruction to the build.

        :param instruction: a docker instruction
        """
        self._instructions.append(instruction)

    def build(self, image_name: str) -> None:
        """
        Builds the docker image.

        :param image_name: a name for the docker image
        """
        if not os.path.exists("dist"):
            os.makedirs("dist")

        with open("dist/Dockerfile", "w") as docker_file:
            for instruction in self._instructions:
                docker_file.write(str(instruction))
                docker_file.write(os.linesep)

        result = subprocess.run(
            ["docker", "build", "--tag", image_name, "--file", "dist/Dockerfile", os.path.abspath("dist")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )

        if result.returncode == 0:
            self._io.write_line(f"<b>poetry-version-plugin</b>: Image '{image_name}' was successfully created!")
            return
