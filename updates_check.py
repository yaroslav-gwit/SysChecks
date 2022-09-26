import re
import os
import sys
import json
import subprocess
from os.path import exists

from rich.console import Console
from invoke import run
import invoke


if os.getuid() != 0:
    print("You have to run this script as root!", file=sys.stderr)
    sys.exit(1)


def detect_os() -> str:
    os_release_input = "/etc/os-release"
    if exists(os_release_input):
        with open(os_release_input, "r") as f:
            os_release = f.read().split("\n")
    else:
        print("Could not find OS release file. Is this a linux system?", file=sys.stderr)
        sys.exit(1)

    re_os_type = re.compile(r"ID=")
    os_type = ""
    for i in os_release:
        if re_os_type.match(i):
            i = i.strip("ID=")
            i = i.strip("\"")
            os_type = i

    if os_type == "pop" or os_type == "ubuntu" or os_type == "debian":
        os_type = "deb"
    elif os_type == "centos":
        os_type = "yum"
    elif os_type == "almalinux":
        os_type = "dnf"
    else:
        os_type = "unsupported"

    return os_type


def pretty_os() -> str:
    os_release_input = "/etc/os-release"
    if exists(os_release_input):
        with open(os_release_input, "r") as f:
            os_release = f.read().split("\n")
    else:
        print("Could not find OS release file. Is this a linux system?", file=sys.stderr)
        sys.exit(1)
    re_os_type = re.compile(r"PRETTY_NAME=")
    os_type = ""
    for i in os_release:
        if re_os_type.match(i):
            i = i.strip("PRETTY_NAME=")
            i = i.strip("\"")
            os_type = i
    return os_type


def dnf_check(dummy_data:bool = False) -> dict:
    all_updates = []
    security_updates = []

    dir_path = os.path.dirname(os.path.realpath(__file__))
    dummy_data_dnf_all = dir_path + "/dummy_data/dnf_all.txt"
    dummy_data_dnf_security = dir_path + "/dummy_data/dnf_security.txt"

    if dummy_data:
        with open(dummy_data_dnf_all, "r") as f:
            all_updates_input = f.read().split("\n")
        with open(dummy_data_dnf_security, "r") as f:
            security_updates_input = f.read().split("\n")
    else:
        command = "dnf makecache"
        run(command, hide=True)

        command = "dnf --cacheonly check-update"
        result = run(command, hide=True)
        if result.ok:
            all_updates_input = result.stdout.splitlines()

        command = "dnf --cacheonly updateinfo list updates security"
        result = run(command, hide=True)
        if result.ok:
            security_updates_input = result.stdout.splitlines()

    re_replace_1 = re.compile(r"\s+")
    re_mtd = re.compile(r"Last metadata")
    re_obslt = re.compile(r"Obsoleting Packages")
    re_sec = re.compile(r".*/Sec.\s")

    for i in all_updates_input:
        i = re_replace_1.sub(" ", i)
        i = i.replace(" baseos ", "")
        i = i.replace(" epel ", "")
        i = i.replace(" appstream ", "")
        i = i.replace(" epel-source", "")
        if re_mtd.match(i):
            continue
        elif re_obslt.match(i):
            break
        elif i:
            all_updates.append(i)

    for i in security_updates_input:
        i = re_replace_1.sub(" ", i)
        i = re_sec.sub("", i)
        if re_mtd.match(i):
            continue
        elif i:
            security_updates.append(i)

    # ONLY LEAVE IN UNIQUE VALUES
    security_updates = set(security_updates)
    security_updates = list(security_updates)

    results = {}
    if len(all_updates) > 0:
        results["system_updates_available"] = True
    else:
        results["system_updates_available"] = False
    results["system_updates"] = len(all_updates)
    results["system_updates_list"] = all_updates
    
    if len(security_updates) > 0:
        results["security_updates_available"] = True
    else:
        results["security_updates_available"] = False
    results["security_updates"] = len(security_updates)
    results["security_updates_list"] = security_updates

    return results


