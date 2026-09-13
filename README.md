# ErdiUI
#Still Broken Af
#Not as broken, i kind of fixed some things that were not working, 70% done

A Termux operator console with a loud hacker look.

It is meant to *feel* powerful. On load it shows the GitHub banner and a system HUD, then opens a module menu for real Termux tools.

## What you see on load

- Flashing GitHub box (`github.com/erdi-exe`)
- Wi-Fi signal percentage bar
- Uptime and last boot
- Processor name
- CPU usage bar
- RAM total / used / free + usage bar
- Storage total / used / free + used and free bars

## Modules

1. Device scan
2. Memory map
3. Uplink probe (ping class)
4. Port probe
5. Process radar
6. Shell drop
7. Torch
8. About
0. Exit

## Requirements

- Android phone
- Termux from F-Droid or the official GitHub release
- Python 3

`requirements.txt` has no pip packages.

Optional:

```bash
pkg install termux-api
```

Install the **Termux:API** Android app too for Wi-Fi signal % and torch.

## How to run in Termux

```bash
pkg update
pkg upgrade
pkg install python git
cd ~
git clone https://github.com/erdi-exe/erdiui.git
cd erdiui
pip install -r requirements.txt
python erdi_ui.py
```

Update later:

```bash
cd ~/erdiui
git pull
python erdi_ui.py
```

Exit with `0`, or Volume Down + C for Ctrl+C.
