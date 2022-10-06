import re
import invoke
import os

class Cpu:
    __slots__ = "cpu_model", "cpu_cores", "cpu_sockets", "cpu_threads"
    def __init__(self):
        cpuinfo = Cpu.get_cpuinfo_linux()
        self.cpu_model = cpuinfo["cpu_model"]
        self.cpu_cores = cpuinfo["cpu_cores"]
        self.cpu_sockets = cpuinfo["cpu_sockets"]
        self.cpu_threads = cpuinfo["cpu_threads"]


    @staticmethod
    def get_cpuinfo_linux() -> dict:
        with open("/proc/cpuinfo", "r") as f:
            proc_cpuinfo = f.read().split("\n")
        
        re_cpu_model = re.compile(".*model name.*")
        re_cpu_model_sub = re.compile(".*model name.*:\s+")
        
        re_cpu_cores = re.compile(".*cpu cores.*")
        re_cpu_cores_sub = re.compile(".*cpu cores.*:\s")

        re_cpu_sockets = re.compile(".*physical id.*")
        re_cpu_sockets_sub = re.compile(".*physical id.*:\s")

        re_cpu_threads = re.compile(".*siblings.*")
        re_cpu_threads_sub = re.compile(".*siblings.*:\s")

        cpuinfo = {}
        for i in proc_cpuinfo:
            if re_cpu_model.match(i):
                i = re_cpu_model_sub.sub("", i)
                cpuinfo["cpu_model"] = i
            elif re_cpu_cores.match(i):
                i = re_cpu_cores_sub.sub("", i)
                cpuinfo["cpu_cores"] = i
            elif re_cpu_sockets.match(i):
                i = re_cpu_sockets_sub.sub("", i)
                cpuinfo["cpu_sockets"] = str(int(i) + 1)
            elif re_cpu_threads.match(i):
                i = re_cpu_threads_sub.sub("", i)
                cpuinfo["cpu_threads"] = i

        return cpuinfo



class Memory:
    __slots__ = "mem_used", "mem_used_h", "mem_free", "mem_free_h", "mem_total", "mem_total_h"
    def __init__(self):
        meminfo = Memory.get_meminfo_linux()
        self.mem_used = meminfo["mem_used"]
        self.mem_used_h = meminfo["mem_used_h"]
        self.mem_free = meminfo["mem_free"]
        self.mem_free_h = meminfo["mem_free_h"]
        self.mem_total = meminfo["mem_total"]
        self.mem_total_h = meminfo["mem_total_h"]


    @staticmethod
    def get_meminfo_linux():
        with open("/proc/meminfo", "r") as f:
            proc_meminfo = f.read().split("\n")
        
        re_mem_total = re.compile(r".*MemTotal.*")
        re_mem_total_sub = re.compile(r".*MemTotal.*:\s+")
        
        re_mem_free = re.compile(r".*MemAvailable.*")
        re_mem_free_sub = re.compile(r".*MemAvailable.*:\s+")
        
        meminfo = {}
        for i in proc_meminfo:
            if re_mem_total.match(i):
                i = re_mem_total_sub.sub("", i)
                i = i.strip(" kB")
                mem_total = int(i) * 1024
                mem_total_h = (float(i) / 1024) / 1024
                mem_total_h = round(mem_total_h, 2)
                meminfo["mem_total"] = mem_total
                meminfo["mem_total_h"] = mem_total_h
            elif re_mem_free.match(i):
                i = re_mem_free_sub.sub("", i)
                i = i.strip(" kB")
                mem_free = int(i) * 1024
                mem_free_h = (float(i) / 1024) / 1024
                mem_free_h = round(mem_free_h, 2)
                meminfo["mem_free"] = mem_free
                meminfo["mem_free_h"] = mem_free_h
        
        meminfo["mem_used"] = meminfo["mem_total"] - meminfo["mem_free"]
        meminfo["mem_used_h"] = round((meminfo["mem_total_h"] - meminfo["mem_free_h"]), 2)

        meminfo["mem_used_h"] = str(meminfo["mem_used_h"]) + "G"
        meminfo["mem_free_h"] = str(meminfo["mem_free_h"]) + "G"
        meminfo["mem_total_h"] = str(meminfo["mem_total_h"]) + "G"

        return meminfo



class NetworkInfo:
    __slots__ = "ip_address_list", "hostname"

    def __init__(self):
        self.ip_address_list = NetworkInfo.ip_address_linux()
        self.hostname = NetworkInfo.hostname_linux()


    @staticmethod
    def ip_address_linux() -> list:
        command = "hostname -I"
        result = invoke.run(command, hide=True)
        ip_address_list = result.stdout.split(" ")
        for i in ip_address_list:
            if i == "\n":
                ip_address_list.remove(i)

        return ip_address_list


    @staticmethod
    def hostname_linux() -> str:
        command = "hostname -f"
        result = invoke.run(command, hide=True)
        hostname = result.stdout.splitlines()[0]

        return hostname


