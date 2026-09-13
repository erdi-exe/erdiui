# ErdiUI | https://github.com/erdi-exe
# Hacker-style control panel for Termux.
# Run: python erdi_ui.py
# Very Broken, wait till next update

import json
import os
import platform
import shutil
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path


GITHUB = "https://github.com/erdi-exe"
GREEN = "92"
DIM = "90"
CYAN = "96"
RED = "91"
YELLOW = "93"
BOLD_GREEN = "92;1"
BOLD_CYAN = "96;1"
MAGENTA = "95"


def paint(text, code=GREEN):
    return f"\033[{code}m{text}\033[0m"


def run(command, timeout=8):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (result.stdout or result.stderr or "").strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read().strip()
    except OSError:
        return ""


def getprop(name):
    return run(["getprop", name])


def clear():
    os.system("clear")


def line(char="═", width=46):
    return char * width


def box(title, rows, width=46):
    print(paint("╔" + line("═", width - 2) + "╗", CYAN))
    print(paint("║", CYAN) + paint(title.center(width - 2), BOLD_GREEN) + paint("║", CYAN))
    print(paint("╠" + line("═", width - 2) + "╣", CYAN))
    for row in rows:
        text = row[: width - 4]
        pad = " " * (width - 4 - len(text))
        print(paint("║ ", CYAN) + paint(text, GREEN) + pad + paint(" ║", CYAN))
    print(paint("╚" + line("═", width - 2) + "╝", CYAN))


def github_box(flash=False):
    """Same fancy framed GitHub link as Phone Info."""
    label = " github.com/erdi-exe "
    link = " " + GITHUB + " "
    width = max(len(label), len(link))
    label = label.center(width)
    link = link.center(width)
    top = "╔" + "═" * width + "╗"
    mid = "╠" + "═" * width + "╣"
    bot = "╚" + "═" * width + "╝"
    empty = "║" + " " * width + "║"

    try:
        cols = os.get_terminal_size().columns
    except OSError:
        cols = 40
    pad = " " * max(0, (cols - len(top)) // 2)

    lines_on = [
        paint(pad + top, CYAN),
        paint(pad + "║", CYAN) + paint(label, "95;1") + paint("║", CYAN),
        paint(pad + mid, CYAN),
        paint(pad + "║", CYAN) + paint(link, GREEN) + paint("║", CYAN),
        paint(pad + bot, CYAN),
    ]
    lines_off = [
        paint(pad + top, DIM),
        paint(pad + empty, DIM),
        paint(pad + mid, DIM),
        paint(pad + empty, DIM),
        paint(pad + bot, DIM),
    ]

    if flash:
        for tick in range(8):
            shown = lines_on if tick % 2 == 0 else lines_off
            print("\n".join(shown))
            time.sleep(0.18)
            print(f"\033[{len(shown)}A", end="")
        print("\n".join(lines_on))
    else:
        print("\n".join(lines_on))


def status_bar():
    model = getprop("ro.product.model") or platform.node() or "DEVICE"
    android = getprop("ro.build.version.release") or "?"
    now = datetime.now().strftime("%H:%M:%S")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("1.1.1.1", 80))
        ip = sock.getsockname()[0]
        sock.close()
        link = "LINK UP"
        link_color = GREEN
    except OSError:
        ip = "OFFLINE"
        link = "LINK DOWN"
        link_color = RED

    battery = "?"
    raw = run(["termux-battery-status"], timeout=3)
    if raw:
        try:
            battery = str(json.loads(raw).get("percentage", "?")) + "%"
        except json.JSONDecodeError:
            pass
    else:
        supply = "/sys/class/power_supply"
        if os.path.isdir(supply):
            for name in os.listdir(supply):
                cap = read_file(f"{supply}/{name}/capacity")
                if cap.isdigit():
                    battery = cap + "%"
                    break

    print(paint("┌" + line("─", 44) + "┐", DIM))
    print(
        paint("│ ", DIM)
        + paint("ERDIUI", BOLD_CYAN)
        + paint("  //  ", DIM)
        + paint(link, link_color)
        + paint(f"  {now}", DIM)
        + paint(" │", DIM)
    )
    print(
        paint("│ ", DIM)
        + paint(f"{model[:18]}", GREEN)
        + paint("  A", DIM)
        + paint(android, GREEN)
        + paint(f"  BAT {battery}", YELLOW)
        + paint(f"  {ip}", CYAN)
        + paint(" │", DIM)
    )
    print(paint("└" + line("─", 44) + "┘", DIM))


