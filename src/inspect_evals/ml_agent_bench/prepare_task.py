"""Prepare a benchmark folder for a task."""

import fnmatch
import json
import os
import shutil
import subprocess
import sys
from inspect_ai.util import sandbox

TASKS_DIR = os.path.dirname(os.path.realpath(__file__)) + "/tasks"


def setup_log_dir(log_dir: str):
    # set up log dir
    if os.path.exists(log_dir):
        print("log_dir {} already exists".format(log_dir))
    else:
        os.makedirs(log_dir)

    if os.path.exists(os.path.join(log_dir, "tool_logs")):
        print(
            "tools_log_dir {} already exists".format(os.path.join(log_dir, "tool_logs"))
        )
        # raise ValueError("log_dir {} already exists".format(self.log_dir))
    else:
        os.makedirs(os.path.join(log_dir, "tool_logs"))

    if os.path.exists(os.path.join(log_dir, "traces")):
        print("tools_log_dir {} already exists".format(os.path.join(log_dir, "traces")))
        # raise ValueError("log_dir {} already exists".format(self.log_dir))
    else:
        os.makedirs(os.path.join(log_dir, "traces"))

    print("done setup")
    print(f"{os.getcwd()=}")
    print(f'{os.path.join(log_dir, "traces")=}')


PARENT = os.path.dirname(os.path.realpath(__file__))
TASKS_DIR = os.path.join(PARENT, "tasks")


async def initialize_task_env(python: str) -> list[str]:
    # remove the workspace folder if it exists
    # if os.path.exists(work_dir):
    #     print(f"removing {work_dir}")
    #     shutil.rmtree(work_dir)
    # else:
    #     print(f"{work_dir} does not exist, not removing")

    await run_prepare_script(python)

    # find all read only files
    all_read_only_patterns: list[str] = []
    if await sb_file_exists(os.path.join("scripts", "read_only_files.txt")):
        sandbox().exec
        readonly_patterns = (
            await sandbox().read_file(os.path.join("scripts", "read_only_files.txt"))
        ).split("\n")

        present_files = await get_all_files('.')
        for fname in present_files:
            if any(fnmatch.fnmatch(fname, pattern) for pattern in readonly_patterns):
                all_read_only_patterns.append(fname)


    # # init backup folder and remove all content if it exists
    # if os.path.exists(os.path.join(work_dir, "backup")):
    #     shutil.rmtree(os.path.join(work_dir, "backup"))

    # os.makedirs(os.path.join(work_dir, "backup"), exist_ok=True)

    return all_read_only_patterns

WALK_SCRIPT = '''
import os,json,sys
print(json.dumps(list(os.walk(sys.argv[1] if len(sys.argv)>1 else "."))))
'''

async def sandbox_walk(start_path='.'):
    res = await sandbox().exec(['python', '-'], input=WALK_SCRIPT.encode(), cwd=start_path)
    return json.loads(res.stdout)

async def get_all_files(basedir: str) -> list[str]:
    all_files = []
    for path, subdirs, local_fnames in await sandbox_walk(basedir):
        relpath = os.path.relpath(path, basedir)
        for local_fname in local_fnames:
            all_files.append(os.path.join(relpath, local_fname))
    return all_files

# TODO(oli): standardise task string names into enum or literal type
def get_research_problem(task: str) -> str:
    """task: which task to run: ["cifar10", "babylm", etc.]"""
    available_tasks = [
        dir
        for dir in os.listdir(TASKS_DIR)
        if os.path.isdir(os.path.join(TASKS_DIR, dir, "env"))
    ]

    if task not in available_tasks:
        raise ValueError(
            f"task {task} not supported in tasks, available tasks: {available_tasks}"
        )

    research_problem_file = os.path.join(
        TASKS_DIR, task, "scripts", "research_problem.txt"
    )
    with open(research_problem_file, "r") as f:
        research_problem = f.read()

    return research_problem


# def get_task_info_deprecated(task):
#     """Get research problem and benchmark folder name for task"""
#     research_problem = None
#     benchmark_folder_name = None

#     # Retrieve task from benchmarks
#     tasks = json.load(open(os.path.join(TASKS_DIR, "tasks.json")))
#     if task in tasks:
#         research_problem = tasks[task].get("research_problem", None)
#         benchmark_folder_name = tasks[task].get("benchmark_folder_name", None)

#     elif task in os.listdir(TASKS_DIR) and os.path.isdir(
#         os.path.join(TASKS_DIR, task, "env")
#     ):
#         # default benchmarks
#         benchmark_folder_name = task

#     else:
#         raise ValueError(f"task {task} not supported in tasks")

#     if research_problem is None:
#         research_problem_file = os.path.join(
#             TASKS_DIR, benchmark_folder_name, "scripts", "research_problem.txt"
#         )
#         if os.path.exists(research_problem_file):
#             # Load default research problem from file
#             with open(research_problem_file, "r") as f:
#                 research_problem = f.read()

#     return benchmark_folder_name, research_problem


async def sb_file_exists(path: str) -> bool:
    return (await sandbox().exec(["ls", "-la", path])).stdout.strip() != ""


async def run_prepare_script(python="python"):
    """Run prepare.py in the scripts folder of the benchmark if it exists and has not been run yet."""
    prepare_script_exists = await sb_file_exists(os.path.join("scripts", "prepare.py"))

    if not prepare_script_exists:
        print("prepare.py not found")
        return

    print("Running prepare.py ...")
    response = await sandbox().exec([python, "prepare.py"], cwd="scripts")

    if response.returncode != 0:
        print("prepare.py failed")
        print(response)
        sys.exit(1)

    print("finished running prepare.py")


# if __name__ == "__main__":
#     task = sys.argv[1]
#     if len(sys.argv) > 2:
#         python = sys.argv[2]
#     else:
#         python = "python"
#     benchmark_name, _ = get_task_info(task)
#     task_dir = os.path.join(tasks_dir, benchmark_name)
#     prepare_task(task_dir, python=python)
