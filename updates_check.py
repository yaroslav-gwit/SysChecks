import re
import os
import sys
import json
import datetime
import subprocess
from os.path import exists

from rich.console import Console
from invoke import run
import invoke



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
    if os.getuid() != 0:
        print("You have to run this script as root!", file=sys.stderr)
        sys.exit(1)

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
        try:
            result = run(command, hide=True)
            all_updates_input = result.stdout.splitlines()
        except invoke.exceptions.UnexpectedExit as e:
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
    if os.getuid() != 0:
        print("You have to run this script as root!", file=sys.stderr)
        sys.exit(1)

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
    if os.getuid() != 0:
        print("You have to run this script as root!", file=sys.stderr)
        sys.exit(1)

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
    re_continue_5 = re.compile("\s:\sversionlock")
    re_continue_6 = re.compile(r"Last metadata expiration check")
    re_continue_7 = re.compile(".*\s:\ssubscription-manager.*")

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
        elif re_continue_7.match(i):
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
        elif re_continue_7.match(i):
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


def final_json(dummy_data:bool = False, cache_file_location:str = "/tmp/syschk_updates.json",
                cache_create:bool = False, cache_use:bool = False, cache_timeout:int = 900,
                json_console_output:bool = True, json_pretty = False) -> None:

    console = Console()
    with console.status("[bold royal_blue1]Working on it...[/]"):
        if cache_use:
            if exists(cache_file_location):
                with open(cache_file_location, "r") as f:
                    c_file = f.read()
                    json_input = json.loads(c_file)
                    json_input["cache_exists"] = True
                    file_creatition_time = os.path.getctime(cache_file_location)
                    file_creatition_time = datetime.datetime.fromtimestamp(file_creatition_time)
                    # json_input["cache_created_on"] = file_creatition_time.strftime("%Y-%m-%d_%H-%M-%S")
                    json_input["cache_created_on"] = file_creatition_time.strftime("%Y-%m-%d %H:%M:%S")
                    if (datetime.datetime.now() - datetime.timedelta(minutes=cache_timeout)) < file_creatition_time:
                        json_input["cache_up_to_date"] = True
                    else:
                        json_input["cache_up_to_date"] = False
            else:
                print("Cache file could not be found!", file=sys.stderr)
                sys.exit(1)
        elif not cache_use:
            os_type = detect_os()
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
        json_output_no_format = json.dumps(json_input, sort_keys=False)
        if json_pretty:
            result = json_output
        else:
            result = json_output_no_format
        
        if cache_create:
            if exists(cache_file_location):
                os.remove(cache_file_location)
            with open(cache_file_location, "w") as f:
                f.write(json_output_no_format)
            os.chmod(cache_file_location, 0o644)

        if json_console_output:
            if json_pretty:
                console.print(result)
            else:
                print(result)
        else:
            return result


def final_human(dummy_data:bool = False, cache_file_location:str = "/tmp/syschk_updates.json",
                cache_create:bool = True, cache_use:bool = False, cache_timeout:int = 900,
                return_result:bool = False, no_output:bool = False) -> None:

    console = Console()
    with console.status("[bold royal_blue1]Working on it...[/]"):
        if cache_use:
            if exists(cache_file_location):
                with open(cache_file_location, "r") as f:
                    c_file = f.read()
                    json_input = json.loads(c_file)
                    json_input["cache_exists"] = True
                    file_creatition_time = os.path.getctime(cache_file_location)
                    file_creatition_time = datetime.datetime.fromtimestamp(file_creatition_time)
                    json_input["cache_created_on"] = file_creatition_time.strftime("%Y-%m-%d %H:%M:%S")
                    if (datetime.datetime.now() - datetime.timedelta(minutes=cache_timeout)) < file_creatition_time:
                        json_input["cache_up_to_date"] = True
                    else:
                        json_input["cache_up_to_date"] = False
            else:
                if return_result:
                    return "🟠 [yellow]Update cache file doesn't exist![/]\n   Please create it by running [green]syschecks updates --cache-create[/]"
                else:
                    print("Update cache file could not be found!", file=sys.stderr)
                    sys.exit(1)
        elif cache_create:
            c_file = final_json(cache_create=cache_create, cache_file_location=cache_file_location, json_console_output=False, dummy_data=dummy_data)
            json_input = json.loads(c_file)

        system_updates = json_input["system_updates"]
        security_updates = json_input["security_updates"]
        cache_up_to_date = json_input.get("cache_up_to_date", True)

        if no_output:
            return

        if system_updates > 0 and security_updates > 0:
            if return_result:
                space = ""
                result = space + "[yellow]🟡 There is a number of system updates available: [/]" + str(system_updates) + "\n" + space + "[bright_red]🔴 Including a number of security updates: [/]" + str(security_updates)
                if not cache_up_to_date:
                    result = result + "\n\n" + space +  "[bright_red]🔴 Your cache file is out of date!"
                return result
            else:
                space = " "
                result = space + "[yellow]🟡 There is a number of system updates available: [/]" + str(system_updates) + "\n" + space + "[bright_red]🔴 Including a number of security updates: [/]" + str(security_updates)
                if not cache_up_to_date:
                    result = result + "\n\n" + space + "[bright_red]🔴 Your cache file is out of date!"
                console.print(result)

        elif system_updates > 0:
            if return_result:
                result = "[yellow]🟡 There is a number of system updates available: [/]" + str(system_updates)
                if not cache_up_to_date:
                    result = result + "\n[bright_red]🔴 Your cache file is out of date!"
                return result
            else:
                result = " [yellow]🟡 There is a number of system updates available: [/]" + str(system_updates)
                if not cache_up_to_date:
                    result = result + "\n [bright_red]🔴 Your cache file is out of date!"
                console.print(result)

        elif security_updates > 0:
            if return_result:
                result = "[bright_red]🔴 There is a number of security updates available: [/]" + str(security_updates)
                if not cache_up_to_date:
                    result = result + "\n[bright_red]🔴 Your cache file is out of date!"
                return result
            else:
                result = " [bright_red]🔴 There is a number of security updates available: [/]" + str(security_updates)
                if not cache_up_to_date:
                    result = result + "\n [bright_red]🔴 Your cache file is out of date!"
                console.print(result)

        elif system_updates == 0 and security_updates == 0:
            if return_result:
                result = "[royal_blue1]🟢 The system is up to date.[/] Well done!"
                if not cache_up_to_date:
                    result = result + "\n[bright_red]🔴 Your cache file is out of date!"
                return result
            else:
                result = " [royal_blue1]🟢 The system is up to date.[/] Well done!"
                if not cache_up_to_date:
                    result = result + "\n [bright_red]🔴 Your cache file is out of date!"
                console.print(result)



if __name__ == "__main__":
    final_human()
