from os.path import exists
import datetime
import sys
import os
import re

from rich.console import Console
from rich.panel import Panel
import invoke
import typer

import updates_check
import kernel_check
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
    cache_file_location:str = typer.Option("/tmp/syschk_updates.json", help="JSON Cache file location"),
    cache_create:bool = typer.Option(False, help="Create a JSON file on disk to read the data from"),
    cache_use:bool = typer.Option(True, help="Use JSON file as a cache (don't start a fresh check)"),
    cache_timeout:int = typer.Option(900, help="Time (in minutes) to check if cache is valid (15 hours by default)"),
    json_output:bool = typer.Option(False, help="Show JSON output"),
    no_output:bool = typer.Option(False, help="No console output"),
    dummy_data:bool = typer.Option(False, help="Use dummy data to test/debug the app"),
    ):
    """ Updates related checks """
    if json_output:
        if cache_create:
            cache_use = False
        updates_check.final_json(cache_file_location=cache_file_location, cache_create=cache_create, cache_use=cache_use, cache_timeout=cache_timeout, json_console_output = json_output, dummy_data=dummy_data)
    else:
        if cache_create:
            cache_use = False
        updates_check.final_human(cache_file_location=cache_file_location, cache_create=cache_create, cache_use=cache_use, cache_timeout=cache_timeout, dummy_data=dummy_data, no_output=no_output)


@app.command()
def self_update():
    """ Pull the latest updates from our Git repo """

    console = Console()
    # Uncomment for PROD env
    os.chdir("/opt/syschecks/")
    # Uncomment for DEV env
    # os.chdir("/root/Git/SysChecks")

    with console.status("[bold blue]Working on it...[/]"):
        try:
            result = invoke.run("git pull", hide=True)
            if result.ok:
                git_output = result.stdout.splitlines()
                re_out_1 = re.compile(".*Already up to date.*")
                re_out_2 = re.compile(".*Already up-to-date.*")
                for index, value in enumerate(git_output):
                    if re_out_1.match(value):
                        console.print("[green]SysChecks is already up-to-date!")
                    elif re_out_2.match(value):
                        console.print("[green]SysChecks is already up-to-date!")
                    elif not re_out_1.match(value) and (index + 1) == len(git_output):
                        console.print("[green]SysChecks was updated succesfully!")
                        cron_init()

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
def cron_init():
    """ Initialize the required cron jobs """
    file_location = "/etc/cron.d/syschecks"
    if exists(file_location):
        os.remove(file_location)

    cron_jobs_list = []
    result = invoke.run("which bash", hide=True)
    if result.ok:
        bash_shell_location = result.stdout.splitlines()[0]

    cron_shell = "SHELL=" + bash_shell_location
    cron_jobs_list.append(cron_shell)
    cron_jobs_list.append("PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin")

    cron_job_generation_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    cron_jobs_list.append("\n# THIS JOB FILE WAS GENERATED ON: " + cron_job_generation_date)
    cron_jobs_list.append("MAILTO=\"\"")

    cron_job_1 = "@reboot root sleep 10 && syschecks updates --cache-create --no-output"
    cron_job_2 = "7 */12 * * * root syschecks updates --cache-create --no-output"
    cron_job_3 = "17 9 */3 * * root syschecks self-update"
    
    cron_jobs_list.append(cron_job_1)
    cron_jobs_list.append(cron_job_2)
    cron_jobs_list.append(cron_job_3)

    final_result = "\n".join(cron_jobs_list) + "\n"
    with open(file_location, "w") as f:
        f.write(final_result)

    if exists(file_location):
        Console().print("[green]The new SysChecks cron.d file was created at: [/]" + file_location)
    else:
        Console().print("[red]Could not create a new cron.d file at: [/]" + file_location)


@app.command()
def login_view():
    """ Show a pretty login banner """

    cpuinfo = system_info.Cpu()
    cpu_model = cpuinfo.cpu_model
    cpu_cores = cpuinfo.cpu_cores
    cpu_threads = cpuinfo.cpu_threads

    meminfo = system_info.Memory()
    mem_total = meminfo.mem_total_h
    mem_free = meminfo.mem_free_h
    mem_used = meminfo.mem_used_h

    ip_address_list = system_info.NetworkInfo(get_ip=True).ip_address_list
    hostname = system_info.NetworkInfo(get_hostname=True).hostname

    kernel_results = kernel_check.final_human(return_result=True)
    prettyos = updates_check.pretty_os()
    update_results = updates_check.final_human(cache_use=True, return_result=True)
    
    console = Console()
    console.print(Panel.fit(
        "\n" +
        "🔥 [green]System info[/] 🔥" +
        "\n[white]" +
        "[blue]💻 OS installed:[/] " + prettyos +
        "\n"
        "[blue]📡 Hostname:[/] " + hostname + "  [blue] Machine IPs:[/] "  + str(ip_address_list) +
        "\n"
        "[blue]🤖 CPU Cores:[/] " + str(cpu_cores) + " cores, " + cpu_threads + " threads  (" + cpu_model + ")" +
        "\n"
        "[blue]🧠 Memory:[/] " + str(mem_used) + "(used)/" + str(mem_total) + "(total)" +
        "\n" +
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


@app.command()
def version():
    """ Show SysChecks version and exit """
    Console().print("2022.9.28 (main Git branch)")


@app.callback(invoke_without_command=True)
def main(ctx:typer.Context):
    """ A collection of scripts to run certain system checks """
    if ctx.invoked_subcommand is None:
        login_view()


if __name__ == "__main__":
    app()
