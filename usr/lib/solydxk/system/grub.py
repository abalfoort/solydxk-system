#!/usr/bin/env python3

import re
import os
from utils import shell_exec, replace_pattern_in_file

# i18n: http://docs.python.org/3/library/gettext.html
import gettext
_ = gettext.translation('solydxk-system', fallback=True).gettext


# Handles general plymouth functions
class Grub():
    def __init__(self, logger_object=None):
        self.log = logger_object
        self.grub_default = '/etc/default/grub' if os.path.isfile('/etc/default/grub') else None
        self.grub_cfg = '/boot/grub/grub.cfg' if os.path.isfile('/boot/grub/grub.cfg') else None
        self.installed_themes = self._installed_themes()
        self.resolution = self._current_resolution()
        self.theme = self._current_theme()
        self.grub_default_lines = []
        with open(file=self.grub_default, mode='r', encoding='utf-8') as grub_fle:
            self.grub_default_lines = grub_fle.read().splitlines()

    def _grub_default_value(self, pattern, group_nr=0):
        if not self.grub_default:
            self.write_log("Grub configuration file not found", 'warning')
            return None

        lines = []
        with open(file=self.grub_default, mode='r', encoding='utf-8') as grub_fle:
            lines = grub_fle.read().splitlines()
        for line in lines:
            # Search text for resolution
            match = re.search(pattern, line)
            if match:
                return match.group(group_nr).strip()
        return None

    def _installed_themes(self):
        themes = []
        for theme_dir in ['/usr/share/grub/themes', '/boot/grub/themes']:
            if not os.path.exists(theme_dir):
                continue

            for theme in set(next(os.walk(theme_dir))[1]):
                theme_path = os.path.join(theme_dir, theme + "/theme.txt")
                if os.path.exists(theme_path):
                    themes.append(theme_path)
        themes.sort()
        return themes

    # Get current Grub resolution
    def _current_resolution(self):
        resolution = self._grub_default_value(r'^GRUB_GFXMODE\s*=[\s"]*([0-9]+x[0-9]+)', 1)
        self.write_log(f"Current grub resolution: {resolution}")
        return resolution

    def _current_theme(self):
        theme = self._grub_default_value(r'^GRUB_THEME\s*=(.*)', 1)
        if os.path.exists(str(theme)):
            self.write_log(f"Current grub theme: {theme}")
            return theme
        return None

    def theme_name(self, theme_path):
        return os.path.basename(os.path.dirname(theme_path))

    def theme_path(self, theme_name):
        for theme in self.installed_themes:
            if theme_name in theme:
                return theme
        return None

    def has_splash(self):
        splash = self._grub_default_value(r'^GRUB_CMDLINE_LINUX_DEFAULT=.*[\s"](splash)[\s"]', 1)
        if splash:
            self.write_log("Splash is configured in Grub")
            return True
        self.write_log("Splash is NOT configured in Grub")
        return False

    # Save given grub resolution
    def save(self, theme=None, resolution=None, splash=True):
        if self.grub_default:
            theme_path = self.theme_path(theme) if not '/' in theme else theme
            if os.path.exists(str(theme_path)):
                replace_pattern_in_file(r'^#?GRUB_THEME\s*=.*',
                                        f'GRUB_THEME={theme_path}',
                                        self.grub_default)
                self.write_log(f'Grub theme set: {theme_path}')
            else:
                replace_pattern_in_file(r'^GRUB_THEME\s*=',
                                        '#GRUB_THEME=',
                                        self.grub_default,
                                        False)
                self.write_log('Grub theme disabled')
                resolution = None

            if resolution:
                replace_pattern_in_file(r'^#?GRUB_GFXMODE\s*=.*',
                                        f'GRUB_GFXMODE={resolution},auto',
                                        self.grub_default)
                replace_pattern_in_file(r'^#?GRUB_GFXPAYLOAD_LINUX\s*=.*',
                                        'GRUB_GFXPAYLOAD_LINUX=keep',
                                        self.grub_default)
                self.write_log(f'Grub resolution set: {resolution}')
            else:
                replace_pattern_in_file(r'^GRUB_GFXMODE\s*=',
                                        '#GRUB_GFXMODE=',
                                        self.grub_default,
                                        False)
                replace_pattern_in_file(r'^GRUB_GFXPAYLOAD_LINUX\s*=',
                                        '#GRUB_GFXPAYLOAD_LINUX=',
                                        self.grub_default,
                                        False)
                self.write_log('Grub resolution disabled')

            replace_pattern_in_file(r'\s*[no]*splash', '', self.grub_default)
            if splash:
                cmd = f"sed -i -e '/^GRUB_CMDLINE_LINUX_DEFAULT=/ s/\"$/ splash\"/' {self.grub_default}"
                shell_exec(cmd)
            else:
                cmd = f"sed -i -e '/^GRUB_CMDLINE_LINUX_DEFAULT=/ s/\"$/ nosplash\"/' {self.grub_default}"
                shell_exec(cmd)

            shell_exec('update-grub')

    def write_log(self, message, level='debug'):
        if self.log:
            self.log.write(message, 'Grub', level)
