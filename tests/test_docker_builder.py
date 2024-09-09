# Project
from poetry_docker_plugin import Arg, Cmd, Copy, EntryPoint, Env, Expose, From, Labels, Run, User, Volume, WorkDir
from poetry_docker_plugin.docker_builder import BuildCommand, PushCommand


def test_arg_with_no_default_value() -> None:
    arg = Arg(arg_name="foo")
    assert str(arg) == "ARG foo"


def test_arg_with_value() -> None:
    arg = Arg(arg_name="foo", default_value="bar")
    assert str(arg) == "ARG foo=bar"


def test_label_with_one_label() -> None:
    label = Labels(labels={"foo": "bar"})
    assert str(label) == "LABEL foo=bar"


def test_label_with_two_label() -> None:
    label = Labels(labels={"foo": "bar", "baz": "qux"})
    assert str(label) == "LABEL foo=bar\nLABEL baz=qux"


def test_from_with_only_base_image() -> None:
    fromm = From(base_image="python:3.8")
    assert str(fromm) == "FROM python:3.8"


def test_from_with_base_image_and_platform() -> None:
    fromm = From(base_image="python:3.8", platform="linux/amd64")
    assert str(fromm) == "FROM --platform linux/amd64 python:3.8"


def test_copy_with_one_source_and_destination() -> None:
    copy = Copy(source="foo", destination="bar")
    assert str(copy) == "COPY foo bar"


def test_env_with_one_variable() -> None:
    env = Env(env_name="foo", value="bar")
    assert str(env) == 'ENV foo="bar"'


def test_expose_with_one_port() -> None:
    expose = Expose(port=80)
    assert str(expose) == "EXPOSE 80"


def test_volume_with_path() -> None:
    volume = Volume(path="/foo")
    assert str(volume) == "VOLUME /foo"


def test_workdir_with_path() -> None:
    workdir = WorkDir(path="/foo")
    assert str(workdir) == "WORKDIR /foo"


def test_user_with_default_group() -> None:
    user = User(user="foo")
    assert str(user) == "USER foo"


def test_user_with_group() -> None:
    user = User(user="foo", group="bar")
    assert str(user) == "USER foo:bar"


def test_run_with_one_command() -> None:
    run = Run(command="echo 'Hello, World!'")
    assert str(run) == "RUN echo 'Hello, World!'"


def test_cmd_with_one_arg() -> None:
    cmd = Cmd(args=["echo"])
    assert str(cmd) == 'CMD ["echo"]'


def test_cmd_with_two_args() -> None:
    cmd = Cmd(args=["echo", "Hello, World!"])
    assert str(cmd) == 'CMD ["echo", "Hello, World!"]'


def test_entrypoint_with_one_arg() -> None:
    entrypoint = EntryPoint(args=["python"])
    assert str(entrypoint) == 'ENTRYPOINT ["python"]'


def test_entrypoint_with_two_args() -> None:
    entrypoint = EntryPoint(args=["python", "app.py"])
    assert str(entrypoint) == 'ENTRYPOINT ["python", "app.py"]'


def test_build_command_with_no_platform(dist_directory: str) -> None:
    build_cmd = BuildCommand(image_tags=["foo"], platform=[])
    assert build_cmd.command() == [
        "docker",
        "build",
        "--no-cache",
        "--tag",
        "foo",
        "--file",
        "dist/Dockerfile",
        dist_directory,
    ]


def test_build_command_with_no_platform_and_custom_dockerfile(dist_directory: str) -> None:
    build_cmd = BuildCommand(image_tags=["foo"], platform=[], dockerfile_name="Dockerfile.dev")
    assert build_cmd.command() == [
        "docker",
        "build",
        "--no-cache",
        "--tag",
        "foo",
        "--file",
        "dist/Dockerfile.dev",
        dist_directory,
    ]


def test_build_with_no_platform_and_one_arg(dist_directory: str) -> None:
    build_cmd = BuildCommand(image_tags=["foo"], platform=[], arguments={"foo": "bar"})
    assert build_cmd.command() == [
        "docker",
        "build",
        "--no-cache",
        "--build-arg=foo=bar",
        "--tag",
        "foo",
        "--file",
        "dist/Dockerfile",
        dist_directory,
    ]


def test_build_with_no_platform_and_two_args(dist_directory: str) -> None:
    build_cmd = BuildCommand(image_tags=["foo"], platform=[], arguments={"foo": "bar", "baz": "qux"})
    assert build_cmd.command() == [
        "docker",
        "build",
        "--no-cache",
        "--build-arg=foo=bar",
        "--build-arg=baz=qux",
        "--tag",
        "foo",
        "--file",
        "dist/Dockerfile",
        dist_directory,
    ]


def test_build_command_with_one_platform(dist_directory: str) -> None:
    build_cmd = BuildCommand(image_tags=["foo"], platform=["linux/amd64"])
    assert build_cmd.command() == [
        "docker",
        "buildx",
        "build",
        "--load",
        "--no-cache",
        "--platform=linux/amd64",
        "--tag",
        "foo",
        "--file",
        "dist/Dockerfile",
        dist_directory,
    ]


def test_build_with_two_platforms(dist_directory: str) -> None:
    build_cmd = BuildCommand(image_tags=["foo"], platform=["linux/amd64", "linux/arm64"])
    assert build_cmd.command() == [
        "docker",
        "buildx",
        "build",
        "--no-cache",
        "--platform=linux/amd64,linux/arm64",
        "--tag",
        "foo",
        "--file",
        "dist/Dockerfile",
        dist_directory,
    ]


def test_push_with_two_platforms(dist_directory: str) -> None:
    push_cmd = PushCommand(image_tags=["foo"], platform=["linux/amd64", "linux/arm64"])
    assert push_cmd.command() == [
        "docker",
        "buildx",
        "build",
        "--push",
        "--platform=linux/amd64,linux/arm64",
        "--tag",
        "foo",
        "--file",
        "dist/Dockerfile",
        dist_directory,
    ]
