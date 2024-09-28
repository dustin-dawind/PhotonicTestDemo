import sys
import os
import tomllib
import subprocess
import ctypes
from ctypes import wintypes
from pathlib import Path

from analysisfromtoml import analysis_scripts

from rich import print
from rich.pretty import pprint
from rich.console import Console
console = Console()

import traceback


sys.excepthook = lambda *args: (traceback.print_exception(*args), console.input("[red]\n\nPress any key to exit...[/]"))


ReturnCode = int


# Check if the script is being run in a frozen environment (e.g. as an executable)
is_frozen = getattr(sys, 'frozen', False)
if is_frozen:
    cwd = Path(sys._MEIPASS)
else:
    cwd = Path.cwd()


if "analysisfromtoml" not in cwd.parts:
    path_to_package = cwd / Path(r"analysisfromtoml/")
else:
    path_to_package = cwd

path_to_config_toml = path_to_package / Path(r"config.toml")

# TODO: Reconfigure path to sublime_text.exe to the portable version kept on flash drive when that's set up
path_to_notepad_plus_plus = Path(r'C:\Program Files\Sublime Text\sublime_text.exe')

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
user32 = ctypes.WinDLL('user32', use_last_error=True)


FLASHW_STOP = 0
FLASHW_CAPTION = 0x00000001
FLASHW_TRAY = 0x00000002
FLASHW_ALL = 0x00000003
FLASHW_TIMER = 0x00000004
FLASHW_TIMERNOFG = 0x0000000C


class FLASHWINFO(ctypes.Structure):
    _fields_ = (('cbSize', wintypes.UINT),
                ('hwnd', wintypes.HWND),
                ('dwFlags', wintypes.DWORD),
                ('uCount', wintypes.UINT),
                ('dwTimeout', wintypes.DWORD))

    def __init__(self, hwnd, flags=FLASHW_TRAY, count=5, timeout_ms=0):
        self.cbSize = ctypes.sizeof(self)
        self.hwnd = hwnd
        self.dwFlags = flags
        self.uCount = count
        self.dwTimeout = timeout_ms


kernel32.GetConsoleWindow.restype = wintypes.HWND
user32.FlashWindowEx.argtypes = (ctypes.POINTER(FLASHWINFO),)
user32.IsIconic.argtypes = (wintypes.HWND,)
user32.IsIconic.restype = wintypes.BOOL


def flash_console_icon(n_times: int = 5):
    console_handle = kernel32.GetConsoleWindow()
    if not console_handle:
        raise ctypes.WinError(ctypes.get_last_error())
    winfo = FLASHWINFO(console_handle, n_times)
    previous_state = user32.FlashWindowEx(ctypes.byref(winfo))
    return previous_state


def launch_cmd():
    path_to_module = path_to_package / Path(r"analysis_from_toml.py")
    os.system(f"start cmd.exe /c python \"{path_to_module}\"")


def get_config_from_toml():
    """Reads configuration settings from config.toml, sets `config_vars`, and returns the contents of config.toml

    Returns
    -------
    config_toml : dict
        The contents of config.toml
    """
    try:
        with open(path_to_config_toml, "rb") as f:
            return tomllib.load(f)
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        try_open_sublime()

        try:
            with open(path_to_config_toml, "rb") as f:
                return tomllib.load(f)
        except (FileNotFoundError, tomllib.TOMLDecodeError):
            raise


def clear_console():
    """Clears the console window.

    `\033[` is the special ANSI escape code called the Control Sequence Introducer (CSI).

    * `\033[H` == sequence that moves the cursor to the top of the screen
    * `\033[J` == sequence that clears the screen from the cursor to the end of the screen.
        --> `\033[xJ` == behavior depends on the value of `x`
            ==> if `x` == 0 or missing, clear from cursor to end of screen
            ==> if `x` == 1, clear from cursor to beginning of the screen
            ==> if `x` == 2, clear entire screen and moves cursor to upper left
            ==> if `x` == 3, clear entire screen and delete all lines saved in the scrollback buffer

    References: https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_(Control_Sequence_Introducer)_sequences
    """
    console.print("\x1b[H\x1b[2J")


