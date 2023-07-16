#!/usr/bin/env python3

import re
import threading
from os.path import join, abspath, dirname, exists, basename
from utils import getoutput, get_config_dict, shell_exec, has_string_in_file, \
                  does_package_exist, is_package_installed, \
                  get_debian_version, get_firefox_version

DEFAULTLOCALE = 'en_US'


class LocaleInfo():
    def __init__(self):
        self.script_dir = abspath(dirname(__file__))
        cmd = "awk '/^[^#]/{print $3}' /usr/share/zoneinfo/zone.tab | sort -k3"
        self.timezones = getoutput(cmd)
        self.refresh()

        # Genereate locale files with the default locale if they do not exist
        if not exists('/etc/locale.gen'):
            shell_exec(f'echo "{DEFAULTLOCALE}.UTF-8 UTF-8" >> /etc/locale.gen')
            shell_exec("locale-gen")
        if self.default_locale == '':
            self.default_locale = DEFAULTLOCALE
            shell_exec("echo \"\" > /etc/default/locale")
            shell_exec(f'update-locale LANG="{self.default_locale}.UTF-8"')
            shell_exec(f'update-locale LANG={self.default_locale}.UTF-8')

    def list_timezones(self, continent=None):
        timezones = []
        for timezone in self.timezones:
            tz_lst = timezone.split('/')
            if tz_lst:
                if not continent:
                    # return continent only
                    if tz_lst[0] not in timezones:
                        timezones.append(tz_lst[0])
                else:
                    # return timezones of given continent
                    if tz_lst[0] == continent:
                        timezones.append('/'.join(tz_lst[1:]))
        return timezones

    def get_readable_language(self, locale):
        lan = ''
        lan_list = join(self.script_dir, 'languages.list')
        if exists(lan_list):
            cmd = f"grep '^{locale}' \"{lan_list}\" | awk -F'=' '{{print $2}}'"
            lan = getoutput(cmd)[0]
            if not lan:
                cmd = f"grep '^{locale.split('_')[0]}' \"{lan_list}\" | awk -F'[= ]' '{{print $2}}' | uniq"
                lan = getoutput(cmd)[0]
        return lan

    def refresh(self):
        self.locales = getoutput("awk -F'[@. ]' '/UTF-8/{print $1}' /usr/share/i18n/SUPPORTED | uniq")
        self.default_locale = getoutput("awk -F'[=.]' '/UTF-8/{print $2}' /etc/default/locale")[0]
        self.available_locales = getoutput("locale -a | grep '_' | awk -F'[@ .]' '{print $1}'")
        self.timezone_continents = self.list_timezones()
        tz = getoutput("cat /etc/timezone 2>/dev/null")[0]
        self.current_timezone_continent = dirname(tz)
        self.current_timezone = basename(tz)


