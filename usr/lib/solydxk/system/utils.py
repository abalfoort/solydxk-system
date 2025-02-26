#!/usr/bin/env python3
""" General pupose functions """

import subprocess
from socket import timeout
from urllib.request import ProxyHandler, HTTPBasicAuthHandler, Request, \
    build_opener, HTTPHandler, install_opener, urlopen
from urllib.error import URLError, HTTPError
from random import choice
import re
import threading
import operator
import filecmp
import numbers
import socket
import pwd
from enum import Enum
from os import walk, listdir
from os.path import exists, isdir, expanduser,  splitext,  dirname, islink
from packaging.version import Version, InvalidVersion
import apt


# Debian testing uses names, not numbers
# Complement this dictionary with this URL:
# https://wiki.debian.org/DebianReleases
deb_name = {}
deb_name[15] = "duke"
deb_name[14] = "forky"
deb_name[13] = "trixie"
deb_name[12] = "bookworm"
deb_name[11] = "bullseye"
deb_name[10] = "buster"
deb_name[9] = "stretch"
deb_name[8] = "jessie"
deb_name[7] = "wheezy"
deb_name[6] = "squeeze"
deb_name[5] = "lenny"
deb_name[4] = "etch"


def shell_exec_popen(command, kwargs=None):
    """ Execute a command with Popen (returns the returncode attribute) """
    if not kwargs:
        kwargs = {}
    print((f"Executing: {command}"))
    # return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, **kwargs)
    return subprocess.Popen(command,
                            shell=True,
                            bufsize=0,
                            stdout=subprocess.PIPE,
                            universal_newlines=True,
                            **kwargs)


def shell_exec(command, wait=False):
    """ Execute a command (returns the returncode attribute) """
    print((f"Executing: {command}"))
    if wait:
        return subprocess.check_call(command, shell=True)
    return subprocess.call(command, shell=True)


def getoutput(command, timeout=None):
    """ Return command output (list) """
    try:
        output = subprocess.check_output(
            command, shell=True, timeout=timeout).decode('utf-8').strip().split('\n')
    except Exception as detail:
        print((f'getoutput exception: {detail}'))
        output = ['']
    return output


def chroot_exec(command, target):
    """ Excecute command in chroot """
    command = command.replace('"', "'").strip()  # FIXME
    return shell_exec(f'chroot {target}/ /bin/sh -c "{command}"')


def memoize(func):
    """ Caches expensive function calls.

    Use as:

        c = Cache(lambda arg: function_to_call_if_yet_uncached(arg))
        c('some_arg')  # returns evaluated result
        c('some_arg')  # returns *same* (non-evaluated) result

    or as a decorator:

        @memoize
        def some_expensive_function(args [, ...]):
            [...]

    See also: http://en.wikipedia.org/wiki/Memoization
    """
    class memodict(dict):
        def __call__(self, *args):
            return self[args]

        def __missing__(self, key):
            ret = self[key] = func(*key)
            return ret
    return memodict()


def get_config_dict(file, key_value=re.compile(r'^\s*(\w+)\s*=\s*["\']?(.*?)["\']?\s*(#.*)?$')):
    """Returns POSIX config file (key=value, no sections) as dict.
    Assumptions: no multiline values, no value contains '#'. """
    conf_dict = {}
    with open(file=file, mode='r', encoding='utf-8') as conf_fle:
        for line in conf_fle.readlines():
            try:
                key, value, _ = key_value.match(line).groups()
            except AttributeError:
                continue
            conf_dict[key] = value
    return conf_dict


def has_internet_connection(hostname=None):
    """ Check for internet connection """
    # Taken from https://stackoverflow.com/questions/20913411/test-if-an-internet-connection-is-present-in-python
    if not hostname:
        hostname = 'solydxk.com'
    try:
        # See if we can resolve the host name - tells us if there is
        # A DNS listening
        host = socket.gethostbyname(hostname)
        # Connect to the host - tells us if the host is actually reachable
        s = socket.create_connection((host, 80), 2)
        s.close()
        return True
    except Exception:
        pass # We ignore any errors, returning False
    return False


