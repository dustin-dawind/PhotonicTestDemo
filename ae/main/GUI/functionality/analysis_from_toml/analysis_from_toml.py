import sys
import tomllib
import subprocess
from pprint import PrettyPrinter


config_vars = {
    "LIV_DIR"    : None,
    "SPECTRA_DIR": None,
    "OUTPUT_PATH": None,
}


def launch_cmd():
    subprocess.Popen(["cmd.exe", "python", r"ae\functionality\analysis_from_toml\analysis_from_toml.py"])

def get_config_from_toml():
    """Reads configuration settings from config.toml, sets `config_vars`, and returns the contents of config.toml

    Returns
    -------
    config_toml : dict
        The contents of config.toml

    """
    with open(r"config.toml", "rb") as f:
        config = tomllib.load(f)

    config_vars["LIV_DIR"] = config["input_dir_paths"]["liv"]
    config_vars["SPECTRA_DIR"] = config["input_dir_paths"]["spectra"]
    config_vars["OUTPUT_PATH"] = config["output_filepath"]

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
    print("\033[H\033[2J", end="")


class NoStrWrapPrettyPrinter(PrettyPrinter):
    def _format(self, object, *args):
        if isinstance(object, str):
            width = self._width
            self._width = sys.maxsize
            try:
                super()._format(object, *args)
            finally:
                self._width = width
        else:
            super()._format(object, *args)


def high_vis_print(config_dict):
    """Constructs a formatted string of the contents of config.toml (using ANSI color codes) and prints the result to
    stdout.

    Parameters
    ----------
    config_dict : dict
        The contents of config.toml
    """
    def set_key_color(key_str: str):
        return f"\033[94m{key_str}\033[0m"

    def set_value_color(value_str: str):
        return f"\033[92m{value_str}\033[0m"

    keys, values = config_dict.keys(), config_dict.values()
    subkeys = list(subkey for value in values if isinstance(value, dict) for subkey in value.keys())
    subvalues = list(subvalue for value in values if isinstance(value, dict) for subvalue in value.values())

    for key, value in zip(keys, values):
        colored_key = set_key_color(key)
        config_dict[colored_key] = config_dict.pop(key)

        if isinstance(value, dict):
            for subkey, subvalue in zip(subkeys, subvalues):
                colored_subkey = set_key_color(subkey)
                colored_subvalue = set_value_color(subkey)
                config_dict[colored_key][colored_subkey] = config_dict[colored_key].pop(subkey)
                config_dict[colored_key][colored_subkey] = colored_subvalue

        else:
            config_dict[colored_key] = set_value_color(config_dict[colored_key])

    NoStrWrapPrettyPrinter().pprint(config_dict)



if __name__ == "__main__":
    clear_console()

    high_vis_print(get_config_from_toml())