def deb_check(dummy_data:bool = False) -> dict:
    all_updates = []
    security_updates = []

    dir_path = os.path.dirname(os.path.realpath(__file__))
    dummy_data_deb_all = dir_path + "/dummy_data/deb_all.txt"

    if dummy_data:
        with open(dummy_data_deb_all, "r") as f:
            all_updates_input = f.read().split("\n")
    else:
        command = "apt-get update"
        run(command, hide=True)

        command = "apt-get dist-upgrade -s"
        result = run(command, hide=True)
        if result.ok:
            all_updates_input = result.stdout.splitlines()

    re_all_upds = re.compile(r"Inst")
    re_sec_upds = re.compile(r".*security.*")

    for i in all_updates_input:
        if re_all_upds.match(i):
            i = i.replace("Inst ", "")
            i = i.replace(" []", "")
            all_updates.append(i)
            if re_sec_upds.match(i):
                security_updates.append(i)

    results = {}
    if len(all_updates) > 0:
        results["system_updates_available"] = True
    else:
        results["system_updates_available"] = False
    results["system_updates"] = len(all_updates)
    results["system_updates_list"] = all_updates
    
    if len(security_updates) > 0:
        results["security_updates_available"] = True
    else:
        results["security_updates_available"] = False
    results["security_updates"] = len(security_updates)
    results["security_updates_list"] = security_updates

    return results


def yum_check(dummy_data:bool = True) -> dict:
    all_updates = []
    security_updates = []

    dir_path = os.path.dirname(os.path.realpath(__file__))
    dummy_data_yum_all = dir_path + "/dummy_data/yum_all.txt"
    dummy_data_yum_security = dir_path + "/dummy_data/yum_security.txt"

    if dummy_data:
        with open(dummy_data_yum_all, "r") as f:
            all_updates_input = f.read().split("\n")
        with open(dummy_data_yum_security, "r") as f:
            security_updates_input = f.read().split("\n")
    else:
        command = "yum makecache fast"
        run(command, hide=True)

        command = "yum --cacheonly check-update"
        try:
            result = run(command, hide=True)
            # if result.return_code = 0:
            if result.ok:
                all_updates_input = result.stdout.splitlines()
        except invoke.exceptions.UnexpectedExit as e:
            if e.result.stdout:
                all_updates_input = e.result.stdout.splitlines()
            elif e.result.stderr:
                all_updates_input = e.result.stderr.splitlines()

        command = "yum --cacheonly updateinfo list updates security"
        result = run(command, hide=True)
        if result.ok:
            security_updates_input = result.stdout.splitlines()
        if not result.ok:
            all_updates_input = result.stderr.splitlines()

    re_w_repl = re.compile(r"\s+")
    re_sec = re.compile(r".*/Sec.\s")
    re_obslt = re.compile(r"Obsoleting Packages")

    re_continue_1 = re.compile(r"Loaded plugins: ")
    re_continue_2 = re.compile(r"updateinfo list done")
    re_continue_3 = re.compile(r": manager,")
    re_continue_4 = re.compile(r"This system is not registered")
    re_continue_5 = re.compile(r"versionlock")
    re_continue_6 = re.compile(r"Last metadata expiration check")

    for i in all_updates_input:
        i = re_w_repl.sub(" ", i)
        i = i.replace(" baseos ", "")
        i = i.replace(" epel ", "")
        i = i.replace(" appstream ", "")
        i = i.replace(" epel-source", "")

        if re_continue_1.match(i) or re_continue_2.match(i) or re_continue_3.match(i):
            continue
        elif re_continue_4.match(i) or re_continue_5.match(i) or re_continue_6.match(i):
            continue
        elif re_obslt.match(i):
            break
        elif i:
            all_updates.append(i)

    for i in security_updates_input:
        i = re_w_repl.sub(" ", i)
        i = re_sec.sub("", i)
        
        if re_continue_1.match(i) or re_continue_2.match(i) or re_continue_3.match(i):
            continue
        elif re_continue_4.match(i) or re_continue_5.match(i) or re_continue_6.match(i):
            continue
        elif re_obslt.match(i):
            break
        elif i:
            security_updates.append(i)

    # ONLY LEAVE IN UNIQUE VALUES
    security_updates = set(security_updates)
    security_updates = list(security_updates)

    results = {}
    if len(all_updates) > 0:
        results["system_updates_available"] = True
    else:
        results["system_updates_available"] = False
    results["system_updates"] = len(all_updates)
    results["system_updates_list"] = all_updates
    
    if len(security_updates) > 0:
        results["security_updates_available"] = True
    else:
        results["security_updates_available"] = False
    results["security_updates"] = len(security_updates)
    results["security_updates_list"] = security_updates

    return results