class Localize(threading.Thread):
    # locales = [[install_bool, locale_string, language_string, default_bool]]
    def __init__(self, locales, timezone, queue=None):
        threading.Thread.__init__(self)

        self.locales = locales
        self.default_locale = ''
        self.delete_locale = ''
        for loc in locales:
            if loc[0] and loc[3]:
                self.default_locale = loc[1]
                break
        if not self.default_locale:
            self.default_locale = DEFAULTLOCALE
        self.timezone = timezone.strip()
        self.queue = queue
        self.user = getoutput("logname")[0]
        self.user_dir = f"/home/{self.user}"
        cmd = "awk -F'[=.]' '/UTF-8/{ print $2 }' /etc/default/locale"
        self.current_default = getoutput(cmd)[0]
        self.script_dir = abspath(dirname(__file__))
        self.edition = 'all'

        # Get configuration settings
        self.debian_version = get_debian_version()
        config = get_config_dict(join(self.script_dir, "solydxk-system.conf"))
        self.debian_frontend = f"DEBIAN_FRONTEND={config.get('DEBIAN_FRONTEND', 'noninteractive')}"
        self.apt_options = config.get('APT_OPTIONS_8', '')
        if self.debian_version == 0 or self.debian_version >= 9:
            self.apt_options = config.get('APT_OPTIONS_9', '')
        self.info = config.get('INFO', '/usr/share/solydxk/info')
        if exists(self.info):
            config = get_config_dict(self.info)
            self.edition = config.get('EDITION', 'all').replace(' ', '').lower()

        # Steps
        self.max_steps = 10
        self.current_step = 0

    def run(self):
        self.set_locale()
        self.queue_progress()
        shell_exec("apt-get update")
        self.applications()
        self.language_specific()

    def set_locale(self):
        print((f" --> Set locale {self.default_locale}"))
        self.queue_progress()
        # First, comment all languages
        shell_exec("sed -i -e '/^[a-z]/ s/^#*/# /' /etc/locale.gen")
        # Loop through all locales
        for loc in self.locales:
            if loc[0]:
                if has_string_in_file(loc[1], '/etc/locale.gen'):
                    # Uncomment the first occurence of the locale
                    lan = loc[1].replace('.', r'\.')
                    cmd = rf"sed -i '0,/^# *{lan}.UTF-8/{{s/^# *{lan}.UTF-8/{lan}.UTF-8/}}' /etc/locale.gen"
                    shell_exec(cmd)
                else:
                    # Add the locale
                    shell_exec(f'echo "{loc[1]}.UTF-8 UTF-8" >> /etc/locale.gen')

                # Save new default locale
                if loc[3]:
                    self.default_locale = loc[1]

        # Check if at least one locale is set
        locales = getoutput("awk -F'[@. ]' '{print $1}' < /etc/locale.gen | grep -v -E '^#|^$'")
        if locales[0] == '':
            shell_exec(f'echo "{self.default_locale}.UTF-8 UTF-8" >> /etc/locale.gen')

        cmd = f"echo '{self.timezone}' > /etc/timezone && " \
              f"rm /etc/localtime; ln -sf /usr/share/zoneinfo/{self.timezone} /etc/localtime && " \
              f"echo 'LANG={self.default_locale}.UTF-8' > /etc/default/locale && " \
              "dpkg-reconfigure --frontend=noninteractive locales && " \
              f"update-locale LANG={self.default_locale}.UTF-8"
        shell_exec(cmd)

        # Copy mo files for Grub if needed
        cmd = "mkdir -p /boot/grub/locale && " \
              "for F in $(find /usr/share/locale -name 'grub.mo'); do " \
              "MO=/boot/grub/locale/$(echo $F | cut -d'/' -f 5).mo; " \
              "cp -afuv $F $MO; done"
        shell_exec(cmd)

        # Cleanup old default grub settings
        default_grub = '/etc/default/grub'
        shell_exec(f"sed -i '/^# Set locale$/d' {default_grub} && " \
                   f"sed -i '/^LANG=/d' {default_grub} && " \
                   f"sed -i '/^LANGUAGE=/d' {default_grub} && " \
                   f"sed -i '/^GRUB_LANG=/d' {default_grub}")

        # Update Grub and make sure it uses the new locale
        shell_exec(f'LANG={self.default_locale}.UTF-8 update-grub')

        # Change user settings
        if exists(self.user_dir):
            if exists(join(self.user_dir, '.dmrc')):
                cmd = rf'sudo -H -u {self.user} bash -c "sed -i \'s/Language=.*/Language={self.default_locale}\.utf8/\' {self.user_dir}/.dmrc'
                shell_exec(cmd)
            cmd = f'sudo -H -u {self.user} bash -c "printf {self.default_locale} > {self.user_dir}/.config/user-dirs.locale"'
            shell_exec(cmd)
            cmd = f'find {self.user_dir} -type f -name "prefs.js" -not -path "*/extensions/*"'
            prefs = getoutput(cmd)
            for pref in prefs:
                self.localizePref(pref)

        self.current_default = self.default_locale

    def localizePref(self, prefs_path):
        if exists(prefs_path):
            with open(file=prefs_path, mode='r', encoding='utf-8') as prefs_fle:
                text = prefs_fle.read()

            prev_lan = self.current_default.split('_')[0]
            moz_prev_lan = self.current_default.replace('_', '-')
            lan = self.default_locale.split('_')[0]
            moz_lan = self.default_locale.replace('_', '-')
            if 'thunderbird' in prefs_path:
                ff_ver = 0
            else:
                ff_ver = get_firefox_version()

            # Set Mozilla parameters in prefs file
            moz_line = f'user_pref("spellchecker.dictionary", "{lan}");'
            pattern = r"^user_pref.*spellchecker\.dictionary.*"
            text = self.search_and_replace(text, pattern, moz_line, moz_line)

            moz_line = "user_pref(\"intl.locale.matchOS\", true);"
            pattern = r"^user_pref.*intl\.locale\.matchOS.*"
            text = self.search_and_replace(text, pattern, moz_line, moz_line)

            # Setting these is not needed because of matchOS=true but
            # it helps users if they want to manually change Mozilla's interface language into
            # something different than the OS's locale.
            if ff_ver < 59:
                moz_line = f'user_pref("general.useragent.locale", "{moz_lan}");'
                pattern = r"^user_pref.*general\.useragent\.locale.*"
                text = self.search_and_replace(text, pattern, moz_line, moz_line)
            else:
                # From FF version 59 a new variable is used
                moz_line = f'user_pref("intl.locale.requested", "{moz_lan}");'
                pattern = r"^user_pref.*intl\.locale\.requested.*"
                text = self.search_and_replace(text, pattern, moz_line, moz_line)

            # Change language of anything that is left
            text = self.search_and_replace(text, moz_prev_lan, moz_lan)
            text = self.search_and_replace(text, f'"{prev_lan}"', f'"{lan}"')
            text = self.search_and_replace(text, f'"{prev_lan.upper()}"', f'"{lan.upper()}"')

            with open(file=prefs_path, mode='w', encoding='utf-8') as prefs_fle:
                prefs_fle.write(text)

    def search_and_replace(self, text, regexp_search, replace_with_string, append_string=None):
        match = re.search(regexp_search, text, re.MULTILINE)
        if match:
            # We need the flags= or else the index of re.MULTILINE is passed
            text = re.sub(regexp_search, replace_with_string, text, flags=re.MULTILINE)
        else:
            if not append_string:
                text += f'\n{append_string}'
        return text

    def language_specific(self):
        localize_conf = join(self.script_dir, f'localize/{self.default_locale}')
        if exists(localize_conf):
            try:
                print((f' --> Localizing {self.edition}'))
                config = get_config_dict(localize_conf)
                packages = config.get(self.edition, '').strip()
                if packages:
                    self.queue_progress()
                    cmd = f'{self.debian_frontend} apt-get install {self.apt_options} {packages}'
                    shell_exec(cmd)
            except Exception as detail:
                msg = f'ERROR: {detail}'
                print(msg)

    def applications(self):
        for loc in self.locales:
            cmd_apt = f'{self.debian_frontend} apt-get install {self.apt_options}'
            locale = ''
            if loc[0]:
                locale = loc[1]
            if locale in ('en_US', ''):
                continue
            spellchecker = False
            # Localize KDE
            if is_package_installed("kde-runtime"):
                print((" --> Localizing KDE"))
                package = self.get_localized_package("kde-l10n", locale)
                if package:
                    self.queue_progress()
                    shell_exec(f'{cmd_apt} {package}')

            # Localize LibreOffice
            if is_package_installed("libreoffice"):
                print((" --> Localizing LibreOffice"))
                package = self.get_localized_package("libreoffice-l10n", locale)
                if package:
                    self.queue_progress()
                    shell_exec(f'{cmd_apt} libreoffice {package}')
                package = self.get_localized_package("libreoffice-help", locale)
                if package:
                    self.queue_progress()
                    shell_exec(f'{cmd_apt} {package}')
                if not spellchecker:
                    package = self.get_localized_package("hunspell", locale)
                    if package == '':
                        package = self.get_localized_package("myspell", locale)
                    if package:
                        spellchecker = True
                        self.queue_progress()
                        shell_exec(f'{cmd_apt} {package}')

            # Localize AbiWord
            if is_package_installed("abiword"):
                print((" --> Localizing AbiWord"))
                package = self.get_localized_package("aspell", locale)
                if package:
                    self.queue_progress()
                    shell_exec(f'{cmd_apt} {package}')

            # Localize Firefox
            firefox = "firefox"
            is_esr = is_package_installed("firefox-esr")
            if is_esr:
                firefox = "firefox-esr"
            if is_esr or is_package_installed("firefox"):
                esr = ""
                if is_esr:
                    esr = "esr-"
                print((" --> Localizing Firefox"))
                package = self.get_localized_package(f'firefox-{esr}l10n', locale)
                if package:
                    self.queue_progress()
                    shell_exec(f'{cmd_apt} {package} {firefox}')
                if not spellchecker:
                    package = self.get_localized_package("hunspell", locale)
                    if package == '':
                        package = self.get_localized_package("myspell", locale)
                    if package:
                        spellchecker = True
                        self.queue_progress()
                        shell_exec(f'{cmd_apt} {package}')

            # Localize Thunderbird
            if is_package_installed("thunderbird"):
                print((" --> Localizing Thunderbird"))
                package = self.get_localized_package("thunderbird-l10n", locale)
                if package:
                    self.queue_progress()
                    shell_exec(f'{cmd_apt} {package}')
                if not spellchecker:
                    package = self.get_localized_package("hunspell", locale)
                    if package == '':
                        package = self.get_localized_package("myspell", locale)
                    if package:
                        spellchecker = True
                        self.queue_progress()
                        shell_exec(f'{cmd_apt} {package}')

    def queue_progress(self):
        self.current_step += 1
        if self.current_step > self.max_steps:
            self.current_step = self.max_steps
        if self.queue:
            #print((">> step %d of %d" % (self.current_step, self.max_steps)))
            self.queue.put([self.max_steps, self.current_step])

    def get_localized_package(self, package, locale):
        language_list = locale.lower().split("_")
        lan = ''.join(language_list)
        pck = f'{package}-{lan}'
        if not does_package_exist(pck):
            lan = '-'.join(language_list)
            pck = f'{package}-{lan}'
            if not does_package_exist(pck):
                lan = language_list[0]
                pck = f'{package}-{lan}'
                if not does_package_exist(pck):
                    pck = ''
        return pck