def bar(percent, width=28):
    percent = max(0, min(100, int(percent)))
    filled = int(width * percent / 100)
    return "[" + "#" * filled + "-" * (width - filled) + f"] {percent}%"


def gb(num_bytes):
    return round(num_bytes / (1024 ** 3), 2)


def mem_stats():
    values = {}
    for line_text in read_file("/proc/meminfo").splitlines():
        if ":" not in line_text:
            continue
        key, value = line_text.split(":", 1)
        number = value.strip().split()[0]
        if number.isdigit():
            values[key] = int(number)
    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", values.get("MemFree", 0))
    used = max(total - available, 0)
    percent = round(used * 100 / total) if total else 0
    return total, used, available, percent


def cpu_name():
    text = read_file("/proc/cpuinfo")
    for key in ("Hardware", "model name", "Processor"):
        for line_text in text.splitlines():
            if ":" not in line_text:
                continue
            left, right = line_text.split(":", 1)
            if left.strip().lower() == key.lower() and right.strip():
                return right.strip()
    return getprop("ro.board.platform") or platform.machine() or "unknown"


def cpu_usage():
    def sample():
        lines = read_file("/proc/stat").splitlines()
        if not lines:
            return 0, 0
        parts = lines[0].split()[1:]
        if len(parts) < 4:
            return 0, 0
        try:
            numbers = [int(x) for x in parts]
        except ValueError:
            return 0, 0
        idle = numbers[3] + (numbers[4] if len(numbers) > 4 else 0)
        return idle, sum(numbers)

    try:
        idle1, total1 = sample()
        time.sleep(0.25)
        idle2, total2 = sample()
    except Exception:
        return 0
    delta_total = total2 - total1
    delta_idle = idle2 - idle1
    if delta_total <= 0:
        return 0
    return round((1 - delta_idle / delta_total) * 100)


def storage_stats():
    for path in ("/storage/emulated/0", "/sdcard", Path.home(), "/"):
        if not os.path.exists(path):
            continue
        try:
            usage = shutil.disk_usage(path)
            used_percent = round(usage.used * 100 / usage.total) if usage.total else 0
            free_percent = round(usage.free * 100 / usage.total) if usage.total else 0
            return path, usage.total, usage.used, usage.free, used_percent, free_percent
        except OSError:
            continue
    return "?", 0, 0, 0, 0, 0


def wifi_percent():
    raw = run(["termux-wifi-connectioninfo"], timeout=4)
    if raw:
        try:
            data = json.loads(raw)
            rssi = data.get("rssi")
            ssid = data.get("ssid") or "Wi-Fi"
            if isinstance(rssi, (int, float)):
                # Rough map: -30 dBm ~ 100%, -90 dBm ~ 0%
                percent = int(max(0, min(100, (rssi + 90) * (100 / 60))))
                return ssid, percent, f"{rssi} dBm"
            link = data.get("link_speed_mbps")
            if link:
                return ssid, min(100, int(link)), f"{link} Mbps"
        except json.JSONDecodeError:
            pass

    # Fallback: connected or not
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("1.1.1.1", 80))
        sock.close()
        return "uplink", 100, "online"
    except OSError:
        return "uplink", 0, "offline"


def uptime_stats():
    raw = read_file("/proc/uptime").split()
    if not raw:
        return "unknown", "unknown"
    seconds = int(float(raw[0]))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    uptime = f"{days}d {hours}h {minutes}m {secs}s"
    boot = datetime.now().timestamp() - seconds
    last_boot = datetime.fromtimestamp(boot).strftime("%Y-%m-%d %H:%M:%S")
    return uptime, last_boot


