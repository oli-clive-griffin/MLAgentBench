"""Prepare a benchmark folder for a task."""

import fnmatch
import json
import os
import shutil
import subprocess
import sys

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


def initialize_task_env(work_dir: str, task_folder_name: str, python: str) -> list[str]:
    # remove the workspace folder if it exists
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)

    benchmark_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "benchmarks",
        task_folder_name,
    )

    # prepare if there is a prepare.py and it has not been prepared
    prepare_task(benchmark_dir, python)

    # copy the benchmarks folder to work_dir
    if os.path.exists(os.path.join(benchmark_dir, "env")):
        shutil.copytree(os.path.join(benchmark_dir, "env"), work_dir, symlinks=True)

    # find all read only files
    read_only_files: list[str] = []
    if os.path.exists(os.path.join(benchmark_dir, "scripts", "read_only_files.txt")):
        ignore_files = (
            open(os.path.join(benchmark_dir, "scripts", "read_only_files.txt"), "r")
            .read()
            .split("\n")
        )
        for path, subdirs, files in os.walk(os.path.join(work_dir)):
            relpath = os.path.relpath(path, work_dir)
            # filter out the files that are read only
            filenames = [os.path.join(relpath, filename) for filename in files]
            for ignore in ignore_files:
                ignore_filenames = [n for n in filenames if fnmatch.fnmatch(n, ignore)]
                read_only_files.extend(ignore_filenames)

    # init backup folder and remove all content if it exists
    if os.path.exists(os.path.join(work_dir, "backup")):
        shutil.rmtree(os.path.join(work_dir, "backup"))
    os.mkdir(os.path.join(work_dir, "backup"))

    return read_only_files


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
            f"task {task} not supported in benchmarks, available tasks: {available_tasks}"
        )

    with open(os.path.join(TASKS_DIR, task, "research_problem.txt"), "r") as f:
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
#         raise ValueError(f"task {task} not supported in benchmarks")

#     if research_problem is None:
#         research_problem_file = os.path.join(
#             TASKS_DIR, benchmark_folder_name, "scripts", "research_problem.txt"
#         )
#         if os.path.exists(research_problem_file):
#             # Load default research problem from file
#             with open(research_problem_file, "r") as f:
#                 research_problem = f.read()

#     return benchmark_folder_name, research_problem


def prepare_task(benchmark_dir, python="python"):
    """Run prepare.py in the scripts folder of the benchmark if it exists and has not been run yet."""
    if os.path.exists(
        os.path.join(benchmark_dir, "scripts", "prepare.py")
    ) and not os.path.exists(os.path.join(benchmark_dir, "scripts", "prepared")):
        print("Running prepare.py ...")
        p = subprocess.run(
            [python, "prepare.py"], cwd=os.path.join(benchmark_dir, "scripts")
        )
        if p.returncode != 0:
            print("prepare.py failed")
            sys.exit(1)
        else:
            with open(os.path.join(benchmark_dir, "scripts", "prepared"), "w") as f:
                f.write("success")
        print("prepare.py finished")
    else:
        print("prepare.py not found or already prepared")


# if __name__ == "__main__":
#     task = sys.argv[1]
#     if len(sys.argv) > 2:
#         python = sys.argv[2]
#     else:
#         python = "python"
#     benchmark_name, _ = get_task_info(task)
#     benchmark_dir = os.path.join(tasks_dir, benchmark_name)
#     prepare_task(benchmark_dir, python=python)
