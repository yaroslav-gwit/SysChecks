import re

class Cpu():
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



class Memory():
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
