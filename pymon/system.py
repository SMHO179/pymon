"""System information collection from /proc and /sys."""
import os
import time
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class CPUStats:
    user: int
    nice: int
    system: int
    idle: int
    iowait: int
    irq: int
    softirq: int
    steal: int
    guest: int
    guest_nice: int

    @property
    def total(self) -> int:
        return (self.user + self.nice + self.system + self.idle +
                self.iowait + self.irq + self.softirq + self.steal +
                self.guest + self.guest_nice)

    @property
    def busy(self) -> int:
        return self.total - self.idle - self.iowait


@dataclass
class MemoryInfo:
    total: int
    available: int
    used: int
    free: int
    buffers: int
    cached: int
    swap_total: int
    swap_free: int
    swap_used: int


@dataclass
class DiskInfo:
    device: str
    mountpoint: str
    fstype: str
    total: int
    used: int
    free: int
    percent: float


@dataclass
class NetworkInfo:
    interface: str
    rx_bytes: int
    tx_bytes: int
    rx_packets: int
    tx_packets: int
    rx_errors: int
    tx_errors: int


@dataclass
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: float
    mem_percent: float
    mem_rss: int
    status: str
    username: str


@dataclass
class LoadAverage:
    load1: float
    load5: float
    load15: float


@dataclass
class Uptime:
    seconds: float
    idle_seconds: float


def read_cpu_stats() -> List[CPUStats]:
    stats = []
    with open('/proc/stat', 'r') as f:
        for line in f:
            if line.startswith('cpu'):
                parts = line.split()
                if len(parts) >= 11:
                    stats.append(CPUStats(
                        user=int(parts[1]),
                        nice=int(parts[2]),
                        system=int(parts[3]),
                        idle=int(parts[4]),
                        iowait=int(parts[5]),
                        irq=int(parts[6]),
                        softirq=int(parts[7]),
                        steal=int(parts[8]),
                        guest=int(parts[9]),
                        guest_nice=int(parts[10])
                    ))
    return stats


def read_memory_info() -> MemoryInfo:
    meminfo = {}
    with open('/proc/meminfo', 'r') as f:
        for line in f:
            key, val = line.split(':', 1)
            meminfo[key.strip()] = int(val.strip().split()[0]) * 1024

    total = meminfo.get('MemTotal', 0)
    free = meminfo.get('MemFree', 0)
    buffers = meminfo.get('Buffers', 0)
    cached = meminfo.get('Cached', 0)
    available = meminfo.get('MemAvailable', free + buffers + cached)
    used = total - available
    swap_total = meminfo.get('SwapTotal', 0)
    swap_free = meminfo.get('SwapFree', 0)
    swap_used = swap_total - swap_free

    return MemoryInfo(
        total=total,
        available=available,
        used=used,
        free=free,
        buffers=buffers,
        cached=cached,
        swap_total=swap_total,
        swap_free=swap_free,
        swap_used=swap_used
    )


def read_disk_info() -> List[DiskInfo]:
    disks = []
    with open('/proc/mounts', 'r') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 3:
                device, mountpoint, fstype = parts[0], parts[1], parts[2]
                if fstype in ('proc', 'sysfs', 'devtmpfs', 'tmpfs', 'devpts', 'cgroup', 'cgroup2', 'pstore', 'bpf', 'tracefs', 'securityfs', 'configfs', 'debugfs', 'hugetlbfs', 'mqueue', 'binfmt_misc', 'rpc_pipefs', 'nsfs', 'autofs'):
                    continue
                try:
                    stat = os.statvfs(mountpoint)
                    total = stat.f_blocks * stat.f_frsize
                    free = stat.f_bfree * stat.f_frsize
                    used = total - free
                    percent = (used / total * 100) if total > 0 else 0
                    disks.append(DiskInfo(device, mountpoint, fstype, total, used, free, percent))
                except (OSError, ZeroDivisionError):
                    pass
    return disks