def get_value_from_url(url, timeout_secs=5, return_errors=False):
    """ Get returned value from a URL """
    try:
        # http://www.webuseragents.com/my-user-agent
        user_agents = [
            'Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
        ]

        # Create proxy handler
        proxy = ProxyHandler({})
        auth = HTTPBasicAuthHandler()
        opener = build_opener(proxy, auth, HTTPHandler)
        install_opener(opener)

        # Create a request object with given url
        req = Request(url)

        # Get a random user agent and add that to the request object
        user_agent = choice(user_agents)
        req.add_header('User-Agent', user_agent)

        # Get the output of the URL
        output = urlopen(req, timeout=timeout_secs)

        # Decode to text
        txt = output.read().decode('utf-8')

        # Return the text
        return txt

    except (HTTPError, URLError) as error:
        err = f'ERROR: could not connect to {url}: {error}'
        if return_errors:
            return err
        print((err))
        return None
    except timeout:
        err = f'ERROR: socket timeout on: {url}'
        if return_errors:
            return err
        print((err))
        return None


def in_virtual_box():
    """ Check if running in virtual box """
    virtual_box = 'VirtualBox'
    dmi_bios_version = getoutput(
        f"grep '{virtual_box}' /sys/devices/virtual/dmi/id/bios_version")
    dmi_system_product = getoutput(
        f"grep '{virtual_box}' /sys/devices/virtual/dmi/id/product_name")
    dmi_board_product = getoutput(
        f"grep '{virtual_box}' /sys/devices/virtual/dmi/id/board_name")
    if virtual_box not in dmi_bios_version and \
       virtual_box not in dmi_system_product and \
       virtual_box not in dmi_board_product:
        return False
    return True


def is_amd64():
    """ Check if is 64-bit system """
    machine = getoutput("uname -m")[0]
    if machine == "x86_64":
        return True
    return False


def is_xfce_running():
    """ Check if xfce is running """
    xfce = getoutput('pidof xfce4-session')[0]
    if xfce:
        return True
    return False


class VersionComparison(Enum):
    """ Return enum for compare_package_versions """
    INVALID = 1
    EQUAL = 2
    SMALLER = 3
    LARGER = 4

def compare_package_versions(package_version_1, package_version_2):
    """ Compare two package version strings """
    try:
        if Version(package_version_1) < Version(package_version_2):
            return VersionComparison.SMALLER
        elif Version(package_version_1) > Version(package_version_2):
            return VersionComparison.LARGER
        elif Version(package_version_1) == Version(package_version_2):
            return VersionComparison.EQUAL
    except InvalidVersion:
        return VersionComparison.INVALID


def does_package_exist(package_name):
    """ Check if a package exists """
    try:
        return bool(apt.Cache()[package_name])
    except KeyError:
        return False


def is_package_installed(package_name):
    """ Check if a package is installed """
    try:
        return apt.Cache()[package_name].is_installed
    except KeyError:
        return False


def get_package_version(package_name, candidate=False):
    """ Get package version (default=installed) """
    if not does_package_exist(package_name=package_name):
        return ''
    if candidate:
        return apt.Cache()[package_name].candidate.version
    return apt.Cache()[package_name].installed.version


def validate_package_version(package_name, min_package_version):
    """ Validate the installed package version with a minimum version number """
    installed_version = get_package_version(package_name=package_name)
    if Version(installed_version) >= Version(min_package_version):
        return True
    return False


def has_newer_in_backports(package_name, backports_repository):
    """ Check if a package has a newer version in backports """
    # https://apt-team.pages.debian.net/python-apt/library/apt.package.html
    # Command: f"apt-cache madison {package_name} | grep {backports_repository}")
    installed_version = get_package_version(package_name=package_name)
    if not installed_version:
        return False
    for version in apt.Cache()[package_name].versions:
        for origin in version.origins:
            if backports_repository in origin.archive:
                if Version(version.version) > Version(installed_version):
                    return True
    return False


def get_system_version_info():
    """ Get system version information """
    info = ''
    try:
        info_list = getoutput('cat /proc/version')
        if info_list:
            info = info_list[0]
    except Exception as detail:
        print((detail))
    return info


def get_current_resolution():
    """ Return current screen resolution """
    res = getoutput("xrandr 2>/dev/null | awk '/*/{print $1}'")[0]
    if not res:
        res = getoutput("xdpyinfo 2>/dev/null | awk '/dimensions/{print $2}'")[0]
    return res


