#!/usr/bin/env python3

# For debugging: print execution time per process
write_blame = False

from time import process_time
import os
import re
from os.path import exists, splitext, dirname, isdir, basename, join
from adjust_sources import Sources
from logger import Logger
from utils import getoutput,  get_apt_force,  get_package_version,  \
                  get_apt_cache_locked_program,  has_string_in_file,  \
                  get_debian_version,  can_copy, get_swap_device

# Init logging
log_file = "/var/log/solydxk-system.log"
log = Logger(log_file, addLogTime=True, maxSizeKB=5120)
log.write('=====================================', 'adjust')
log.write(">>> Start SolydXK Adjustment <<<", 'adjust')
log.write('=====================================', 'adjust')

# --force-yes is deprecated in stretch
force = get_apt_force()

# Fix some programs [package, what to fix, options (touch/mkdir|owner:group|permissions), exec from debian version (0 = all)]
fix_progs = [['login', '/var/log/btmp', 'touch|root:utmp|600', 0],
             ['login', '/var/log/lastlog', 'touch|root:utmp|664', 0],
             ['login', '/var/log/faillog', 'touch|root:utmp|664', 0],
             ['login', '/var/log/wtmp', 'touch|root:utmp|664', 0],
             ['apache2', '/var/log/apache2', 'mkdir|root:adm|755', 0],
             ['mysql-client', '/var/log/mysql', 'mkdir|mysql:adm|755', 0],
             ['clamav', '/var/log/clamav', 'mkdir|clamav:clamav|755', 0],
             ['clamav', '/var/log/clamav/freshclam.log', 'touch|clamav:clamav|644', 0],
             ['samba', '/var/log/samba', 'mkdir|root:adm|755', 0],
             ['consolekit', '/var/log/ConsoleKit', 'mkdir|root:root|755', 0],
             ['exim4-base', '/var/log/exim4', 'mkdir|Debian-exim:adm|755', 0],
             ['lightdm', '/var/lib/lightdm/data', 'mkdir|lightdm:lightdm|755', 0],
             ['usbguard', '/etc/usbguard/rules.conf', 'touch|root:root|600', 0]]
             #['v86d', 'v86d', 'purge', 0],
             #['lightdm', 'accountsservice', 'install', 0]]
             #['usb-creator', 'solydxk-usb-creator', 'purge', 0],
             #['solydk-system-adjustments-8', 'solydk-system-adjustments', 'purge', 0],
             #['solydx-system-adjustments-8', 'solydx-system-adjustments', 'purge', 0],
             #['solydk-system-adjustments-9', 'solydk-system-adjustments', 'purge', 0],
             #['solydx-system-adjustments-9', 'solydx-system-adjustments', 'purge', 0],
             #'firefox-solydxk-adjustments', 'firefox-esr-solydxk-adjustments', 'purge', 0]]
             
gtk_deprecated_properties = ['child-displacement', 
                             'scrollbars-within-bevel', 
                             'indicator-size', 
                             'GtkExpander-expander-size', 
                             'shadow-type']

t = process_time()
if write_blame: log.write("Blame start - {}".format(t), 'blame')

ver = get_debian_version()
for prog in fix_progs:
    if ver >= prog[3] or prog[3] == 0:
        if get_package_version(prog[0]) != '':
            options = prog[2].split('|')
            if options[0] == 'purge' or options[0] == 'install':
                if get_apt_cache_locked_program() == '':
                    os.system("apt-get {action} {opt} {pck}".format(action=options[0], opt=force, pck=prog[1]))
            elif options[0] == 'touch' and not exists(prog[1]):
                dir_name = dirname(prog[1])
                if not isdir(dir_name):
                    os.system("mkdir -p {dir}; chown {own} {dir}; chmod {perm} {dir}".format(dir=dir_name, own=options[1], perm=options[2]))
                os.system("touch {fle}; chown {own} {fle}; chmod  {perm} {fle}".format(fle=prog[1], own=options[1], perm=options[2]))
            elif options[0] == 'mkdir' and not isdir(prog[1]):
                os.system("mkdir -p {dir}; chown {own} {dir}; chmod {perm} {dir}".format(dir=prog[1], own=options[1], perm=options[2]))

if write_blame: log.write("Blame 01 - {}".format(process_time() - t), 'blame')

