# Types
from typing import Dict, List, Optional

# Standard Library
import abc
import os
import subprocess

# Dependencies
from cleo.io.io import IO


class Instruction(metaclass=abc.ABCMeta):
    pass


class Arg(Instruction):
    def __init__(self, name: str, default_value: Optional[str] = None):
        self._name = name
        self._default_value = default_value

    def __str__(self):
        return f"ARG {self._name}={self._default_value}" if self._default_value else f"ARG {self._name}"


class Labels(Instruction):
    def __init__(self, labels: Dict[str, str]):
        self._labels = labels

    def __str__(self):
        return f"LABEL {str(self._labels).replace(': ', '=').replace('{', '').replace('}', '')}"


class From(Instruction):
    def __init__(self, base_image: str):
        self._base_image = base_image

    def __str__(self):
        return f"FROM {self._base_image}"


class Copy(Instruction):
    def __init__(self, source: str, destination: str):
        self._source = source
        self._destination = destination

    def __str__(self):
        return f"COPY {self._source} {self._destination}"


class Env(Instruction):
    def __init__(self, name: str, value: str):
        self._name = name
        self._value = value

    def __str__(self):
        return f'ENV {self._name}="{self._value}"'


class Expose(Instruction):
    def __init__(self, port: int):
        self._port = port

    def __str__(self):
        return f"EXPOSE {self._port}"


class Volume(Instruction):
    def __init__(self, path: str):
        self._path = path

    def __str__(self):
        return f"VOLUME {self._path}"


class WorkDir(Instruction):
    def __init__(self, path: str):
        self._path = path

    def __str__(self):
        return f"WORKDIR {self._path}"


class User(Instruction):
    def __init__(self, user: str):
        self._user = user

    def __str__(self):
        return f"USER {self._user}"


class Run(Instruction):
    def __init__(self, command: str):
        self._command = command

    def __str__(self):
        return f"RUN {self._command}"


class Cmd(Instruction):
    def __init__(self, args: List[str]):
        self._args = args

    def __str__(self):
        return f"CMD {str(self._args)}"


class EntryPoint(Instruction):
    def __init__(self, command: str):
        self._command = command

    def __str__(self):
        return f"ENTRYPOINT {self._command}"


class DockerFile(object):
    def __init__(self, io: IO, instructions: Optional[List[Instruction]] = None):
        self._io = io
        self._instructions = [] if instructions is None else instructions

    def add(self, instruction: Instruction) -> None:
        self._instructions.append(instruction)

    def build(self, image_name: str) -> None:
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
