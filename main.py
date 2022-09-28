from os.path import exists
import re

import typer
import os
import sys
from rich.panel import Panel
from rich.console import Console
import invoke

import kernel_check
import updates_check
import system_info


app = typer.Typer()
@app.command()
def kern(
    json:bool = typer.Option(False, help="Show JSON output", show_default = False),
    ):
    """ Kernel related checks """
    if not json:
        kernel_check.final_human()
    elif json:
        kernel_check.final_json()


@app.command()
def updates(
    file_location:str = typer.Argument("/tmp/syschk_updates.human", help="Output file location"),
    json_file_location:str = typer.Argument("/tmp/syschk_updates.json", help="JSON output file location"),
    save_file:bool = typer.Option(False, help="Save human output as a file"),
    json:bool = typer.Option(False, help="Show JSON output"),
    dummy_data:bool = typer.Option(False, help="Use dummy data to test/debug the app"),
    ):
    """ Updates related checks """
    if not json:
        updates_check.final_human(dummy_data=dummy_data, save_file=save_file, file_location=file_location)
    if json:
        updates_check.final_json(dummy_data=dummy_data, save_file=save_file, file_location=json_file_location)


@app.command()
def self_update():
    """ Pull the latest updates from our Git repo """

    console = Console()
    os.chdir("/opt/syschecks/")

    try:
        result = invoke.run("git pull", hide=True)
        if result.ok:
            git_output = result.stdout.splitlines()
            console.print("[green]Syschecks has been updated succesfully!")
    except invoke.exceptions.UnexpectedExit as e:
        re_err_1 = re.compile(".*not a git repository.*")
        if e.result.stdout:
            git_output = e.result.stdout.splitlines()
        elif e.result.stderr:
            git_output = e.result.stderr.splitlines()
        for i in git_output:
            if re_err_1.match(i):
                console = Console(stderr=True)
                console.print("[red]/opt/syschecks/ is not a Git repo folder![/]\nPlease remove the folder and install [green]SysChecks[/] again.")
                sys.exit(1)


@app.command()
def login_view():
    """ Show a pretty login banner """

    cpu_info_dict = system_info.get_cpuinfo_linux()
    cpu_model = cpu_info_dict["cpu_model"]
    cpu_cores = cpu_info_dict["cpu_cores"]

    mem_info_dict = system_info.get_meminfo_linux()
    mem_total = mem_info_dict["mem_total_h"]
    mem_free = mem_info_dict["mem_free_h"]
    mem_used = mem_info_dict["mem_used_h"]

    kernel_results = kernel_check.final_human(return_result=True)
    prettyos = updates_check.pretty_os()
    updates_file = "/tmp/syschk_updates.human"
    if exists(updates_file):
        with open(updates_file, "r") as f:
            update_results = f.read()
    else:
        update_results = "🟠 Still loading..."

    console = Console()
    console.print(Panel.fit(
        "\n" +
        "🔥 [green]System info[/] 🔥" +
        "\n[white]" +
        "[blue]💻 OS installed: [/]" + prettyos +
        "\n"
        "[blue]🤖 CPU Cores: [/]" + str(cpu_cores) + " (" + cpu_model + ")" +
        "\n"
        "[blue]🧠 Memory: [/]" + str(mem_used) + "(used)/" + str(mem_total) + "(total)" +
        "\n[/]" +
        "\n" +
        "🔥 [green]Kernel reboot status[/] 🔥" +
        "\n[white]" +
        kernel_results +
        "\n" +
        "\n" +
        "🔥 [green]Update status[/] 🔥" +
        "\n" +
        update_results +
        "[/]\n",
        title="[green]🚀 Welcome, " + os.getenv("USER") + "![/]", style="blue", title_align="left"
    ))


@app.callback(invoke_without_command=True)
def main(ctx:typer.Context):
    """ A collection of scripts to run certain system checks """
    if ctx.invoked_subcommand is None:
        login_view()


if __name__ == "__main__":
    app()