def get_resolutions(min_res='', max_res='', reverse_order=False, use_vesa=False):
    """ Get valid screen resolutions """
    resolutions = ['']
    default_res = ['640x480', '800x600', '1024x768', '1280x1024']

    if use_vesa:
        vbe_modes = '/sys/bus/platform/drivers/uvesafb/uvesafb.0/vbe_modes'
        if exists(vbe_modes):
            resolutions = getoutput(f"cat {vbe_modes} | cut -d'-' -f1", 5)
        elif is_package_installed('hwinfo'):
            resolutions = getoutput(
                r"hwinfo --framebuffer | awk '/[0-9]+x[0-9]+\s/{print $3}'", 5)
    else:
        resolutions = getoutput(
            r"xrandr 2>/dev/null | awk '/[0-9]+x[0-9]+\s/{print $1}'", 5)

    if not resolutions[0]:
        # Add current resolution and set that as maximum
        max_res = get_current_resolution()
        default_res.append(max_res)
        resolutions = default_res

    # Remove any duplicates from the list
    res_list = list(set(resolutions))

    avl_res = []
    avl_res_tmp = []
    min_width = 0
    min_height = 0
    max_width = 0
    max_height = 0

    # Split the minimum and maximum resolutions
    if 'x' in min_res:
        min_res_list = min_res.split('x')
        min_width = str_to_nr(min_res_list[0])
        min_height = str_to_nr(min_res_list[1])
    if 'x' in max_res:
        max_res_list = max_res.split('x')
        max_width = str_to_nr(max_res_list[0])
        max_height = str_to_nr(max_res_list[1])

    # Fill the list with screen resolutions
    for line in res_list:
        for item in line.split():
            item_chk = re.search(r'\d+x\d+', line)
            if item_chk:
                item_list = item.split('x')
                item_width = str_to_nr(item_list[0])
                item_height = str_to_nr(item_list[1])
                # Check if it can be added
                if (item_width >= min_width and item_height >= min_height) and \
                   (max_width == 0 and max_height == 0 or (max_width > 0 and max_height > 0 and item_width <= max_width and item_height <= max_height)):
                    print((f"Resolution added: {item}"))
                    avl_res_tmp.append([item_width, item_height])

    # Sort the list and return as readable resolution strings
    avl_res_tmp.sort(key=operator.itemgetter(0), reverse=reverse_order)
    for res in avl_res_tmp:
        avl_res.append(str(res[0]) + 'x' + str(res[1]))
    return avl_res


def get_current_aspect_ratio():
    """ Return screen aspect ratio """
    return get_resolution_aspect_ratio(get_current_resolution())


def get_resolution_aspect_ratio(resolution_string):
    """ Get the aspect ratio from a screen resolution """
    res = resolution_string.split('x')
    if len(res) != 2:
        return ''

    res_width = str_to_nr(res[0])
    res_height = str_to_nr(res[1])

    if res_width <= 0 or res_height <= 0:
        return ''

    width = res_width
    height = res_height
    res_tuple = (res_width, res_height)
    remainder = 0
    hcf = 1

    if res_width < res_height:
        (height, width) = res_tuple

    while True:
        remainder = width % height
        if remainder == 0:
            hcf = height
            break
        width = height
        height = remainder

    # Return aspect ratio string
    return f"{int(res_width / hcf)}:{int(res_height / hcf)}"


def get_resolutions_with_aspect_ratio(aspect_ratio_string, use_vesa=False):
    """ Get screen resolution with aspect ratio """
    ret_arr = []
    resolutions = get_resolutions(use_vesa=use_vesa)
    for res in resolutions:
        aspect_ration = get_resolution_aspect_ratio(res)
        if aspect_ration == aspect_ratio_string:
            ret_arr.append(res)
    return ret_arr


def human_size(nkbytes):
    """ Return human readable string from number of kilobytes """
    suffixes = ['KB', 'MB', 'GB', 'TB', 'PB']
    nkbytes = float(nkbytes)
    if nkbytes == 0:
        return '0 B'
    i = 0
    while nkbytes >= 1024 and i < len(suffixes) - 1:
        nkbytes /= 1024.
        i += 1
    format_string = f'{nkbytes:.2f}'.rstrip('0').rstrip('.')
    return f'{format_string} {suffixes[i]}'