try:
    adjustment_directory = "/usr/share/solydxk/system-adjustments/"
    array_preserves = []
    overwrites = {}

    # Perform file execution adjustments
    for filename in sorted(os.listdir(adjustment_directory)):
        full_path = adjustment_directory + filename
        bn, extension = splitext(filename)
        if extension == ".execute":
            log.write("> Execute: %s" % full_path,  'execute')
            os.system("chmod a+rx %s" % full_path)
            os.system(full_path)
        elif extension == ".preserve":
            log.write("> Preserve: %s" % full_path,  'preserve')
            filehandle = open(full_path)
            for line in filehandle:
                line = line.strip()
                array_preserves.append(line)
            filehandle.close()
        elif extension == ".overwrite":
            log.write("> Overwrite: %s" % full_path,  'overwrite')
            filehandle = open(full_path)
            for line in filehandle:
                line = line.strip()
                line_items = line.split()
                if len(line_items) == 2:
                    source, destination = line.split()
                    if destination not in array_preserves:
                        overwrites[destination] = source
            filehandle.close()
            # Perform file overwriting adjustments
            for key in list(overwrites.keys()):
                source = overwrites[key]
                destination = key
                if exists(source):
                    if not "*" in destination:
                        # Simple destination, do a cp
                        if can_copy(source, destination):
                            os.system("cp " + source + " " + destination)
                            log.write("%s overwritten with %s" % (destination,  source),  'overwrite')
                    else:
                        # Wildcard destination, find all possible matching destinations
                        matching_destinations = getoutput("find " + destination)
                        matching_destinations = matching_destinations.split("\n")
                        for matching_destination in matching_destinations:
                            matching_destination = matching_destination.strip()
                            if can_copy(source, matching_destination):
                                os.system("cp " + source + " " + matching_destination)
                                log.write("%s overwritten with %s" % (matching_destination,  source),  'overwrite')
        elif extension == ".link":
            log.write("> Link: %s" % full_path)
            filehandle = open(full_path)
            for line in filehandle:
                line = line.strip()
                line_items = line.split()
                if len(line_items) == 2:
                    link, destination = line.split()
                    if destination not in array_preserves and \
                       exists(dirname(link)) and \
                       exists(destination):
                        os.system("ln -sf %s %s" % (destination ,  link))
                        log.write("link %s created to %s" % (link,  destination),  'link')

    if write_blame: log.write("Blame 02 - {}".format(process_time() - t), 'blame')

    # Remove resume file if no swap has been defined
    resume = '/etc/initramfs-tools/conf.d/resume'
    if get_swap_device():
        os.system("echo 'RESUME=auto' > %s" % resume)
    else:
        os.system("echo 'RESUME=none' > %s" % resume)
    
    if write_blame: log.write("Blame 03 - {}".format(process_time() - t), 'blame')

    # Restore LSB information
    with open('/usr/share/solydxk/info', 'r') as f:
        info = f.readlines()

    def get_info_line(par_name):
        matches = [match for match in info if par_name in match]
        return '' if not matches else matches[0]

    codename = get_info_line("CODENAME")
    release = get_info_line("RELEASE")
    distrib_id = get_info_line("DISTRIB_ID")
    description = get_info_line("DESCRIPTION")
    pretty_name = get_info_line("PRETTY_NAME")
    home_url = get_info_line("HOME_URL")
    support_url = get_info_line("SUPPORT_URL")
    bug_report_url = get_info_line("BUG_REPORT_URL")
    
    with open("/etc/lsb-release", "w") as f:
        f.writelines([distrib_id,
                      "DISTRIB_" + release,
                      "DISTRIB_" + codename,
                      "DISTRIB_" + description])
    log.write("/etc/lsb-release overwritten",  'lsb-release')

    with open("/usr/lib/os-release", "w") as f:
        f.writelines([pretty_name,
                      codename.replace("CODENAME", "NAME"),
                      release.replace("RELEASE", "VERSION_ID"),
                      distrib_id.replace("DISTRIB_ID", "ID"),
                      release.replace("RELEASE", "VERSION"),
                      codename.replace("CODENAME", "VERSION_CODENAME"),
                      home_url,
                      support_url,
                      bug_report_url])
    log.write("/usr/lib/os-release overwritten",  'os-release')

    if write_blame: log.write("Blame 04 - {}".format(process_time() - t), 'blame')

    # Restore /etc/issue and /etc/issue.net
    issue = description.replace("DESCRIPTION=", "").replace("\"", "")
    with open("/etc/issue", "w") as f:
        f.writelines(issue.strip() + " \\n \\l\n")
    log.write("/etc/issue overwritten",  'issue')
    with open("/etc/issue.net", "w") as f:
        f.writelines(issue)
    log.write("/etc/issue.net overwritten",  'issue')

    if write_blame: log.write("Blame 05 - {}".format(process_time() - t), 'blame')

    # Adapt bashrc
    bashrc = '/etc/skel/.bashrc'
    if exists(bashrc):
        # Force prompt colors in bashrc
        os.system("sed -i 's/#\s*force_color_prompt=.*/force_color_prompt=yes/' %s" % bashrc)
        os.system("sed -i 's/;31m/;34m/' %s" % bashrc)
        os.system("sed -i 's/;32m/;34m/' %s" % bashrc)
        os.system("sed -i 's/#\s*alias\s/alias /g' %s" % bashrc)
        # Source the solydxk info file
        if not has_string_in_file("/usr/share/solydxk/info",  bashrc):
            with open(bashrc, 'a') as f:
                f.write("\n# Source the SolydXK info file\n"
                        "if [ -f /usr/share/solydxk/info ]; then\n"
                        "  . /usr/share/solydxk/info\n"
                        "fi\n")
        # Set the environment variable for qt5ct
        if get_package_version('qt5ct') != '':
            if not has_string_in_file('QT_QPA_PLATFORMTHEME',  bashrc):
                with open(bashrc, 'a') as f:
                    f.write('\n# Set the environment variable for qt5ct\n'
                            'export QT_QPA_PLATFORMTHEME="qt5ct"\n')
        log.write("%s adapted" % bashrc,  'bashrc')

    if write_blame: log.write("Blame 06 - {}".format(process_time() - t), 'blame')

    # Check start menu favorite for either Firefox ESR or Firefox
    ff = getoutput("which firefox-esr")[0]
    if ff == "":
        ff = getoutput("which firefox")[0]
    if exists(ff):
        dt = "%s.desktop" % basename(ff)
        configs = ["/usr/share/solydxk/default-settings/kde4-profile/default/share/config/kickoffrc",
                   "/etc/xdg/kickoffrc",
                   "/etc/skel/.config/xfce4/panel/whiskermenu-9.rc",
                   "/usr/share/plasma/look-and-feel/org.kde.solydk.desktop/contents/layouts/org.kde.plasma.desktop.defaultPanel/contents/layout.js",
                   "/usr/share/plasma/look-and-feel/org.kde.solydk-dark.desktop/contents/layouts/org.kde.plasma.desktop.defaultPanel/contents/layout.js",
                   "/usr/share/solydxk/default-settings/plasma5-profile/kickoffrc"]
        for config in configs:
            if exists(config):
                if not has_string_in_file(dt,  config):
                    os.system("sed -i -e 's/firefox[a-z-]*.desktop/%s/' %s" % (dt, config))
        log.write("Start menu for Firefox adapted",  'firefox')

    if write_blame: log.write("Blame 07 - {}".format(process_time() - t), 'blame')

    # Change Mozilla widget theme for SolydX
    bx = '/usr/share/themes/Breeze-X'
    if exists(bx):
        configs = ['/usr/lib/firefox-esr/distribution/distribution.ini',
                   '/usr/lib/thunderbird/distribution/distribution.ini',
                   '/opt/waterfox/distribution/distribution.ini',
                   '/etc/skel/.thunderbird/user.default/user.js']
        for config in configs:
            if exists(config):
                os.system("sed -i 's/\"Breeze\"/\"Breeze-X\"/g' %s" % config)
        log.write("Mozilla configuration adapted",  'mozilla')

    # Add live menus in grub when needed
    grubsh = "/etc/grub.d/10_linux"
    livesh = "/usr/lib/solydxk/grub/boot-isos.sh"
    if exists(grubsh) and exists(livesh):
        if not has_string_in_file(livesh,  grubsh):
            escPath = livesh.replace('/', '\/')
            os.system("sed -i \"s/echo '}'/if [ -e %s ]; then \/bin\/bash %s; fi; echo '}'/\" %s" % (escPath, escPath, grubsh))
            log.write("%s adapted for live boot menu" % grubsh,  'boot-isos')

    if write_blame: log.write("Blame 08 - {}".format(process_time() - t), 'blame')

    # Fix gpg
    if exists('/etc/apt/trusted.gpg'):
        os.system('/bin/bash /usr/lib/solydxk/scripts/fix-gpg.sh')

    if write_blame: log.write("Blame 09 - {}".format(process_time() - t), 'blame')

    # Fix pulse audio always set volume to 100%
    pulse = '/etc/pulse/daemon.conf'
    if exists(pulse):
        os.system("sed -i '/^# Fix pulse/,/= no/d' {}".format(pulse))
        os.system("sed -i 's/.*flat-v.*lumes.*/flat-volumes = no/' {}".format(pulse))
    
    #Fix plop in audio for some intel chips
