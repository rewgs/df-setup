import sys

from dataclasses import dataclass
from functools import cache
from pathlib import Path
from platform import system
from subprocess import run, CalledProcessError, CompletedProcess


@dataclass
class App:
    """
    An App represents an application that, if listed as part of a Config, 
    will be installed/setup/etc as specified via its corresponding Dot.
    """
    name: str
    to_install: bool=False


@dataclass
class Config:
    """A Config is a collection of Dots to be installed/setup/etc for a target machine."""
    name: str
    to_setup: list[App]
    operating_systems: set[str]
    desc: str|None=None


class Dot:
    """A Dot represents a single application that is configured via dotfiles."""
    def __init__(self, name: str, path: Path):
        self._install_script: Path|None
        self._setup_script: Path|None
        self._to_install: bool = False
        self.name: str = name
        self.path: Path = path

        self._install_script = self.__get_script("install")
        self._setup_script = self.__get_script("setup")

    @property
    def install_script(self) -> Path|None:
        return self._install_script

    @install_script.setter
    def install_script(self, value: Path) -> None:
        self._install_script = value

    @property
    def setup_script(self) -> Path|None:
        return self._setup_script

    @setup_script.setter
    def setup_script(self, value: Path) -> None:
        self._setup_script = value

    @property
    def to_install(self) -> bool:
        return self._to_install

    @to_install.setter
    def to_install(self, value: bool) -> None:
        self._to_install = value

    def setup(self) -> CalledProcessError|CompletedProcess|None:
        """ Sets up the dotfiles of the application in question. Installs beforehand if instructed. """
        if self.to_install and self.install_script is not None:
            install_result = self._install()
            # FIXME: This isn't great, because if this function returns CalledProcessError or None, 
            # I won't know if it's due to the installation or setup process.
            if install_result is None or isinstance(install_result, CalledProcessError):
                return install_result
        if self.setup_script is not None:
            setup_result: CalledProcessError|CompletedProcess = run(self.setup_script, check=True)
            return setup_result
        return None

    def _install(self) -> CalledProcessError|CompletedProcess|None:
        if self.install_script is not None:
            result: CalledProcessError|CompletedProcess = run(self.install_script, check=True)
            return result
        return None

    def __get_script(self, name: str) -> Path|None:
        match system():
            case "Windows":
                matches: list[Path] = [ file for file in self.path.iterdir() if file.is_file() and (file.name == f"{name}.ps1" or file.name == f"{name}.py") ]
                if len(matches) != 1:
                    return None
                return matches[0]
            case _:
                matches: list[Path] = [ file for file in self.path.iterdir() if file.is_file() and (file.name == f"{name}.sh" or file.name == f"{name}.py") ]
                if len(matches) != 1:
                    return None
                return matches[0]


def get_dotfiles_dir(args) -> Path:
    match len(args):
        case 1:
            dotfiles: Path = Path.home().joinpath("dotfiles")
        case 2:
            dotfiles: Path = Path(args[1]).resolve(strict=True)
        case _:
            print("Too many arguments!")
            exit()
    try:
        resolved: Path = dotfiles.resolve(strict=True)
    except FileNotFoundError as error:
        raise error
    else:
        return resolved


@cache
def get_dots(dotfiles_dir: Path) -> list[Dot]:
    dirs: list[Path] = [ dir for dir in dotfiles_dir.iterdir() if dir.is_dir() and any(file for file in dir.iterdir() if file.is_file() and file.stem == "setup") ]
    dots: list[Dot] = [ Dot(name=dir.name, path=dir) for dir in sorted(dirs) ]
    return dots


def apply_config(config: Config, dots: list[Dot]) -> tuple[list[Dot], list[Dot]]:
    def get_dots_from_config(config: Config, dots: list[Dot]) -> list[Dot]:
        to_setup: list[Dot] = []
        for dot in dots:
            for app in config.to_setup:
                if app.name == dot.name:
                    dot.to_install = app.to_install
                    to_setup.append(dot)
        return to_setup

    def setup_dots(dots: list[Dot]) -> tuple[list[Dot], list[Dot]]:
        failed: list[Dot] = []
        succeeded: list[Dot] = []
        for dot in to_setup:
            result = dot.setup()
            if isinstance(result, CalledProcessError):
                failed.append(dot)
            elif isinstance(result, CompletedProcess):
                succeeded.append(dot)
        return failed, succeeded

    to_setup: list[Dot] = get_dots_from_config(config, dots)
    # for dot in to_setup:
    #     print(dot.name)
    return setup_dots(to_setup)


def postflight(failed: list[Dot], succeeded: list[Dot]) -> None:
    if len(failed) > 0:
        print("The following applications failed to install or setup:")
        for dot in failed:
            print(dot.name)
    if len(succeeded) > 0:
        print("The following applications succeeded setup:")
        for dot in succeeded:
            print(dot.name)


def main():
    dotfiles_dir: Path = get_dotfiles_dir(sys.argv)

    # TODO: Should only be getting Dots of Apps specified in Config, rather than *all* of them as I'm doing here.
    dots: list[Dot] = get_dots(dotfiles_dir)

    # for dot in dots:
    #     print(dot.name)

    apps = [
        App(name="bash", to_install=False),
        App(name="nvim", to_install=False),
        App(name="starship", to_install=True),
        App(name="tmux", to_install=False),
        App(name="vim", to_install=False),
        App(name="zsh", to_install=False),
    ]

    config = Config(name="Linux CLI", 
                    to_setup=apps, 
                    operating_systems={"Linux"})

    failed, succeeded = apply_config(config, dots)
    postflight(failed, succeeded)


if __name__ == "__main__":
    main()