def can_copy(file1, file2):
    """ Check if a file can be copied to destination """
    ret = False
    if exists(file1):
        if exists(file2) and not islink(file2):
            if not filecmp.cmp(file1, file2):
                ret = True
        else:
            if "desktop" not in splitext(file2)[1]:
                if exists(dirname(file2)):
                    ret = True
    return ret


def str_to_nr(value):
    """ Convert string to number """
    if isinstance(value, numbers.Number):
        # Already numeric
        return value

    number = None
    try:
        number = int(value)
    except ValueError:
        try:
            number = float(value)
        except ValueError:
            number = None
    return number


def is_numeric(value):
    """ Check if value is a number """
    return bool(str_to_nr(value))


def has_string_in_file(search_string, file_path):
    """ Check for string in file """
    if exists(file_path):
        matched = re.compile(search_string, re.MULTILINE).search
        with open(file=file_path, mode='r', encoding='utf-8') as target_fle:
            if matched(target_fle.read()):
                return True
    return False


def is_running_live():
    """ Is the system a live system """
    live_dirs = ['/live', '/lib/live/mount', '/rofs']
    for live_dir in live_dirs:
        if exists(live_dir):
            return True
    return False


def get_process_pids(process_name, process_argument=None, fuzzy=False):
    """ Return process ids for process name """
    if fuzzy:
        args = ''
        if process_argument is not None:
            args = f"| grep '{process_argument}'"
        cmd = f"ps -ef | grep -v grep | grep '{process_name}' {args} | awk '{{print $2}}'"
        # print(cmd)
        pids = getoutput(cmd)
    else:
        pids = getoutput(f"pidof {process_name}")
    return pids


def is_process_running(process_name, process_argument=None, fuzzy=False):
    """ Check if porcess name is running """
    pids = get_process_pids(process_name, process_argument, fuzzy)
    if pids[0] != '':
        return True
    return False


def get_apt_force():
    """ Return the apt force string """
    # --force-yes is deprecated in stretch
    force = '--force-yes'
    ver = get_debian_version()
    if ver >= 9:
        force = '--allow-downgrades --allow-remove-essential --allow-change-held-packages'
    force += ' --yes -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold'
    return force


def get_apt_cache_locked_program():
    """ Return the program that is locking apt cache """
    apt_packages = ["dpkg", "apt-get", "synaptic", "adept", "adept-notifier"]
    proc_lst = getoutput("ps -U root -u root -o comm=")
    for apt_proc in apt_packages:
        if apt_proc in proc_lst:
            return apt_proc
    return ''


def get_installed_file_path(file_name):
    """ Return the program that is locking apt cache """
    if not file_name:
        return ''
    return getoutput(f"dpkg -S {file_name} | awk '{{print $NF;}}'")[0]


def get_debian_name():
    """ Return the debian system name """
    try:
        ver = get_debian_version()
        return deb_name[ver]
    except Exception:
        return ''


def get_debian_version():
    """ Get Debian's version number (float) """
    version = 0
    if exists('/etc/debian_version'):
        cmd = "grep -oP '^[a-z0-9]+' /etc/debian_version"
        version = str_to_nr(getoutput(cmd)[0].strip())
    if not version:
        cmd = "grep -Ei 'version=|version_id=|release=' /etc/*release | grep -oP '[0-9]+'"
        versions = getoutput(cmd)
        for version in versions:
            if is_numeric(version):
                version = str_to_nr(version)
                break
    return version


def get_firefox_version():
    """ Return Firefox version """
    firefox = "firefox"
    if is_package_installed("firefox-esr"):
        firefox = "firefox-esr"
    cmd = f"{firefox} --version 2>/dev/null | egrep -o '[0-9]{2,}' || echo 0"
    return str_to_nr(getoutput(cmd)[0])


def comment_line(file_path, pattern, comment=True):
    """ Comment or uncomment a line with given pattern in a file """
    if exists(file_path):
        pattern = pattern.replace("/", r"\/")
        cmd = f"sed -i '/{pattern}/s/^/#/' {file_path}"
        if not comment:
            cmd = rf"sed -i '/^#.*{pattern}/s/^#//' {file_path}"
        shell_exec(cmd)