def read_network_info() -> List[NetworkInfo]:
    nets = []
    with open('/proc/net/dev', 'r') as f:
        for line in f:
            if ':' in line:
                parts = line.split(':')
                iface = parts[0].strip()
                if iface == 'lo':
                    continue
                vals = parts[1].split()
                if len(vals) >= 16:
                    nets.append(NetworkInfo(
                        interface=iface,
                        rx_bytes=int(vals[0]),
                        tx_bytes=int(vals[8]),
                        rx_packets=int(vals[1]),
                        tx_packets=int(vals[9]),
                        rx_errors=int(vals[2]),
                        tx_errors=int(vals[10])
                    ))
    return nets


def read_load_average() -> LoadAverage:
    with open('/proc/loadavg', 'r') as f:
        parts = f.read().split()
        return LoadAverage(
            load1=float(parts[0]),
            load5=float(parts[1]),
            load15=float(parts[2])
        )


def read_uptime() -> Uptime:
    with open('/proc/uptime', 'r') as f:
        parts = f.read().split()
        return Uptime(seconds=float(parts[0]), idle_seconds=float(parts[1]))


def read_processes() -> List[ProcessInfo]:
    processes = []
    uid_cache = {}
    for entry in os.listdir('/proc'):
        if not entry.isdigit():
            continue
        pid = int(entry)
        try:
            with open(f'/proc/{pid}/stat', 'r') as f:
                stat = f.read().split()
            with open(f'/proc/{pid}/status', 'r') as f:
                status_lines = f.read().splitlines()
        except (OSError, IndexError):
            continue

        name = stat[1].strip('()')
        state = stat[2]
        utime = int(stat[13])
        stime = int(stat[14])
        rss = int(stat[23]) * os.sysconf('SC_PAGE_SIZE')
        uid = None
        for line in status_lines:
            if line.startswith('Uid:'):
                uid = int(line.split()[1])
                break

        if uid is not None:
            if uid not in uid_cache:
                try:
                    import pwd
                    uid_cache[uid] = pwd.getpwuid(uid).pw_name
                except (ImportError, KeyError):
                    uid_cache[uid] = str(uid)
            username = uid_cache[uid]
        else:
            username = '?'

        processes.append(ProcessInfo(
            pid=pid,
            name=name[:15],
            cpu_percent=0.0,
            mem_percent=0.0,
            mem_rss=rss,
            status=state,
            username=username
        ))
    return processes


def calculate_cpu_percent(prev: List[CPUStats], curr: List[CPUStats]) -> List[float]:
    percents = []
    for p, c in zip(prev, curr):
        total_diff = c.total - p.total
        busy_diff = c.busy - p.busy
        if total_diff > 0:
            percents.append(busy_diff / total_diff * 100)
        else:
            percents.append(0.0)
    return percents


def calculate_process_cpu(prev_pid_stats: Dict[int, tuple], curr_pid_stats: Dict[int, tuple], interval: float) -> Dict[int, float]:
    result = {}
    for pid, (utime, stime) in curr_pid_stats.items():
        if pid in prev_pid_stats:
            prev_utime, prev_stime = prev_pid_stats[pid]
            total_time = (utime - prev_utime) + (stime - prev_stime)
            result[pid] = (total_time / os.sysconf('SC_CLK_TCK')) / interval * 100
        else:
            result[pid] = 0.0
    return result


def read_pid_cpu_times() -> Dict[int, tuple]:
    times = {}
    for entry in os.listdir('/proc'):
        if not entry.isdigit():
            continue
        pid = int(entry)
        try:
            with open(f'/proc/{pid}/stat', 'r') as f:
                stat = f.read().split()
            utime = int(stat[13])
            stime = int(stat[14])
            times[pid] = (utime, stime)
        except (OSError, IndexError):
            pass
    return times


def format_bytes(bytes_val: int) -> str:
    for unit in ['B', 'K', 'M', 'G', 'T']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}P"


def format_uptime(seconds: float) -> str:
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    mins = int((seconds % 3600) // 60)
    if days > 0:
        return f"{days}d {hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h {mins}m"
    else:
        return f"{mins}m"