#    powersave = '/usr/lib/pm-utils/power.d/intel-audio-powersave'
#    if exists(powersave):
#        os.system("sed -i 's/^INTEL_AUDIO_POWERSAVE=${INTEL_AUDIO_POWERSAVE:-true}/#INTEL_AUDIO_POWERSAVE=${INTEL_AUDIO_POWERSAVE:-true}\\nINTEL_AUDIO_POWERSAVE=false/' %s" % powersave)
#    defaultpa = '/etc/pulse/default.pa'
#    if exists(defaultpa):
#        os.system("sed -i 's/^load-module module-suspend-on-idle/#load-module module-suspend-on-idle/' {}".format(defaultpa))

    # Fix Breeze Gtk warnings
    breezecsss = ['/usr/share/themes/Breeze/gtk-3.18/gtk.css', 
                  '/usr/share/themes/Breeze/gtk-3.20/gtk.css',
                  '/usr/share/themes/Breeze-Dark/gtk-3.18/gtk.css', 
                  '/usr/share/themes/Breeze-Dark/gtk-3.20/gtk.css']
    for css in breezecsss:
        if exists(css):
            os.system("sed -i 's/^ *-GtkButton-child-displacement.*/\/\*& \*\//' {}".format(css))
            os.system("sed -i 's/^ *-GtkScrolledWindow-scrollbars-within-bevel.*/\/\*& \*\//' {}".format(css))

    if write_blame: log.write("Blame 10 - {}".format(process_time() - t), 'blame')

    # Fix device notifiers for Plasma 5
    actions_k4 = '/usr/share/kde4/apps/solid/actions/'
    actions_p5 = '/usr/share/solid/actions/'
    if exists(actions_k4) and exists(actions_p5):
        for fle in os.listdir(actions_k4):
            if fle.endswith(".desktop"):
                link = join(actions_k4, fle)
                destination = join(actions_p5, fle)
                if not exists(destination):
                    os.system("ln -s %s %s" % (link, destination))
                    log.write("link %s created to %s" % (link,  destination),  'plasma5-notifier-fix')

    if write_blame: log.write("Blame 11 - {}".format(process_time() - t), 'blame')

    # Make sure sources.list is correct
    sources = Sources()
    sources.check()

    if write_blame: log.write("Blame 12 - {}".format(process_time() - t), 'blame')

    # Update cache
    os.system("update-desktop-database -q")
    # Recreate pixbuf cache
    pix_cache = '/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/gdk-pixbuf-query-loaders'
    if not exists(pix_cache):
        pix_cache = '/usr/lib/i386-linux-gnu/gdk-pixbuf-2.0/gdk-pixbuf-query-loaders'
    if exists(pix_cache):
        os.system("%s --update-cache" % pix_cache)

    if write_blame: log.write("Blame 13 - {}".format(process_time() - t), 'blame')

    # When on Raspbian
    raspi_config = '/usr/bin/raspi-config'
    if exists(raspi_config):
        os.system("sed -i 's/ pi / solydxk /g' %s" % raspi_config)
        os.system("sed -i 's/(pi)/(solydxk)/g' %s" % raspi_config)
        os.system("sed -i 's/=pi/=solydxk/g' %s" % raspi_config)
        with open(raspi_config, 'r') as f:
            if not '/boot/firmware' in f.read():
                os.system("sed -i 's/\/boot/\/boot\/firmware/g' %s" % raspi_config)

    if write_blame: log.write("Blame 14 - {}".format(process_time() - t), 'blame')

    # Fix Breeze themes by deleting lines with deprecated style properties from the gtk.css files
    gtk_files = ['/usr/share/themes/Breeze/gtk-3.0/gtk.css',
                 '/usr/share/themes/Breeze-Dark/gtk-3.0/gtk.css']
    for gtk in gtk_files:
        if exists(gtk):
            for property in gtk_deprecated_properties:
                os.system("sed -i '/%s/d' %s" % (property, gtk))

    tend = process_time()
    if write_blame: log.write("Blame end - {} ({})".format(tend - t, tend), 'blame')

except Exception as detail:
    print(detail)
    log.write(detail,  'adjust')
