"""Terminal UI for pymon."""
import curses
import time
import argparse
from typing import List, Optional
from .system import (
    read_cpu_stats, read_memory_info, read_disk_info,
    read_network_info, read_load_average, read_uptime,
    read_processes, calculate_cpu_percent, calculate_process_cpu,
    read_pid_cpu_times, format_bytes, format_uptime,
    CPUStats, MemoryInfo, DiskInfo, NetworkInfo,
    ProcessInfo, LoadAverage, Uptime
)


class PymonTUI:
    def __init__(self, interval: float = 1.0, sort_by: str = 'cpu'):
        self.interval = interval
        self.sort_by = sort_by
        self.prev_cpu = read_cpu_stats()
        self.prev_pid_cpu = read_pid_cpu_times()
        self.running = True
        self.stdscr = None

    def run(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        curses.use_default_colors()
        self.stdscr.nodelay(True)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_RED, -1)
        curses.init_pair(4, curses.COLOR_CYAN, -1)

        last_refresh = 0
        while self.running:
            now = time.time()
            if now - last_refresh >= self.interval:
                self.draw()
                last_refresh = now

            self.handle_input()
            time.sleep(0.05)

    def handle_input(self):
        try:
            key = self.stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                self.running = False
            elif key == ord('r') or key == ord('R'):
                self.draw()
            elif key == ord('c') or key == ord('C'):
                self.sort_by = 'cpu'
            elif key == ord('m') or key == ord('M'):
                self.sort_by = 'mem'
        except curses.error:
            pass

    def draw(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        cpu_stats = read_cpu_stats()
        cpu_percents = calculate_cpu_percent(self.prev_cpu, cpu_stats)
        self.prev_cpu = cpu_stats

        mem = read_memory_info()
        disks = read_disk_info()
        nets = read_network_info()
        load = read_load_average()
        uptime = read_uptime()

        curr_pid_cpu = read_pid_cpu_times()
        proc_cpu = calculate_process_cpu(self.prev_pid_cpu, curr_pid_cpu, self.interval)
        self.prev_pid_cpu = curr_pid_cpu

        procs = read_processes()
        for p in procs:
            p.cpu_percent = proc_cpu.get(p.pid, 0.0)
            p.mem_percent = (p.mem_rss / mem.total * 100) if mem.total > 0 else 0.0

        if self.sort_by == 'cpu':
            procs.sort(key=lambda x: x.cpu_percent, reverse=True)
        else:
            procs.sort(key=lambda x: x.mem_percent, reverse=True)

        row = 0
        self.draw_header(row, w, cpu_percents, mem, load, uptime)
        row += 4

        self.draw_disks(row, w, disks)
        row += len(disks) + 2

        self.draw_network(row, w, nets)
        row += 3

        self.draw_processes(row, h, w, procs)

        self.stdscr.refresh()

    def draw_header(self, row: int, w: int, cpu_percents: List[float],
                    mem: MemoryInfo, load: LoadAverage, uptime: Uptime):
        cpu_str = " ".join(f"{c:5.1f}%" for c in cpu_percents[:8])
        self.stdscr.addstr(row, 0, f"CPU: [{cpu_str}]", curses.color_pair(4))

        mem_used_pct = (mem.used / mem.total * 100) if mem.total > 0 else 0
        swap_used_pct = (mem.swap_used / mem.swap_total * 100) if mem.swap_total > 0 else 0
        self.stdscr.addstr(row + 1, 0,
            f"RAM: {format_bytes(mem.used)}/{format_bytes(mem.total)} ({mem_used_pct:.1f}%)  "
            f"Swap: {format_bytes(mem.swap_used)}/{format_bytes(mem.swap_total)} ({swap_used_pct:.1f}%)")

        self.stdscr.addstr(row + 2, 0,
            f"Load: {load.load1:.2f} {load.load5:.2f} {load.load15:.2f}  "
            f"Uptime: {format_uptime(uptime.seconds)}")

        self.stdscr.addstr(row + 3, 0,
            f"Sort: {self.sort_by.upper()}  [q]uit  [r]efresh  [c]pu sort  [m]em sort  Interval: {self.interval}s")

    def draw_disks(self, row: int, w: int, disks: List[DiskInfo]):
        self.stdscr.addstr(row, 0, "DISK:", curses.color_pair(4))
        row += 1
        for d in disks[:5]:
            bar_len = min(int(d.percent / 5), 20)
            bar = '█' * bar_len + '░' * (20 - bar_len)
            color = 1 if d.percent < 70 else (2 if d.percent < 90 else 3)
            self.stdscr.addstr(row, 0, f"  {d.mountpoint[:20]:20} {bar} {d.percent:5.1f}% {format_bytes(d.used)}/{format_bytes(d.total)}", curses.color_pair(color))
            row += 1

    def draw_network(self, row: int, w: int, nets: List[NetworkInfo]):
        self.stdscr.addstr(row, 0, "NETWORK:", curses.color_pair(4))
        row += 1
        for n in nets[:4]:
            self.stdscr.addstr(row, 0,
                f"  {n.interface:8} RX: {format_bytes(n.rx_bytes):>8}  TX: {format_bytes(n.tx_bytes):>8}")
            row += 1

    def draw_processes(self, row: int, h: int, w: int, procs: List[ProcessInfo]):
        self.stdscr.addstr(row, 0, "PROCESSES:", curses.color_pair(4))
        row += 1
        header = f"  {'PID':>6} {'USER':<10} {'CPU%':>6} {'MEM%':>6} {'RSS':>8} {'STAT':<4} {'NAME'}"
        self.stdscr.addstr(row, 0, header[:w-1])
        row += 1

        max_procs = h - row - 1
        for proc in procs[:max_procs]:
            line = f"  {proc.pid:>6} {proc.username:<10} {proc.cpu_percent:>6.1f} {proc.mem_percent:>6.1f} {format_bytes(proc.mem_rss):>8} {proc.status:<4} {proc.name}"
            try:
                self.stdscr.addstr(row, 0, line[:w-1])
            except curses.error:
                pass
            row += 1


def parse_args():
    parser = argparse.ArgumentParser(description='pymon - Lightweight Linux system monitor')
    parser.add_argument('-i', '--interval', type=float, default=1.0,
                        help='Refresh interval in seconds (default: 1.0)')
    parser.add_argument('-s', '--sort', choices=['cpu', 'mem'], default='cpu',
                        help='Initial sort column (default: cpu)')
    return parser.parse_args()


def main():
    args = parse_args()
    tui = PymonTUI(interval=args.interval, sort_by=args.sort)
    curses.wrapper(tui.run)


if __name__ == '__main__':
    main()