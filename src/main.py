import sys

from dataclasses import dataclass
from pathlib import Path
from platform import system
from subprocess import run, CalledProcessError, CompletedProcess


@dataclass
class Config:
    name: str
    desc: str
    dots_to_setup: list[str]
    operating_systems: list[str]


class Dot:
    def __init__(self, name: str, path: Path):
        self._install_script: Path|None
        self._setup_script: Path|None
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

    def setup(self, install: bool=False) -> CalledProcessError|CompletedProcess|None:
        if install:
            try:
                _ = self._install()
            except CalledProcessError as error:
                raise error
        if self.setup_script is not None:
            result: CalledProcessError|CompletedProcess = run(self.setup_script, check=True)
            return result
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


def get_dots(dotfiles_dir: Path) -> list[Dot]:
    dirs: list[Path] = [ dir for dir in dotfiles_dir.iterdir() if dir.is_dir() and any(file for file in dir.iterdir() if file.is_file() and file.stem == "setup") ]
    dots: list[Dot] = [ Dot(name=dir.name, path=dir) for dir in sorted(dirs) ]
    return dots


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


def main():
    dotfiles_dir: Path = get_dotfiles_dir(sys.argv)
    dots: list[Dot] = get_dots(dotfiles_dir)

    for dot in dots:
        print(dot)

    # failed: list[Dot] = []
    # for dot in dots:
    #     result = dot.setup()
    #     if isinstance(result, CalledProcessError):
    #         failed.append(dot)
    # if len(failed) > 0:
    #     print("The following dots failed to setup:")
    #     for f in failed:
    #         print(f.name)


if __name__ == "__main__":
    main()