def dashboard():
    """Load screen: GitHub box + live device bars."""
    try:
        wifi_name, wifi_pct, wifi_detail = wifi_percent()
    except Exception:
        wifi_name, wifi_pct, wifi_detail = "uplink", 0, "unknown"
    try:
        uptime, last_boot = uptime_stats()
    except Exception:
        uptime, last_boot = "unknown", "unknown"
    try:
        total_ram, used_ram, free_ram, ram_pct = mem_stats()
    except Exception:
        total_ram = used_ram = free_ram = ram_pct = 0
    try:
        cpu_pct = cpu_usage()
    except Exception:
        cpu_pct = 0
    try:
        storage_path, total_disk, used_disk, free_disk, used_disk_pct, free_disk_pct = storage_stats()
    except Exception:
        storage_path, total_disk, used_disk, free_disk, used_disk_pct, free_disk_pct = "?", 0, 0, 0, 0, 0
    try:
        proc = cpu_name()
    except Exception:
        proc = "unknown"

    print(paint("  SYSTEM HUD", BOLD_CYAN))
    print(paint("  " + line("─", 42), DIM))
    print()
    print(paint(f"  Wi-Fi     {wifi_name}", GREEN) + paint(f"  ({wifi_detail})", DIM))
    print(paint(f"           {bar(wifi_pct)}", CYAN))
    print()
    print(paint(f"  Uptime    {uptime}", GREEN))
    print(paint(f"  Last boot {last_boot}", GREEN))
    print()
    print(paint(f"  Processor {proc[:40]}", GREEN))
    print(paint(f"  CPU use   {bar(cpu_pct)}", YELLOW))
    print()
    print(
        paint(
            f"  RAM       {round(total_ram / 1024)} MB total  |  "
            f"{round(used_ram / 1024)} used  |  {round(free_ram / 1024)} free",
            GREEN,
        )
    )
    print(paint(f"  RAM use   {bar(ram_pct)}", YELLOW))
    print()
    print(
        paint(
            f"  Storage   {gb(total_disk)} GB total  |  "
            f"{gb(used_disk)} used  |  {gb(free_disk)} free",
            GREEN,
        )
    )
    print(paint(f"  Path      {storage_path}", DIM))
    print(paint(f"  Used      {bar(used_disk_pct)}", YELLOW))
    print(paint(f"  Free      {bar(free_disk_pct)}", CYAN))


def boot_sequence():
    clear()
    print()
    github_box(flash=True)
    print()
    dashboard()
    print()
    input(paint("  [ ENTER ] enter console ", DIM))
    clear()


def pause():
    print()
    input(paint("  [ ENTER ] return to console ", DIM))


def module_header(name):
    clear()
    status_bar()
    print()
    print(paint(f"  ▸ MODULE :: {name}", BOLD_GREEN))
    print(paint("  " + line("─", 42), DIM))
    print()


def scan_device():
    module_header("DEVICE SCAN")
    rows = [
        f"brand     {getprop('ro.product.brand') or '?'}",
        f"model     {getprop('ro.product.model') or '?'}",
        f"device    {getprop('ro.product.device') or '?'}",
        f"android   {getprop('ro.build.version.release') or '?'}",
        f"sdk       {getprop('ro.build.version.sdk') or '?'}",
        f"patch     {getprop('ro.build.version.security_patch') or '?'}",
        f"abi       {getprop('ro.product.cpu.abi') or platform.machine()}",
        f"kernel    {platform.release()}",
        f"python    {platform.python_version()}",
    ]
    box(" TARGET FINGERPRINT ", rows)
    pause()


def scan_memory():
    module_header("MEMORY MAP")
    total, used, avail, percent = mem_stats()
    rows = [
        f"total     {round(total / 1024)} MB",
        f"used      {round(used / 1024)} MB",
        f"free      {round(avail / 1024)} MB",
        f"load      {bar(percent)}",
    ]
    box(" MEMORY ", rows)
    pause()


def net_probe():
    module_header("UPLINK PROBE")
    host = "1.1.1.1"
    print(paint(f"  probing {host} ...", DIM))
    print()
    times = []
    for i in range(1, 6):
        text = run(["ping", "-c", "1", "-W", "2", host])
        ms = None
        for line_text in text.splitlines():
            if "time=" in line_text.lower():
                piece = line_text.lower().split("time=", 1)[1]
                number = ""
                for char in piece:
                    if char.isdigit() or char == ".":
                        number += char
                    elif number:
                        break
                if number:
                    ms = float(number)
                break
        if ms is None:
            print(paint(f"  [{i}/5] TIMEOUT", RED))
        else:
            times.append(ms)
            print(paint(f"  [{i}/5] {ms:.0f} ms", GREEN))
    print()
    if times:
        avg = round(sum(times) / len(times))
        grade = "S" if avg <= 10 else "A" if avg <= 20 else "B" if avg <= 35 else "C" if avg <= 50 else "D" if avg <= 80 else "E" if avg <= 120 else "F"
        box(" LINK CLASS ", [f"average   {avg} ms", f"class     {grade}", f"lost      {5 - len(times)}/5"])
    else:
        box(" LINK CLASS ", ["status    DEAD CHANNEL", "class     F"])
    pause()


