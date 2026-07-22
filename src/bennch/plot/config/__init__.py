"Some basic configuration that is read from external sources."

import logging
import os
from pathlib import Path
from stat import S_IMODE

log = logging.getLogger(__name__)


class XDG:
    """
    Implements XDG Base Directory Specification.

    All basic and system path variables are implemented in this class, together
    with their suggested default values. However, except for the
    `$XDG_RUNTIME_DIR` no existance is asserted and paths may need to be
    created. Make sure to set appropriate `mode`, e.g. with

    ```
    xdg = XDG("myname")
    (xdg.cache_home / "myname").mkdir(mode=0x700, parents=True, exist_ok=True)
    ```

    Note that similar fuctionality is implemented in `platformdirs` package.

    See Also
    --------
    * https://specifications.freedesktop.org/basedir/latest/
    * https://wiki.archlinux.org/title/XDG_Base_Directory
    """

    def __init__(self, myname: str = ""):
        """
        Use the given <myname> as application specific subdir.

        Adds the name to all returned `_home` paths.
        """
        self._myname = myname

    @property
    def cache_home(self) -> Path:
        """
        User-specific cached data $XDG_CACHE_HOME.

        Where user-specific non-essential (cached) data should be written
        (analogous to `/var/cache`).

        Should default to `$HOME/.cache`.
        """
        return Path(os.environ.get("XDG_CACHE_HOME", os.path.expandvars("$HOME/.cache"))) / self._myname

    @property
    def data_home(self) -> Path:
        """
        User-specific data files directory $XDG_DATA_HOME.

        Where user-specific data files should be written (analogous to
        `/usr/share`).

        Should default to `$HOME/.local/share`.
        """
        return Path(os.environ.get("XDG_DATA_HOME", os.path.expandvars("$HOME/.local/share"))) / self._myname

    @property
    def config_home(self) -> Path:
        """
        User-specific configuration files $XDG_CONFIG_HOME.

        Where user-specific configurations should be written (analogous to
        `/etc`).

        Should default to `$HOME/.config`.
        """
        return Path(os.environ.get("XDG_CONFIG_HOME", os.path.expandvars("$HOME/.config"))) / self._myname

    @property
    def state_home(self) -> Path:
        """
        User-specific state files $XDG_STATE_HOME.

        Where user-specific state files should be written (analogous to
        `/var/lib`).

        Should default to `$HOME/.local/state`.
        """
        return Path(os.environ.get("XDG_STATE_HOME", os.path.expandvars("$HOME/.local/state"))) / self._myname

    @property
    def runtime_dir(self) -> Path:
        """
        Non-essential local user-specific session files $XDG_RUNTIME_DIR.

        Used for non-essential, user-specific data files such as sockets, named pipes, etc.

        Not required to have a default value; warnings should be issued if not
        set or equivalents provided.

        * Must be owned by the user with an access mode of 0700.
        * Filesystem fully featured by standards of OS.
        * Must be on the local filesystem.
        * May be subject to periodic cleanup.
        * Modified every 6 hours or set sticky bit if persistence is desired.
        * Can only exist for the duration of the user's login.
        * Should not store large files as it may be mounted as a tmpfs.
        * pam_systemd sets this to /run/user/$UID.
        """
        if "XDG_RUNTIME_DIR" not in os.environ:
            log.warning("XDG_RUNTIME_DIR is not set.")
        else:
            log.debug("XDG_RUNTIME_DIR is set to %s", os.environ["XDG_RUNTIME_DIR"])
        runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR", os.path.expandvars("/run/user/$UID")))
        assert runtime_dir.exists()
        assert runtime_dir.is_dir()
        stat = runtime_dir.stat()
        assert stat.st_uid == os.getuid(), "XDG_RUNTIME_DIR must be owned by current process' user id."
        mode = S_IMODE(stat.st_mode)
        assert mode == 0o700, f"XDG_RUNTIME_DIR has to be writable by the user only, but is {mode:#o}"
        return runtime_dir

    @property
    def user_bin_dir(self) -> Path:
        """
        Custom definition of $HOME/.local/bin.

        Commonly used for user-specific executable files

        Note
        ----
            There is NO `$XDG_BIN_HOME` directory `$HOME/.local` is intended to
            be analogous to `/usr/local`.

        Note
        ----
            Since $HOME might be shared between systems of different
            architectures, installing compiled binaries to `$HOME/.local/bin`
            could cause problems when used on systems of differing
            architectures. This is often not a problem, but the fact that `$HOME`
            becomes partially architecture-specific if compiled binaries are
            placed in it should be kept in mind.
        """
        return Path(os.environ.get("XDG_BIN_HOME", os.path.expandvars("$HOME/.local/bin")))

    @property
    def data_dirs(self) -> list[Path]:
        """
        System directories XDG_DATA_DIRS.

        List of directories separated by : (analogous to PATH).

        Should default to /usr/local/share:/usr/share.
        """
        return [Path(p) for p in os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")]

    @property
    def config_dirs(self) -> list[Path]:
        """
        System directories XDG_CONFIG_DIRS.

        List of directories separated by : (analogous to PATH).

        Should default to /etc/xdg.
        """
        return [Path(p) for p in os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg").split(":")]

    def as_dict(self):
        "Return all paths as a Dictionary."
        return {
            "cache_home": self.cache_home,
            "data_home": self.data_home,
            "config_home": self.config_home,
            "state_home": self.state_home,
            "runtime_dir": self.runtime_dir,
            "user_bin_dir": self.user_bin_dir,
            "data_dirs": self.data_dirs,
            "config_dirs": self.config_dirs,
        }
