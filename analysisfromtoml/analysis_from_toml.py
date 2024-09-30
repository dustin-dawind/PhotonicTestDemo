import sys
import os
import tomllib
import subprocess
import ctypes
from ctypes import wintypes
from pathlib import Path

from analysisfromtoml import analysis_scripts

from PyQt5.QtCore import (
    QObject,
    QThread,
    pyqtSignal,
    QTimer, pyqtSlot
)

from rich import print
from rich.pretty import pprint
from rich.console import Console
console = Console()

# import traceback


# sys.excepthook = lambda *args: (traceback.print_exception(*args), console.input("[red]\n\nPress any key to exit...[/]"))


ReturnCode = int


# Check if the script is being run in a frozen environment (e.g. as an executable)
is_frozen = getattr(sys, 'frozen', False)
if is_frozen:
    cwd = Path(sys._MEIPASS)
else:
    cwd = Path.cwd()


path_to_package = cwd / "resources"

path_to_config_toml = path_to_package / "config.toml"

# TODO: Reconfigure path to sublime_text.exe to the portable version kept on flash drive when that's set up
path_to_sublime_text = Path(r'C:\Program Files\Sublime Text\sublime_text.exe')

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


class Analysis(QObject):
    user_accepted = pyqtSignal()
    request_user_input = pyqtSignal()
    user_quit_analysis = pyqtSignal()
    figure_saved = pyqtSignal(Path)

    def __init__(self):
        super().__init__()
        self.analysis_config = self.get_config_from_toml()
        self.liv_filepath = None

        self.input_verification = InputVerifier()
        self._input_verification_thread = QThread()
        self.input_verification.moveToThread(self._input_verification_thread)
        self._input_verification_thread.start()
        self.input_verification.response_received.connect(self.parse_response)

        self.request_user_input.connect(self.input_verification.user_input)

        self.user_accepted.connect(self.launch_analysis)
        self.figure_saved.connect(self._input_verification_thread.quit)
        self.user_quit_analysis.connect(self._input_verification_thread.quit)

    @pyqtSlot()
    def analysis_entry_point(self):
        if is_frozen:
            console.clear()
        self.verify_input_with_user()

    @staticmethod
    def get_config_from_toml() -> dict:
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

    @pyqtSlot(str)
    def parse_response(self, response: str):
        match response:
            case "y" | "yes" | "Y" | "Yes" | "YES":
                paths = {}
                liv_path = self.analysis_config["input_dir_paths"]["liv"]
                if is_frozen:
                    liv_path = liv_path.lstrip(".\\")
                    self.liv_filepath = Path(sys._MEIPASS) / liv_path
                else:
                    self.liv_filepath = Path(liv_path)

                if self.liv_filepath.is_file():
                    paths["liv"] = self.liv_filepath
                if Path(self.analysis_config["input_dir_paths"]["rev_iv"]).is_file():
                    paths["rev_iv"] = self.analysis_config["input_dir_paths"]["rev_iv"]

                if len(paths) == 0:
                    print("[red]No input files found. Please edit config.toml to specify input files...[/]")
                    try_open_sublime()
                    self.analysis_config = self.get_config_from_toml()
                    pprint(self.analysis_config, expand_all=True)
                    self.get_user_input(preamble="\nPlease confirm that the *edited* version of the run"
                                                 " configuration is correct.")
                else:
                    self.user_accepted.emit()

            case "q" | "quit" | "Quit" | "QUIT":
                console.print("[bright_red]Analysis aborted...[/]")
                self.user_quit_analysis.emit()
                # breakpoint()
            case "e" | "edit" | "Edit" | "EDIT":
                if self.analysis_config["edit_with_sublime_text"] is False:
                    # Try using notepad
                    return_code = open_notepad()
                    if return_code != 0:
                        raise RuntimeError(
                                "An unexpected error occurred while trying to open an editor for input.toml")
                else:
                    try_open_sublime()
                self.analysis_config = self.get_config_from_toml()
                pprint(self.analysis_config, expand_all=True)
                self.get_user_input(preamble="\nPlease confirm that the *edited* version of the run"
                                             " configuration is correct.")

            case _:
                self.get_user_input()

    def get_user_input(self, preamble: str = None):
        if user32.IsIconic(kernel32.GetConsoleWindow()):
            flash_console_icon(10)

        if preamble is not None:
            console.print(preamble, end="")
        console.print("\n([yellow]y[/] \[[yellow]yes[/]]/ [yellow]e[/] \[[yellow]edit[/]]/"
                      " [yellow]q[/] \[[yellow]quit[/]]):"
                      "\n"
                      )
        self.request_user_input.emit()

    @pyqtSlot()
    def verify_input_with_user(self):
        os.system('cls')
        pprint(self.analysis_config, expand_all=True)
        self.get_user_input(preamble="\nPlease confirm that the above run configuration is correct.")

    @pyqtSlot()
    def launch_analysis(self):
        if self.analysis_config["input_dir_paths"]["liv"] != '':
            plot_path = analysis_scripts.liv_analysis(data_path=self.liv_filepath,
                                                      analysis_flags=self.analysis_config["analysis_flags"]["liv"],
                                                      analysis_groupings=self.analysis_config["group_data_by"]
                                                      )

            console.print("\n\n[bright_green]LIV analysis complete.[/]")
            self.figure_saved.emit(plot_path)

class InputVerifier(QObject):
    response_received = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_response = None

        self.check_response_timer = QTimer(self)
        self.check_response_timer.timeout.connect(self.is_response_ready)
        self.check_response_timer.start(100)

    @pyqtSlot()
    def user_input(self):
        self.user_response = console.input()

    @pyqtSlot()
    def is_response_ready(self):
        if self.user_response is not None:
            self.response_received.emit(self.user_response)
            self.user_response = None


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
        sublime = subprocess.Popen([path_to_sublime_text, path_to_config_toml])
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