def port_probe():
    module_header("PORT PROBE")
    host = input(paint("  host [1.1.1.1]: ", CYAN)).strip() or "1.1.1.1"
    port_raw = input(paint("  port [443]: ", CYAN)).strip() or "443"
    if not port_raw.isdigit():
        print(paint("  invalid port", RED))
        pause()
        return
    port = int(port_raw)
    started = time.time()
    try:
        with socket.create_connection((host, port), timeout=5):
            ms = round((time.time() - started) * 1000)
            box(" RESULT ", [f"target    {host}:{port}", f"state     OPEN", f"latency   {ms} ms"])
    except OSError:
        box(" RESULT ", [f"target    {host}:{port}", "state     CLOSED / FILTERED"])
    pause()


def process_radar():
    module_header("PROCESS RADAR")
    text = run(["ps", "-A"], timeout=10)
    if not text:
        print(paint("  no process data", RED))
        pause()
        return
    lines = [line_text for line_text in text.splitlines() if line_text.strip()]
    print(paint("  top of process table", DIM))
    print()
    for line_text in lines[:20]:
        print(paint("  " + line_text[:70], GREEN))
    if len(lines) > 20:
        print(paint(f"  ... {len(lines) - 20} more", DIM))
    pause()


def shell_drop():
    module_header("SHELL DROP")
    print(paint("  type a command to run inside Termux", DIM))
    print(paint("  empty line cancels", DIM))
    print()
    command = input(paint("  $ ", CYAN)).strip()
    if not command:
        return
    print()
    print(paint("  --- output ---", DIM))
    out = run(command.split(), timeout=20)
    print(out or paint("  (no output)", DIM))
    pause()


def torch_pulse():
    module_header("TORCH")
    if not shutil.which("termux-torch"):
        print(paint("  termux-api missing", YELLOW))
        print(paint("  pkg install termux-api", DIM))
        pause()
        return
    print(paint("  [1] ignite", GREEN))
    print(paint("  [2] kill", RED))
    choice = input(paint("  select: ", CYAN)).strip()
    if choice == "1":
        run(["termux-torch", "on"])
        box(" TORCH ", ["state     ONLINE"])
    elif choice == "2":
        run(["termux-torch", "off"])
        box(" TORCH ", ["state     OFFLINE"])
    else:
        print(paint("  cancelled", DIM))
    pause()


def about():
    module_header("ABOUT")
    box(
        " ERDIUI ",
        [
            "operator console for Termux",
            "theme: hacker / high-power look",
            "truth: useful tools, loud style",
            GITHUB,
        ],
    )
    pause()


def main_menu():
    clear()
    status_bar()
    print()
    github_box(flash=False)
    print()
    print(paint("  MODULES", BOLD_CYAN))
    print(paint("  " + line("─", 42), DIM))
    tiles = [
        ("1", "DEVICE SCAN", "fingerprint the phone"),
        ("2", "MEMORY MAP", "RAM pressure view"),
        ("3", "UPLINK PROBE", "ping class to 1.1.1.1"),
        ("4", "PORT PROBE", "check host:port"),
        ("5", "PROCESS RADAR", "list running processes"),
        ("6", "SHELL DROP", "run one Termux command"),
        ("7", "TORCH", "flash control"),
        ("8", "ABOUT", "what this is"),
        ("0", "EXIT", "close console"),
    ]
    for number, name, desc in tiles:
        print(
            paint(f"  [{number}]", BOLD_GREEN)
            + paint(f" {name:<14}", CYAN)
            + paint(f" {desc}", DIM)
        )
    print()
    return input(paint("  select module > ", BOLD_GREEN)).strip().lower()


def main():
    try:
        boot_sequence()
    except Exception as error:
        clear()
        print("Startup error:")
        print(error)
        print()
        input("Press Enter to try the menu anyway...")
    actions = {
        "1": scan_device,
        "2": scan_memory,
        "3": net_probe,
        "4": port_probe,
        "5": process_radar,
        "6": shell_drop,
        "7": torch_pulse,
        "8": about,
    }
    while True:
        try:
            choice = main_menu()
            if choice in {"0", "q", "quit", "exit"}:
                clear()
                print(paint("  session closed.", DIM))
                github_box(flash=False)
                break
            action = actions.get(choice)
            if action:
                action()
            else:
                print(paint("  unknown module", RED))
                time.sleep(0.7)
        except KeyboardInterrupt:
            clear()
            print(paint("\n  session aborted.", DIM))
            break


if __name__ == "__main__":
    main()