def final_json(dummy_data:bool = False, save_file:bool = False, file_location:str = "/tmp/syschk_updates.json") -> None:
    os_type = detect_os()

    console = Console()
    with console.status("[bold blue]Working on it...[/]"):
        if os_type == "deb":
            json_input = deb_check(dummy_data=dummy_data)
        elif os_type == "dnf":
            json_input = dnf_check(dummy_data=dummy_data)
        elif os_type == "yum":
            json_input = yum_check(dummy_data=dummy_data)
        else:
            print(" ⛔ Your OS is not supported!", file=sys.stderr)
            sys.exit(1)

        json_output = json.dumps(json_input, indent=3, sort_keys=False)
        if save_file:
            if exists(file_location):
                os.remove(file_location)
            result = json_output
            with open(file_location, "w") as f:
                f.write(result)
        else:
            console.print(json_output)


def final_human(dummy_data:bool = False, save_file:bool = False, file_location:str = "/tmp/syschk_updates.human") -> None:
    os_type = detect_os()

    console = Console()
    with console.status("[bold blue]Working on it...[/]"):
        if os_type == "deb":
            json_input = deb_check(dummy_data=dummy_data)
        elif os_type == "dnf":
            json_input = dnf_check(dummy_data=dummy_data)
        elif os_type == "yum":
            json_input = yum_check(dummy_data=dummy_data)
        else:
            print(" ⛔ Your OS is not supported!", file=sys.stderr)
            sys.exit(1)

        system_updates = json_input["system_updates"]
        security_updates = json_input["security_updates"]

        if save_file:
            if exists(file_location):
                os.remove(file_location)

        if system_updates > 0 and security_updates > 0:
            if save_file:
                space = ""
                result = space + "[yellow]🟡 There is a number of system updates available: [/]" + str(system_updates) + "\n" + space + "[red]🔴 Including a number of security updates: [/]" + str(security_updates)
                with open(file_location, "w") as f:
                    f.write(result)
            else:
                space = " "
                result = space + "[yellow]🟡 There is a number of system updates available: [/]" + str(system_updates) + "\n" + space + "[red]🔴 Including a number of security updates: [/]" + str(security_updates)
                console.print(result)

        elif system_updates > 0:
            result = "[yellow]🟡 There is a number of system updates available: [/]" + str(system_updates)
            if save_file:
                with open(file_location, "w") as f:
                    f.write(result)
            else:
                console.print(" " + result)

        elif security_updates > 0:
            result = "[red]🔴 There is a number of security updates available: [/]" + str(security_updates)
            if save_file:
                with open(file_location, "w") as f:
                    f.write(result)
            else:
                console.print(" " + result)

        elif system_updates == 0 and security_updates == 0:
            result = "[blue]🟢 The system is up to date.[/] Well done!"
            if save_file:
                with open(file_location, "w") as f:
                    f.write(result)
            else:
                console.print(" " + result)


if __name__ == "__main__":
    final_human()
