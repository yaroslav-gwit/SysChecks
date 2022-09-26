from os.path import exists
import multiprocessing
import re

import typer
import os
from rich.panel import Panel
from rich.console import Console

import kernel_check
import updates_check


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
def login_view():
    """ Show a pretty login banner """

    # Get CPU model on Linux
    with open("/proc/cpuinfo", "r") as f:
        cpu_model = f.read().split("\n")
    re_cpu_model = re.compile(r".*model name.*")
    re_cpu_model_sub = re.compile(r".*model name.*:\s")
    for i in cpu_model:
        if re_cpu_model.match(i):
            i = re_cpu_model_sub.sub("", i)
            cpu_model = i
            break

    # Get memory info
    with open("/proc/meminfo", "r") as f:
        mem_info = f.read().split("\n")
    re_mem_total = re.compile(r".*MemTotal.*")
    re_mem_total_sub = re.compile(r".*MemTotal.*:\s+")
    re_mem_free = re.compile(r".*MemAvailable.*")
    re_mem_free_sub = re.compile(r".*MemAvailable.*:\s+")
    mem_total = ""
    mem_free = ""
    for i in mem_info:
        if re_mem_total.match(i):
            i = re_mem_total_sub.sub("", i)
            i = i.strip(" kB")
            i = (float(i) / 1024) / 1024
            i = round(i, 2)
            mem_total = i
        elif re_mem_free.match(i):
            i = re_mem_free_sub.sub("", i)
            i = i.strip(" kB")
            i = (float(i) / 1024) / 1024
            i = round(i, 2)
            mem_free = i
    mem_used = round((mem_total - mem_free), 2)

    number_of_cpus = multiprocessing.cpu_count()
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
        "[blue]🤖 CPU Cores: [/]" + str(number_of_cpus) + " (" + cpu_model + ")" +
        "\n"
        "[blue]🧠 Memory: [/]" + str(mem_used) + "G(used)/" + str(mem_total) + "G(total)" +
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
