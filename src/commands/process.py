"""
Click command to kill pythonw.exe Windows Python background process
"""
import click
import psutil


PROCESS_NAME = "pythonw.exe"


@click.command()
def kill_pythonw_process():
    """
    Click command to kill pythonw.exe Windows Python background process
    """
    for process in psutil.process_iter():
        if process.name() == PROCESS_NAME:
            process.kill()
            print(f"Killed {PROCESS_NAME} process")
            break
    else:
        print(f"{PROCESS_NAME} process not found")

