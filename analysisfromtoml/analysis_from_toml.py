import sys
import os
import tomllib
import subprocess
from pathlib import Path

from rich.pretty import pprint

from rich.console import Console
console = Console()


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


config_vars = {
    "LIV_DATA"    : None,
    "REV_IV_DATA": None,
    "OUTPUT_PATH": None,
}


def launch_cmd():
    path_to_module = path_to_package / Path(r"analysis_from_toml.py")
    os.system(f"start cmd.exe /k python \"{path_to_module}\"")

def get_config_from_toml():
    """Reads configuration settings from config.toml, sets `config_vars`, and returns the contents of config.toml

    Returns
    -------
    config_toml : dict
        The contents of config.toml
    """
    with open(path_to_config_toml, "rb") as f:
        config = tomllib.load(f)

    config_vars["LIV_DIR"] = config["input_dir_paths"]["liv"]
    config_vars["SPECTRA_DIR"] = config["input_dir_paths"]["spectra"]
    config_vars["OUTPUT_PATH"] = config["output_filepath"]
    config_vars["use_sublime"] = config["edit_with_sublime_text"]

    return config

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


ReturnCode = int


def verify_input_with_user(input_dict: dict):

    def get_user_input(preamble: str = None) -> str:
        if preamble is not None:
            console.print(preamble, end="")
        return console.input("\n([yellow]y[/] \[[yellow]yes[/]]/ [yellow]e[/] \[[yellow]edit[/]]/"
                             " [yellow]q[/] \[[yellow]quit[/]]):"
                             "\n"
                             )

    def open_sublime() -> ReturnCode:
        sublime = subprocess.Popen([path_to_notepad_plus_plus, path_to_config_toml])
        sublime.wait()

        return sublime.returncode

    def open_notepad() -> ReturnCode:
        notepad = subprocess.Popen(['notepad.exe', path_to_config_toml])
        notepad.wait()

        return notepad.returncode

    def parse_response(res: str):
        match res:
            case "y" | "yes" | "Y" | "Yes" | "YES":
                return
            case "q" | "quit" | "Quit" | "QUIT":
                print("Update cancelled... Exiting...")
                sys.exit(0)
            case "e" | "edit" | "Edit" | "EDIT":
                if config_vars["use_sublime"] is False:
                    # Try using notepad
                    return_code = open_notepad()
                    if return_code != 0:
                        raise RuntimeError("An unexpected error occurred while trying to open an editor for input.toml")

                else:
                    try:
                        # Try using sublime text first if possible
                        return_code = open_sublime()
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

                pprint(get_config_from_toml(), indent_guides=False)
                parse_response(get_user_input(preamble="\nPlease confirm that the *edited* version of the run"
                                                       " configuration is correct.")
                               )

            case _:
                parse_response(get_user_input())

    os.system('cls')

    pprint(input_dict, indent_guides=False)
    parse_response(get_user_input(preamble="\nPlease confirm that the above run configuration is correct."))


if __name__ == "__main__":
    if is_frozen:
        console.clear()

    verify_input_with_user(get_config_from_toml())