def try_open_sublime():
    try:
        # Try using sublime text first if possible
        sublime = subprocess.Popen([path_to_notepad_plus_plus, path_to_config_toml])
        sublime.wait()
        return_code = sublime.returncode
        if return_code != 0:
            raise subprocess.SubprocessError

    except (subprocess.SubprocessError, OSError):
        # Fall back to regular notepad if notepad++ isn't found or if it crashes for some reason
        return_code = open_notepad()
        if return_code != 0:
            raise RuntimeError("An unexpected error occurred while trying to open an editor for input.toml")
    finally:
        # Clear the console window so it doesn't get cluttered
        os.system('cls')


def open_notepad() -> ReturnCode:

    notepad = subprocess.Popen(['notepad.exe', path_to_config_toml])
    notepad.wait()
    return notepad.returncode


def verify_input_with_user(input_dict: dict):

    def get_user_input(preamble: str = None) -> str:
        if user32.IsIconic(kernel32.GetConsoleWindow()):
            flash_console_icon(10)

        if preamble is not None:
            console.print(preamble, end="")
        return console.input("\n([yellow]y[/] \[[yellow]yes[/]]/ [yellow]e[/] \[[yellow]edit[/]]/"
                             " [yellow]q[/] \[[yellow]quit[/]]):"
                             "\n"
                             )

    def parse_response(res: str):
        global analysis_config

        match res:
            case "y" | "yes" | "Y" | "Yes" | "YES":
                paths = {}
                if Path(analysis_config["input_dir_paths"]["liv"]).is_file():
                    paths["liv"] = analysis_config["input_dir_paths"]["liv"]
                if Path(analysis_config["input_dir_paths"]["rev_iv"]).is_file():
                    paths["rev_iv"] = analysis_config["input_dir_paths"]["rev_iv"]

                if len(paths) == 0:
                    print("[red]No input files found. Please edit config.toml to specify input files...[/]")
                    try_open_sublime()
                    pprint(analysis_config := get_config_from_toml(), expand_all=True)
                    parse_response(get_user_input(preamble="\nPlease confirm that the *edited* version of the run"
                                                           " configuration is correct.")
                                   )
                else:
                    return
            case "q" | "quit" | "Quit" | "QUIT":
                print("Update cancelled... Exiting...")
                sys.exit(0)
            case "e" | "edit" | "Edit" | "EDIT":
                if input_dict["edit_with_sublime_text"] is False:
                    # Try using notepad
                    return_code = open_notepad()
                    if return_code != 0:
                        raise RuntimeError("An unexpected error occurred while trying to open an editor for input.toml")
                else:
                    try_open_sublime()
                pprint(analysis_config := get_config_from_toml(), expand_all=True)
                parse_response(get_user_input(preamble="\nPlease confirm that the *edited* version of the run"
                                                       " configuration is correct.")
                               )

            case _:
                parse_response(get_user_input())

    os.system('cls')

    pprint(input_dict, expand_all=True)
    parse_response(get_user_input(preamble="\nPlease confirm that the above run configuration is correct."))


if __name__ == "__main__":
    if is_frozen:
        console.clear()

    analysis_config = get_config_from_toml()
    verify_input_with_user(analysis_config)

    if analysis_config["input_dir_paths"]["liv"] != '':
        analysis_scripts.liv_analysis(data_path=Path(analysis_config["input_dir_paths"]["liv"]),
                                      analysis_flags=analysis_config["analysis_flags"]["liv"],
                                      analysis_groupings=analysis_config["group_data_by"]
                                      )

    console.input("[bright_green]Analysis complete. Press any key to exit...[/]")

