""" Module to adjust general SolydXK settings """

#!/usr/bin/env python3

import os
from os.path import exists, dirname, isdir
from utils import get_apt_force, is_package_installed,  \
    get_apt_cache_locked_program, get_debian_version

# --force-yes is deprecated in stretch
APT_FORCE = get_apt_force()

# Fix some programs [package, what to fix, options (touch/mkdir/purge/install|owner:group|permissions), exec from debian version (0 = all)]
fix_progs = [['login', '/var/log/btmp', 'touch|root:utmp|600', 0],
             ['login', '/var/log/lastlog', 'touch|root:utmp|664', 0],
             ['login', '/var/log/faillog', 'touch|root:utmp|664', 0],
             ['login', '/var/log/wtmp', 'touch|root:utmp|664', 0],
             ['apache2', '/var/log/apache2', 'mkdir|root:adm|755', 0],
             ['mysql-client', '/var/log/mysql', 'mkdir|mysql:adm|755', 0],
             ['clamav', '/var/log/clamav', 'mkdir|clamav:clamav|755', 0],
             ['clamav', '/var/log/clamav/freshclam.log',
                 'touch|clamav:clamav|644', 0],
             ['samba', '/var/log/samba', 'mkdir|root:adm|755', 0],
             ['consolekit', '/var/log/ConsoleKit', 'mkdir|root:root|755', 0],
             ['exim4-base', '/var/log/exim4', 'mkdir|Debian-exim:adm|755', 0],
             ['lightdm', '/var/lib/lightdm/data', 'mkdir|lightdm:lightdm|755', 0],
             ['usbguard', '/etc/usbguard/rules.conf', 'touch|root:root|600', 0]]

try:
    ver = get_debian_version()
    for prog in fix_progs:
        if ver >= prog[3] or prog[3] == 0:
            if is_package_installed(prog[0]):
                options = prog[2].split('|')
                if options[0] == 'purge' or options[0] == 'install':
                    if not get_apt_cache_locked_program():
                        os.system(
                            f"apt-get {options[0]} {APT_FORCE} {prog[1]}")
                elif options[0] == 'touch' and not exists(prog[1]):
                    dir_name = dirname(prog[1])
                    if not isdir(dir_name):
                        os.system(
                            f"mkdir -p {dir_name}; chown {options[1]} {dir_name}; chmod {options[2]} {dir_name}")
                    os.system(
                        f"touch {prog[1]}; chown {options[1]} {prog[1]}; chmod  {options[2]} {prog[1]}")
                elif options[0] == 'mkdir' and not isdir(prog[1]):
                    os.system(
                        f"mkdir -p {prog[1]}; chown {options[1]} {prog[1]}; chmod {options[2]} {prog[1]}")
except Exception as detail:
    print(detail)

def get_info_line(par_name):
    """ Return the info per line """
    matches = [match for match in info if par_name in match]
    return '' if not matches else matches[0]

if exists('/usr/share/solydxk/info'):
    with open(file='/usr/share/solydxk/info', mode='r', encoding='utf-8') as f:
        info = f.readlines()

    codename = get_info_line("CODENAME")
    release = get_info_line("RELEASE")
    distrib_id = get_info_line("DISTRIB_ID")
    description = get_info_line("DESCRIPTION")
    pretty_name = get_info_line("PRETTY_NAME")
    home_url = get_info_line("HOME_URL")
    support_url = get_info_line("SUPPORT_URL")
    bug_report_url = get_info_line("BUG_REPORT_URL")

    try:
        # Restore LSB information
        with open(file="/etc/lsb-release", mode="w", encoding="utf-8") as f:
            f.writelines([distrib_id,
                        "DISTRIB_" + release,
                        "DISTRIB_" + codename,
                        "DISTRIB_" + description])
    except Exception as detail:
        print(detail)

    try:
        with open(file="/usr/lib/os-release", mode="w", encoding="utf-8") as f:
            f.writelines([pretty_name,
                        codename.replace("CODENAME", "NAME"),
                        release.replace("RELEASE", "VERSION_ID"),
                        distrib_id.replace("DISTRIB_ID", "ID"),
                        release.replace("RELEASE", "VERSION"),
                        codename.replace("CODENAME", "VERSION_CODENAME"),
                        home_url,
                        support_url,
                        bug_report_url])
    except Exception as detail:
        print(detail)

    try:
        # Restore /etc/issue and /etc/issue.net
        issue = description.replace("DESCRIPTION=", "").replace("\"", "")
        with open(file="/etc/issue", mode="w", encoding="utf-8") as f:
            f.writelines(issue.strip() + " \\n \\l\n")
        with open(file="/etc/issue.net", mode="w", encoding="utf-8") as f:
            f.writelines(issue)
    except Exception as detail:
        print(detail)