def replace_pattern_in_file(pattern, replace_string, file, append_if_not_exists=True):
    """ Replace a given pattern in file """
    if exists(file):
        cont = None
        p_obj = re.compile(pattern, re.MULTILINE)
        with open(file=file, mode='r', encoding='utf-8') as target_fle:
            cont = target_fle.read()
        if re.search(p_obj, cont):
            cont = re.sub(p_obj, replace_string, cont)
        else:
            if append_if_not_exists:
                cont = cont + "\n" + replace_string + "\n"
            else:
                cont = None
        if cont:
            with open(file=file, mode='w', encoding='utf-8') as target_fle:
                target_fle.write(cont)

def get_nr_files_in_dir(path, recursive=True):
    """ Return number of files in path """
    total = 0
    if isdir(path):
        # return str_to_nr(getoutput("find %s -type f | wc -l" % path)[0])
        if recursive:
            for root, directories, filenames in walk(path):
                total += len(filenames)
        else:
            total = len(listdir(path))
    return total


def get_logged_user():
    """ Get user name """
    p = os.popen("logname", 'r')
    user_name = p.readline().strip()
    p.close()
    if user_name == "":
        user_name = pwd.getpwuid(os.getuid()).pw_name
    return user_name


def get_user_home():
    """ Return the user home path """
    return expanduser(f"~{get_logged_user()}")


def has_grub(path):
    """ Return if path (device or partition) has grub installed """
    cmd = f"dd bs=512 count=1 if={path} 2>/dev/null | strings"
    out = ' '.join(getoutput(cmd)).upper()
    if "GRUB" in out:
        print((f"Grub installed on {path}"))
        return True
    return False


def get_uuid(partition_path):
    """ Return UUID of partition """
    return getoutput(f"blkid -o value -s UUID {partition_path}")[0]


def get_mount_points(partition_path):
    """ Return mount points of partition (list) """
    out = getoutput(f"lsblk -o MOUNTPOINT -n {partition_path} | grep -v '^$'")
    return out if out[0] else []


def get_filesystem(partition_path):
    """ Return file system of partition """
    return getoutput(f"blkid -o value -s TYPE {partition_path}")[0]


def get_device_from_uuid(uuid):
    """ Return device from UUID """
    uuid = uuid.replace('UUID=', '')
    return getoutput(f"blkid -U {uuid}")[0]


def get_label(partition_path):
    """ Return label of partition """
    return getoutput(f"blkid -o value -s LABEL {partition_path}")[0]


def get_swap_device():
    """ Return the swap device """
    return getoutput("grep '/' /proc/swaps | awk '{print $1}'")[0]

def has_value_in_multi_array(value, multi_array, index=None):
    """ Check if value exist in multi-dimensional array """
    if not index:
        return any(value in x for x in multi_array)
    for lst in multi_array:
        try:
            if value == lst[index]: return True
        except Exception:
            return False
    return False

def _ratio_devider(width, height):
    if height == 0:
        return width
    return _ratio_devider(height, width % height)

def aspect_ratio(width, height):
    """ Get screen aspect ratio, e.g.: '16:9' """
    try:
        ratio_devider = _ratio_devider(width, height)
        return f'{int(width / ratio_devider)}:{int(height / ratio_devider)}'
    except Exception:
        return None

class ExecuteThreadedCommands(threading.Thread):
    """ Class to run commands in a thread and return the output in a queue """

    def __init__(self, commandList, queue=None, return_output=False):
        threading.Thread.__init__(self)

        self._commands = commandList
        self._queue = queue
        self._return_output = return_output

    def run(self):
        if isinstance(self._commands, (list, tuple)):
            for cmd in self._commands:
                self.exec_cmd(cmd)
        else:
            self.exec_cmd(self._commands)

    def exec_cmd(self, cmd):
        """ Execute a given command """
        if self._return_output:
            ret = getoutput(cmd)
        else:
            ret = shell_exec(cmd)
        if self._queue is not None:
            self._queue.put(ret)


class ExecuteThreadedFunction(threading.Thread):
    """ Class to run a function in a thread and return the output in a queue """

    def __init__(self, target, queue=None, *args):
        threading.Thread.__init__(self)

        self._target = target
        self._args = args
        self._queue = queue

    def run(self):
        out = self._target(*self._args)
        if self._queue is not None:
            self._queue.put(out)