class Users:
    def __init__(self, debug:bool = False):
        self.sudo_info = Users.get_sudo_info(debug=debug)
        self.debug = debug

        if os.getuid() != 0:
            print("You have to run this script as root!", file=sys.stderr)
            sys.exit(1)

    def get_user_info(self) -> dict:
        with open("/etc/passwd", "r") as f:
            passwd_info_list = f.read().splitlines()

        password_info = []
        for i in passwd_info_list:
            if i:
                password_info.append(i)

        ignore_list = [
            "daemon", "bin", "sys", "sync", "games", "man", "lp", "mail", "news", "uucp", "proxy", "backup", "list",
            "www-data", "systemd-coredump", "sshd", "messagebus", "nobody", "systemd-resolve", "systemd-network", "irc", "_apt",
            "systemd-timesync", "gnats", "syslog", "tss", "uuidd", "tcpdump", "landscape", "pollinate", "lxd", "Debian-snmp",
            "ntp", "usbmux", "postgres"
        ]
        ignore_list = set(ignore_list); ignore_list = list(ignore_list)

        for remove_item in ignore_list:
            for password_item in password_info:
                if remove_item == password_item.split(":")[0]:
                    password_info.remove(password_item)

        user_dict = []
        for i in password_info:
            temp_dict = {}
            user_item = i.split(":")
            temp_dict["username"] = user_item[0]
            temp_dict["full_name"] = user_item[4].strip(",,,")
            if user_item[5][-1] == "/":
                temp_dict["home_dir"] = user_item[5]
            else:
                temp_dict["home_dir"] = user_item[5] + "/"
            temp_dict["shell"] = user_item[6]

            command = "groups " + temp_dict["username"]
            result = invoke.run(command, hide=True)
            temp_dict["user_groups"] = result.stdout.split(" : ")[1].strip("\n").split(" ")

            temp_dict["sudo_access"] = False
            for group in self.sudo_info["groups"]:
                if group in temp_dict["user_groups"]:
                    temp_dict["sudo_access"] = True
            for user in self.sudo_info["users"]:
                if user == temp_dict["username"]:
                    temp_dict["sudo_access"] = True
            user_dict.append(temp_dict)

        return user_dict


    @staticmethod
    def get_sudo_info(debug:bool = False) -> dict:
        with open("/etc/sudoers", "r") as f:
            sudoers_file = f.read().splitlines()

        re_ignore_1 = re.compile(".*Defaults.*")
        re_ignore_2 = re.compile("^#")
        re_ignore_3 = re.compile("^@include")
        re_ignore_4 = re.compile("^Cmnd_Alias")
        re_match_group = re.compile("^%")

        sudo_users = []
        sudo_groups = []
        for line in sudoers_file:
            if line:
                if re_ignore_1.match(line) or re_ignore_2.match(line) or re_ignore_3.match(line) or re_ignore_4.match(line):
                    continue
                elif re_match_group.match(line):
                    line = line.split()[0].strip("%")
                    sudo_groups.append(line)
                else:
                    line = line.split()[0]
                    sudo_users.append(line)

        sudo_dict = {}
        sudo_dict["groups"] = []
        for group in sudo_groups:
            sudo_dict["groups"].append(group)
        sudo_dict["users"] = []
        for user in sudo_users:
            sudo_dict["users"].append(user)

        if debug:
            print("[DEBUG: get_sudo_info FUNC]")
            print("Users: " + str(sudo_dict["users"]))
            print("Groups: " + str(sudo_dict["groups"]))
            print("[DEBUG: get_sudo_info FUNC END]")

        return sudo_dict


def json_return() -> dict:
    output_dict = {}

    net_info = NetworkInfo()
    output_dict["hostname"] = net_info.hostname
    output_dict["ip_address_list"] = net_info.ip_address_list

    cpu_info = Cpu()
    output_dict["cpu_model"] = cpu_info.cpu_model
    output_dict["cpu_cores"] = cpu_info.cpu_cores
    output_dict["cpu_sockets"] = cpu_info.cpu_sockets
    output_dict["cpu_threads"] = cpu_info.cpu_threads
    # output_dict = {**output_dict, **cpu_info}

    mem_info = Memory()
    output_dict["ram_free"] = mem_info.mem_free
    output_dict["ram_total"] = mem_info.mem_total
    output_dict["ram_used"] = mem_info.mem_used

    return output_dict
