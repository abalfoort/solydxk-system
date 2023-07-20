#!/usr/bin/env python3

# http://wiki.debian.org/plymouth
# https://wiki.ubuntu.com/Plymouth

import re
from os.path import exists, isfile
from shutil import which
from utils import getoutput, shell_exec
from grub import Grub

# i18n: http://docs.python.org/3/library/gettext.html
import gettext
_ = gettext.translation('solydxk-system', fallback=True).gettext

# Handles general plymouth functions
class Plymouth():
    def __init__(self, logger_object=None):
        self.log = logger_object
        self.grub = Grub(self.log)
        self.avl_themes_search_str = '^plymouth-theme'
        try:
            self.set_theme_path = which('plymouth-set-default-theme')
        except:
            self.set_theme_path = None
        self.modules_path = '/etc/initramfs-tools/modules'

    # Get a list of installed Plymouth themes
    def installed_themes(self):
        if self.set_theme_path:
            cmd = f'{self.set_theme_path} --list'
            return getoutput(cmd)
        return []

    def is_plymouth_booted(self):
        cmdline = getoutput("cat /proc/cmdline")[0]
        if ' splash' in cmdline:
            return True

        # It could be that the user manually removed splash in Grub when booting
        # Check grub.cfg
        match = re.search(r'\/.*=[0-9a-z\-]+', cmdline)
        if match:
            if exists(self.grub.grub_cfg):
                grubcfg_splash = getoutput(f'grep "{match.group(0)}" "{self.grub.grub_cfg}" | grep " splash"')[0]
                if grubcfg_splash:
                    return True
        return False

    # Get the currently used Plymouth theme
    def current_theme(self):
        if not self.grub.has_splash():
            return None
        if self.set_theme_path and \
           self.is_plymouth_booted():
            return getoutput(self.set_theme_path)[0]
        return None

    # Get a list of Plymouth themes in the repositories that can be installed
    def available_themes(self):
        cmd = f'apt-cache pkgnames {self.avl_themes_search_str}'
        available_themes = getoutput(cmd)
        avl_themes = []

        for line in available_themes:
            match = re.search(f'{self.avl_themes_search_str}-([a-zA-Z0-9-]*)', line)
            if match:
                theme = match.group(1)
                if not 'all' in theme:
                    avl_themes.append(theme)

        return avl_themes

    def preview(self):
        try:
            cmd = "su -c 'plymouthd; plymouth --show-splash ; for ((I=0; I<10; I++)); do plymouth --update=test$I ; sleep 1; done; plymouth quit'"
            shell_exec(cmd)
        except Exception as detail:
            self.write_log(detail, 'exception')

    # Get the package name that can be uninstalled of a given Plymouth theme
    def removable_package_name(self, theme):
        cmd = f'dpkg -S {theme}.plymouth'
        package = None
        package_names = getoutput(cmd)

        for line in package_names:
            if self.avl_themes_search_str in line:
                match = re.search('(^.*):', line)
                if match:
                    package = match.group(1)
                    break
        self.write_log(f"Package found {package}")
        return package

    # Get valid package name of a Plymouth theme (does not have to exist in the repositories)
    def package_name(self, theme):
        return self.avl_themes_search_str + "-" + theme

    # Get current Plymouth resolution
    def current_resolution(self):
        return self.grub.resolution

    # Save theme
    def save(self, theme):
        if not self.set_theme_path:
            self.write_log('Plymouth not installed - exiting', 'warning')
            return

        modules_path = Plymouth().modules_path
        if not exists(modules_path):
            shell_exec(f"touch {modules_path}")

        # Cleanup
        shell_exec(f"sed -i -e 's/^ *//; s/ *$//' {modules_path}")
        shell_exec(f"sed -i -e '/^.*KMS$/d' {modules_path}")
        shell_exec(f"sed -i -e '/^intel_agp$/d' {modules_path}")
        shell_exec(f"sed -i -e '/^drm$/d' {modules_path}")
        shell_exec(f"sed -i -e '/^nouveau modeset.*/d' {modules_path}")
        shell_exec(f"sed -i -e '/^radeon modeset.*/d' {modules_path}")
        shell_exec(f"sed -i -e '/^i915 modeset.*/d' {modules_path}")
        shell_exec(rf"sed -i -e '/^uvesafb\s*mode_option.*/d' {modules_path}")

        # Set the theme and update initramfs
        if str(theme) != 'None':
            self.write_log(f"Set theme: {theme}")
            shell_exec(f"{self.set_theme_path} -R {theme}")

    def write_log(self, message, level='debug'):
        if self.log is not None:
            self.log.write(message, 'Plymouth', level)
