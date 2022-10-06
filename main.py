from os.path import exists
import datetime
import json
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
    json_output:bool = typer.Option(True, help="JSON output", show_default = False),
    json_pretty:bool = typer.Option(False, help="Show pretty JSON output", show_default = False),
    ):
    """ Kernel related checks """
    if not json_output:
        kernel_check.final_human()
    elif json_output:
        kernel_check.final_json(json_pretty=json_pretty)


@app.command()
def updates(
    cache_file_location:str = typer.Option("/tmp/syschk_updates.json", help="JSON Cache file location"),
    cache_create:bool = typer.Option(False, help="Create a JSON file on disk to read the data from"),
    cache_use:bool = typer.Option(True, help="Use JSON file as a cache (don't start a fresh check)"),
    cache_timeout:int = typer.Option(900, help="Time (in minutes) to check if cache is valid (15 hours by default)"),
    json_output:bool = typer.Option(True, help="JSON output"),
    json_pretty:bool = typer.Option(False, help="Show pretty JSON output"),
    no_output:bool = typer.Option(False, help="No console output"),
    dummy_data:bool = typer.Option(False, help="Use dummy data to test/debug the app"),
    ):
    """ Updates related checks """
    if json_output:
        if cache_create:
            cache_use = False
        updates_check.final_json(cache_file_location=cache_file_location, cache_create=cache_create, cache_use=cache_use, cache_timeout=cache_timeout, json_console_output = json_output, dummy_data=dummy_data, json_pretty=json_pretty)
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
            git_result = invoke.run("git pull", hide=True)
            if git_result.ok:
                git_output = git_result.stdout.splitlines()
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
            if e.git_result.stdout:
                git_output = e.git_result.stdout.splitlines()
            elif e.git_result.stderr:
                git_output = e.git_result.stderr.splitlines()
            for i in git_output:
                if re_err_1.match(i):
                    console = Console(stderr=True)
                    console.print("[red]/opt/syschecks/ is not a Git repo folder![/]\nPlease remove the folder and install [green]SysChecks[/] again.")
                    sys.exit(1)

        try:
            pip_result = invoke.run("venv/bin/python3 -m pip install -r requirements.txt --upgrade", hide=True)
            if pip_result.ok:
                pip_output = git_result.stdout.splitlines()
                console.print("[green]Pip dependencies were upgraded!")
        except invoke.exceptions.UnexpectedExit as e:
            if e.git_result.stdout:
                git_output = e.git_result.stdout.splitlines()
                console.print("[green]Pip dependencies upgrade failed for some reason! Error: " + git_output)
            elif e.git_result.stderr:
                git_output = e.git_result.stderr.splitlines()
                console.print("[green]Pip dependencies upgrade failed for some reason! Error: " + git_output)


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
def userinfo(json_pretty:bool = typer.Option(False, help="Pretty JSON output"),
    ):
    """ Prints out user related information """
    user_info = system_info.Users().get_user_info()

    if json_pretty:
        Console().print_json(json.dumps(user_info), indent = 3, sort_keys=False)
    else:
        print(json.dumps(user_info, sort_keys=False))


@app.command()
def sysinfo(json_pretty:bool = typer.Option(False, help="Pretty JSON output"),
    ):
    
    """ Print out system related information: CPU, Network, RAM, Users, etc """

    sysinfo = system_info.json_return()
    json_output = json.dumps(sysinfo, sort_keys = False)
    if json_pretty:
        Console().print_json(json_output, indent = 3, sort_keys=False)
    else:
        print(json_output)


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

    net_info = system_info.NetworkInfo()
    ip_address_list = net_info.ip_address_list[0:3]
    hostname = net_info.hostname

    kernel_results = kernel_check.final_human(return_result=True)
    prettyos = updates_check.pretty_os()
    update_results = updates_check.final_human(cache_use=True, return_result=True)
    
    console = Console()
    console.print(Panel.fit(
        "\n" +
        "🔥 [green]System info[/] 🔥" +
        "\n[white]" +
        "[royal_blue1]💻 OS installed:[/] " + prettyos +
        "\n"
        "[royal_blue1]📡 Hostname:[/] " + hostname + "  [royal_blue1] Machine IPs:[/] "  + str(ip_address_list) +
        "\n"
        "[royal_blue1]🤖 CPU Cores:[/] " + str(cpu_cores) + " cores, " + cpu_threads + " threads  (" + cpu_model + ")" +
        "\n"
        "[royal_blue1]🧠 Memory:[/] " + str(mem_used) + "(used)/" + str(mem_total) + "(total)" +
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
        title="[green]🚀 Welcome, " + os.getenv("USER") + "![/]", style="royal_blue1", title_align="left"
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
