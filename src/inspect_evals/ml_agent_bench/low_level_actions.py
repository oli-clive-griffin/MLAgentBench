"""This file contains the low level actions that are provided by the environment, mostly file system operations and code execution."""

import glob
import inspect
import os
import readline  # This is needed to make sure that the input() function works properly  # noqa: F401
import selectors
import shutil
import subprocess
import sys
import time
from functools import wraps
from io import StringIO
from typing import Any, Callable

from inspect_ai.util import SandboxEnvironment, sandbox

from .schema import Action, ActionInfo, EnvException, Step, Trace


def normalize_args_kwargs(f: Callable[..., Any], *args, **kwargs) -> dict[str, Any]:
    """This function takes a function and its arguments and returns a dictionary of the arguments, with the keys being the argument names."""
    sig = inspect.signature(f)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()  # This line is optional, it fills in any omitted arguments that have default values
    return bound.arguments


def append_to_low_level_steps(
    trace: Trace, name: str, args: dict[str, Any], observation: str
):
    """This function appends a low level step to the trace."""
    trace.low_level_steps.append(
        Step(action=Action(name, args), observation=observation, timestamp=time.time())
    )


def record_low_level_step(func: Callable[..., Any]):
    """This decorator records a low level step in the trace."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        new_kwargs = normalize_args_kwargs(func, *args, **kwargs)
        if "trace" not in new_kwargs["kwargs"]:
            print("Warning: trace not found in kwargs; not recording low level step.")
            print(func)
            return await func(*args, **kwargs)
        else:
            trace = new_kwargs["kwargs"]["trace"]
            for a in LOW_LEVEL_ACTION_INFOS:
                if a.function.__name__ == func.__name__:
                    name = a.name
                    input_args = a.usage.keys()
                    break
            new_kwargs = {k: v for k, v in new_kwargs.items() if k in input_args}
            try:
                observation = await func(*args, **kwargs)
                append_to_low_level_steps(trace, name, new_kwargs, observation)
                return observation
            except EnvironmentError as e:
                append_to_low_level_steps(trace, name, new_kwargs, e)
                raise EnvException(e)

    return wrapper


def check_files_read_only(arg_names: list[str], **kwargs):
    """This decorator checks if the file is read-only."""

    def inner(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            new_kwargs = normalize_args_kwargs(func, *args, **kwargs)
            for arg_name in arg_names:
                fname = new_kwargs[arg_name]
                if fname in new_kwargs["kwargs"]["read_only_files"]:
                    raise EnvException(
                        f"cannot write file {fname} because it is a read-only file."
                    )
            return await func(*args, **kwargs)

        return wrapper

    return inner


def check_files_in_work_dir(arg_names: list[str]):
    """This decorator checks if the file is in the work directory."""

    def inner(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            new_kwargs = normalize_args_kwargs(func, *args, **kwargs)
            work_dir = new_kwargs["work_dir"]
            for arg_name in arg_names:
                file_name = new_kwargs[arg_name]
                file_path = os.path.abspath(os.path.join(work_dir, file_name))
                work_dir_path = os.path.abspath(work_dir)
                if not file_path.startswith(work_dir_path):
                    raise EnvException(
                        f"cannot access file {file_name} because it is not in the work directory."
                    )
            return await func(*args, **kwargs)

        return wrapper

    return inner


@check_files_in_work_dir(["dir_path"])
@record_low_level_step
async def list_files(dir_path: str, work_dir: str = ".", **kwargs):
    try:
        # observation = subprocess.check_output(
        #     ["ls", "-F", os.path.join(work_dir, dir_path)]
        # ).decode("utf-8")
        result = await sandbox().exec(["ls", "-F", os.path.join(work_dir, dir_path)])
        return result.stdout
    except Exception as e:
        print("error", e)
        raise EnvException(f"Cannot list file in the {dir_path} directory")


@check_files_in_work_dir(["file_name"])
@record_low_level_step
async def read_file(file_name: str, work_dir: str = ".", **kwargs):
    try:
        result = await sandbox().exec(["cat", os.path.join(work_dir, file_name)])
        return result.stdout
    except Exception as e:
        print("error", e)
        raise EnvException(f"cannot read file {file_name}")


@check_files_in_work_dir(["file_name"])
@check_files_read_only(["file_name"])
@record_low_level_step
async def write_file(file_name: str, content: str, work_dir: str = ".", **kwargs):
    try:
        await sandbox().write_file(os.path.join(work_dir, file_name), content)
        observation = f"File {file_name} written successfully."
        return observation
    except Exception as e:
        print("error", e)
        raise EnvException(f"cannot write file {file_name}")


@check_files_in_work_dir(["file_name"])
@check_files_read_only(["file_name"])
@record_low_level_step
async def append_file(file_name: str, content: str, work_dir: str = ".", **kwargs):
    try:
        existing_content = await sandbox().read_file(os.path.join(work_dir, file_name))
        await sandbox().write_file(
            os.path.join(work_dir, file_name), existing_content + content
        )
        observation = f"File {file_name} appended successfully."
        return observation
    except Exception as e:
        print("error", e)
        raise EnvException(f"cannot append file {file_name}")


@check_files_in_work_dir(["source", "destination"])
@check_files_read_only(["destination"])
@record_low_level_step
async def copy_file(source: str, destination: str, work_dir: str = ".", **kwargs):
    try:
        src = os.path.join(work_dir, source)
        dst = os.path.join(work_dir, destination)
        await sandbox().exec(["cp", src, dst])
        observation = f"File {source} copied to {destination}"
        return observation
    except Exception as e:
        print("error", e)
        raise EnvException(
            f"File {source} copy to {destination} failed. Check whether the source and destinations are valid."
        )


@check_files_in_work_dir(["script_name"])
@record_low_level_step
async def undo_edit_script(script_name: str, work_dir: str = ".", **kwargs):
    backup_files = glob.glob(os.path.join(work_dir, "backup", f"{script_name}_*"))
    if len(backup_files) == 0:
        raise EnvException("There is no change to undo.")
    try:
        backup_files.sort()
        backup_file = backup_files[-1]

        # shutil.copyfile(backup_file, os.path.join(work_dir, script_name))

        # have to copy from outside the sandbox into the sandbox
        contents = open(backup_file).read()
        await sandbox().write_file(os.path.join(work_dir, script_name), contents)

        # delete the backup file
        os.remove(backup_file)

        new_content = await sandbox().read_file(os.path.join(work_dir, script_name))
        observation = (
            f"Content of {script_name} after undo the most recent edit:\n" + new_content
        )
        return observation
    except Exception as e:
        print("error", e)
        raise EnvException(
            f"Cannot undo the edit of file name {script_name}. Check the file name again."
        )


@check_files_in_work_dir(["script_name"])
@record_low_level_step
async def execute_script(script_name: str, work_dir: str = ".", **kwargs):
    # if not os.path.exists(os.path.join(work_dir, script_name)):
    # results = (await sandbox().exec(["ls", os.path.join(work_dir, script_name)])).stdout
    result = await sandbox().exec(["ls", os.path.join(work_dir, script_name)])
    stdout = result.stdout.strip()
    if stdout == "":
        raise EnvException(f"The file {script_name} does not exist.")
    try:
        script_path = script_name
        device = kwargs["device"]
        python = kwargs["python"]

        cmd = [python, "-u", script_path]
        env = {"CUDA_VISIBLE_DEVICES": str(device)}

        result = await sandbox().exec(cmd=cmd, cwd=work_dir, env=env)

        # TODO(oli): handle timeout
        # TODO(oli): handle stdout vs stderr better
        # TODO(oli): handle formating of observation better with "".join()?
        if result.returncode != 0:
            observation = result.stderr
        else:
            observation = result.stdout or result.stderr

        return "The script has been executed. Here is the output:\n" + observation

    except Exception as e:
        print("error", e)
        raise EnvException(
            f"Something went wrong in executing {script_path}: {e}. Please check if it is ready to be executed."
        )


@record_low_level_step
async def python_repl(command, work_dir=".", **kwargs):
    raise EnvException("Not implemented")
    """Run command and returns anything printed."""
    try:
        cwd = os.getcwd()
        import codeop

        compiler = codeop.CommandCompiler()
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        try:
            os.chdir(work_dir)
            command = compiler(command)
            exec(command, globals())
            sys.stdout = old_stdout
            output = mystdout.getvalue()
        except Exception as e:
            sys.stdout = old_stdout
            output = str(e)
        os.chdir(cwd)
        return output
    except Exception as e:
        raise EnvException(f"Something went wrong in executing {command}: {e}")


### describe the low level actions
LOW_LEVEL_ACTION_INFOS = [
    ActionInfo(
        name="List Files",
        description="Use this to navigate the file system.",
        usage={
            "dir_path": 'a valid relative path to a directory, such as "." or "folder1/folder2"'
        },
        return_value="The observation will be a list of files and folders in dir_path or current directory is dir_path is empty, or an error message if dir_path is invalid.",
        function=list_files,
        is_low_level=True,
    ),
    ActionInfo(
        name="Read File",
        description="Use this to read an existing file.",
        usage={
            "file_name": "a valid file name with relative path to current directory if needed"
        },
        return_value="The observation will be the contents of the file read.",
        function=read_file,
        is_low_level=True,
    ),
    ActionInfo(
        name="Write File",
        description="Use this to write a file. If the file already exists, it will be overwritten.",
        usage={
            "file_name": "a valid file name with relative path to current directory if needed",
            "content": "the content to be written to the file",
        },
        return_value="A success message if the file is written successfully, or an error message if the file cannot be written.",
        function=write_file,
        is_low_level=True,
    ),
    ActionInfo(
        name="Append File",
        description="Use this to append a file to a new location with a new name.",
        usage={
            "file_name": "a valid file name with relative path to current directory if needed",
            "content": "the content to be appended to the file",
        },
        return_value="A success message if the file is appended successfully, or an error message if the file cannot be appended.",
        function=append_file,
        is_low_level=True,
    ),
    ActionInfo(
        name="Copy File",
        description="Use this to copy a file to a new location with a new name.",
        usage={
            "source": "a valid file name with relative path to current directory if needed",
            "destination": "a valid file name with relative path to current directory if needed",
        },
        return_value="A success message if the file is copied successfully, or an error message if the file cannot be copied.",
        function=copy_file,
        is_low_level=True,
    ),
    ActionInfo(
        name="Undo Edit Script",
        description="Use this to undo the last edit of the python script.",
        usage={
            "script_name": "a valid python script name with relative path to current directory if needed"
        },
        return_value="The observation will be the content of the script before the last edit. If the script does not exist, the observation will be an error message.",
        function=undo_edit_script,
        is_low_level=True,
    ),
    ActionInfo(
        name="Execute Script",
        description="Use this to execute the python script. The script must already exist.",
        usage={
            "script_name": "a valid python script name with relative path to current directory if needed"
        },
        return_value="The observation will be output of the script or errors.",
        function=execute_script,
        is_low_level=True,
    ),
    ActionInfo(
        name="Python REPL",
        description="A python REPL. Use this to execute single line python commands.",
        usage={"command": "a valid python command"},
        return_value="The observation will be output of the command or errors.",
        function=python_repl,
        is_low_level=True,
    ),
    ActionInfo(
        name="Final Answer",
        description="Use this to provide the final answer to the current task.",
        usage={"final_answer": "a detailed description on the final answer"},
        return_value="The observation will be empty.",
        function=(lambda **kwargs: ""),
        is_low_level=True,
    ),
]