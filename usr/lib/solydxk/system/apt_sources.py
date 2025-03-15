#!/usr/bin/env python3
"""Classes to handle apt:
    FilteredSourcesList: Used by Apt class - creates a list with debian and solydxk source entries.
    Apt: main apt class
"""

import re
from copy import deepcopy
from os.path import join, abspath, dirname, exists, basename
from utils import get_config_dict, get_value_from_url, getoutput, \
                  get_installed_file_path, validate_package_version

# https://apt-team.pages.debian.net/python-apt/library/aptsources.sourceslist.html
from aptsources.sourceslist import SourcesList, SourceEntry
# Deb822SourceEntry is only available on systems that already support the deb822 .sources format
try:
    from aptsources.sourceslist import Deb822SourceEntry
    # python-apt can be ready for deb822, but apt not
    DEB822 = validate_package_version(package_name='apt', min_package_version='2.9.29')
except ImportError:
    DEB822 = False

# Get all supported architectures
# Used as default if no architectures are provided
def __list_supported_architectures():
    arch = getoutput(command='dpkg --print-architecture')
    arch += getoutput(command='dpkg --print-foreign-architectures')
    return arch
SUPPORTED_ARCHS = __list_supported_architectures()


class FilteredSourcesList(SourcesList):
    """Filtered SourcesList: only allow debian and solydxk sources"""
    def __init__(self):
        SourcesList.__init__(self)
        self.__include_repos = ['debian', 'solydxk']
        self.list = self.__filtered_sources_list()

    def __filtered_sources_list(self):
        filtered_list = []
        sources_list = SourcesList(deb822=DEB822).list
        for source_entry in sources_list:
            # SourcesList appears to return empty lines and comments as well
            if source_entry.type not in ['deb', 'deb-src']:
                continue

            # Only save repos that are listed in self.include_repos
            if not any(x in source_entry.uri for x in self.__include_repos):
                continue

            # If not provided, set the supported architectures
            if not source_entry.architectures:
                source_entry.architectures = SUPPORTED_ARCHS

            filtered_list.append(source_entry)
        return filtered_list

class Apt():
    """Apt class"""
    def __init__(self):
        self.distro_comps = {'debian':
                                ['main',
                                'contrib',
                                'non-free',
                                'non-free-firmware'],
                            'solydxk':
                                ['main',
                                'upstream',
                                'import']
                            }

        self.__keyrings = {'debian': 'debian-archive-keyring.gpg',
                           'solydxk': 'solydxk-archive-keyring.gpg'}

        self.__apt_sources = self.__save_apt_sources()

    def __save_apt_sources(self):
        """Save all apt sources data

        Returns:
            list[dict]: [{source, signed-by}]
        """
        apt_sources = []
        sources_list = FilteredSourcesList().list

        for source_entry in sources_list:
            # Save source_entry in dict and add signed-by which is not in source_entry
            # org-entry is used to save the original entry when source-entry is updated

            # Save suites and types separately because of Deb822SourceEntry/SourceEntry differences
            try:
                suites = source_entry.suites
            except AttributeError:
                suites = [source_entry.dist]

            try:
                types = source_entry.types
            except AttributeError:
                types = [source_entry.type]

            # Create the new entry
            new_entry = {
                "source-entry":source_entry,
                "types":types,
                "suites":suites,
                "signed-by":self.__get_signed_by(source_entry.line),
                "org-entry":None
            }
            apt_sources.append(new_entry)

        return apt_sources

    def __search_keyring_path(self, distro):
        if not distro:
            return ''
        distro = distro.split('-')[0]
        return get_installed_file_path(self.__keyrings[distro])

    def __get_signed_by(self, line):
        # Signed-by is not saved into its own property
        keyring = ''
        match = re.search(pattern=r'signed-by[=:\s]+([^\]\n]+)', string=line, flags=re.IGNORECASE)
        if match:
            # Keyring can be moved: check if it still exists
            if exists(match.group(1)):
                keyring = match.group(1)

        # Keyring not found: check if installed on system
        if not keyring:
            if 'debian' in line:
                keyring = self.__search_keyring_path('debian')
            elif 'solydxk' in line:
                keyring = self.__search_keyring_path('solydxk')
        return keyring

    def __entry_in_list(self, check_source_entry, sources_list):
        # Check if given source entry is found in sources list
        # Only check on line property
        for source_entry in sources_list:
            if check_source_entry.line == source_entry.line:
                return True
        return False

    def source_line(self, types, uri, suites, comps,
                    architectures=None, disabled=False):
        """Create source line

        Args:
            types (list[str]): apt source types
            uri (str): apt source uri
            suites (list[str]): apt source suites
            comps (list[str]): apt source components
            architectures (list[str], optional): apt source arhitectures. Defaults to None.
            signed_by (str, optional): path to keyring file. Defaults to None.
                If not provided it is chosen by repo (__get_signed_by function).
            disabled (bool, optional): sets whether or not the apt source is disabled.
                Defaults to False.

        Returns:
            str: source line
        """
        # Create the options string
        options = ''
        if not architectures:
            architectures = SUPPORTED_ARCHS
        if architectures:
            options = f"arch={','.join(architectures)}"
        if options:
            options = f"[{options.strip()}] "

        # Build source line (pre-deb822 style)
        # next used to stop at first found item
        source_type = next((s for s in types if 'src' not in s), None)
        source_disabled = '#' if disabled else ''
        line = f"{source_disabled}{source_type} {options}{uri} " \
               f"{suites[0]} {' '.join(comps)}\n"

        return line

    def deb822_section(self, types, uri, suites, comps, architectures=None,
                       signed_by=None, disabled=False, comment=''):
        """Create deb822 section
           https://repolib.readthedocs.io/en/latest/deb822-format.html

        Args:
            types (list[str]): apt source types
            uri (str): apt source uri
            suites (list[str]): apt source suites
            comps (list[str]): apt source components
            architectures (list[str], optional): apt source arhitectures. Defaults to None.
            signed_by (str, optional): path to keyring file. Defaults to None.
                If not provided it is chosen by repo (__get_signed_by function).
            disabled (bool, optional): sets whether or not the apt source is disabled.
                Defaults to False.
            comment (str, optional): apt source comment. Defaults to ''.

        Returns:
            str: deb822 section for the repo
        """
        if not architectures:
            architectures = SUPPORTED_ARCHS
        if not signed_by:
            signed_by = self.__get_signed_by(uri)

        # Set default comment for this repo
        source_comment = f"# {suites[0]} repository" if not comment else comment

        # Enabled string
        enabled = 'no' if disabled else 'yes'

        section = f"{source_comment}\n" \
        f"Enabled: {enabled}\n" \
        f"Types: {' '.join(types)}\n" \
        f"URIs: {uri}\n" \
        f"Suites: {' '.join(suites)}\n" \
        f"Components: {' '.join(comps)}\n" \
        f"Architectures: {' '.join(architectures)}\n" \
        f"Signed-By: {signed_by}\n\n"

        return section

    def new_apt_source(self, types, uri, suites, comps, architectures=None,
                       signed_by=None, disabled=False, comment='', file=None):
        """Create apt source dictionary

        Args:
            types (list[str]): apt source types
            uri (str): apt source uri
            suites (list[str]): apt source suites
            comps (list[str]): apt source components
            architectures (list[str], optional): apt source arhitectures. Defaults to None.
            signed_by (str, optional): path to keyring file. Defaults to None.
                If not provided it is chosen by repo (__get_signed_by function).
            disabled (bool, optional): sets whether or not the apt source is disabled.
                Defaults to False.
            comment (str, optional): apt source comment. Defaults to ''.
            file (str, optional): apt sources save file. Defaults to None.
                If not provided a source file is chosen by repo.

        Returns:
            dict{source_entry_object, signed_by_path, org_entry_object}: org_entry_object is used
                 in code to save the original state of the source_entry object when updated.
        """
        # Check current used system
        sources_list = FilteredSourcesList().list
        for source_entry in sources_list:
            #deb822_instance = isinstance(source_entry, Deb822SourceEntry)
            if not file and \
               (('debian' in source_entry.uri and 'debian' in uri) or \
               ('solydxk' in source_entry.uri and 'solydxk' in uri)):
                file=source_entry.file

        if DEB822:
            # Get the deb822 section string
            source_section = self.deb822_section(types=types,
                                                 uri=uri,
                                                 suites=suites,
                                                 comps=comps,
                                                 architectures=architectures,
                                                 signed_by=signed_by,
                                                 disabled=disabled,
                                                 comment=comment)
            new_source_entry = Deb822SourceEntry(section=source_section, file=file)
        else:
            source_line = self.source_line(types=types,
                                           uri=uri,
                                           suites=suites,
                                           comps=comps,
                                           architectures=architectures,
                                           disabled=disabled)
            new_source_entry = SourceEntry(line=source_line, file=file)

        new_entry = {
            "source-entry":new_source_entry,
            "types":types,
            "suites":suites,
            "signed-by":signed_by,
            "org-entry":None
        }

        return new_entry

    def save(self, new_sources_list):
        """Save sources to files

        Args:
            sources_list (list[dict]): Saves list returned by get_apt_sources
        """
        filtered_sources_list = FilteredSourcesList()
        sources_list = filtered_sources_list.list

        for new_source in new_sources_list:
            # Check first if this is an update
            for entry_index, source_entry in enumerate(sources_list):
                if new_source['org-entry']:
                    try:
                        suites = source_entry.suites
                        new_suites = new_source['org-entry'].suites
                    except AttributeError:
                        suites = [source_entry.dist]
                        new_suites = [new_source['org-entry'].dist]
                    if source_entry.uri == new_source['org-entry'].uri and \
                       suites == new_suites:
                        # Update the entry
                        sources_list[entry_index] = new_source['source-entry']
                        break

            # If source_entry is not in source_list, this is a new entry
            if not self.__entry_in_list(check_source_entry=new_source['source-entry'],
                                        sources_list=sources_list):
                # Add a new entry
                sources_list.append(new_source['source-entry'])

        # Set the filtered sources list with the new list
        filtered_sources_list.list = sources_list
        # Backup and save
        filtered_sources_list.backup(backup_ext='.bak')
        filtered_sources_list.save()
        # Save the new sources
        self.__apt_sources = self.__save_apt_sources()

    def get_apt_sources(self, include_repos=None, exclude_suites=None):
        """Get all current (filtered) sources

        Args:
            include_repos (list[str], optional): include only listed repos. Defaults to None.
                          limited by self.__include_repos
            exclude_suites (list[str], optional): exclude listed suites. Defaults to None.

        Returns:
            list[dict]: [{file, types, uri, suites, comps, architectures, disabled}]
        """
        if not include_repos and not exclude_suites:
            return self.__apt_sources

        apt_sources = []
        for apt_source in self.__apt_sources:
            # Check if the source_entry can be saved
            skip_source_entry = False
            if include_repos:
                if not any(x in apt_source['source-entry'].uri for x in include_repos):
                    skip_source_entry = True
            if exclude_suites and not skip_source_entry:
                for suite in apt_source['suites']:
                    if any(x in suite for x in exclude_suites):
                        skip_source_entry = True
            if not skip_source_entry:
                apt_sources.append(apt_source)
        return apt_sources

    def set_uri(self, apt_source, uri):
        """Set the new uri in the apt source and
           save the original apt source in org-entry

        Args:
            apt_source (dict): the apt source
            uri (string): the new uri
        """
        if not apt_source['org-entry']:
            apt_source['org-entry'] = deepcopy(apt_source['source-entry'])
        apt_source['source-entry'].uri = uri

        # Just setting the uri property does not change the line.
        # You need to change it manually to actually save that line to sources.list
        if not DEB822:
            apt_source['source-entry'].line = apt_source['source-entry'].line.replace(
                apt_source['org-entry'].uri, uri)

    def set_disable(self, apt_source, disabled=True):
        """Disable or enable the apt source and
           save the original apt source in org-entry

        Args:
            apt_source (dict): the apt source
            disable (bool): disable the apt source or not
        """
        if not apt_source['org-entry']:
            apt_source['org-entry'] = deepcopy(apt_source['source-entry'])
        apt_source['source-entry'].disabled = disabled

        # Just setting the disabled property does not change the line.
        # You need to change it manually to actually save that line to sources.list
        if not DEB822:
            line = apt_source['source-entry'].line
            if disabled:
                if not line.startswith('#'):
                    apt_source['source-entry'].line = f"#{line}"
            else:
                apt_source['source-entry'].line = re.sub('^#', '', line).strip()

    def get_backports(self, exclude_disabled=True):
        """Get backports repos

        Args:
            exclude_disabled (bool, optional): do not list disabled backports repos.
                                               Defaults to True.

        Returns:
            list[dict]: list with backports repos:
                        [{file, types, uri, suites, comps, architectures, disabled}]
        """
        backports = []
        apt_sources = self.get_apt_sources(include_repos=['debian'])
        for apt_source in apt_sources:
            if 'backports' in ' '.join(apt_source['suites']):
                if exclude_disabled and apt_source['source-entry'].disabled:
                    continue
                backports.append(apt_source)
        return backports

    def get_mirror_data(self, exclude_mirrors=None, get_dead_mirrors=False):
        """ Returns mirror data

        Args:
            exclude_mirrors (list[str], optional): List of mirrors to exclude. Defaults to None.
            get_dead_mirrors (bool, optional): Also list dead mirrors. Defaults to False.

        Returns:
            list[list[str]]: [[country, distro, uri]]
        """
        if exclude_mirrors is None:
            exclude_mirrors = []
        mirror_data = []
        script_dir = abspath(dirname(__file__))
        config = get_config_dict(join(script_dir, "solydxk-system.conf"))
        mirrors_url = config.get('MIRRORSLIST', 'https://repository.solydxk.com/mirrors.list')
        mirrors_list = join(script_dir, basename(mirrors_url))
        if get_dead_mirrors:
            mirrors_list = f"{mirrors_list}.dead"

        mirrors_http_path = join(script_dir, 'mirrors.http')
        mirrors_http = []
        if exists(mirrors_http_path):
            with open(file=mirrors_http_path, mode='r', encoding='utf-8') as f:
                mirrors_http = f.read().splitlines()

        try:
            # Download the mirrors list from the server
            url = mirrors_url
            if get_dead_mirrors:
                url = f"{url}.dead"
            txt = get_value_from_url(url)
            if txt is not None:
                # Make sure that every uri begins with the correct protocol.
                # Uses mirrors.http file for patterns that still use http instead of https.
                arr_txt = []
                for line in txt.splitlines():
                    arr_line = line.strip().split(',')
                    if arr_line[2][:4] != 'http':
                        http = 'https://'
                        for line in mirrors_http:
                            match = re.search(pattern=line, string=arr_line[2])
                            if match:
                                http = 'http://'
                                break
                        arr_line[2] = f'{http}{arr_line[2]}'
                        line = ','.join(arr_line)
                    arr_txt.append(line)
                # Save to a file
                with open(file=mirrors_list, mode='w', encoding='utf-8') as f:
                    f.write('\n'.join(arr_txt))
        except Exception:
            pass

        if exists(mirrors_list):
            with open(file=mirrors_list, mode='r', encoding='utf-8') as f:
                lines = f.readlines()
            for line in lines:
                arr_line = line.strip().split(',')
                if len(arr_line) > 2:
                    if get_dead_mirrors:
                        add = False
                        apt_sources = self.get_apt_sources()
                        for apt_source in apt_sources:
                            if arr_line[2] in apt_source['source-entry'].uri:
                                add = True
                                break
                    else:
                        add = True
                        for excl in exclude_mirrors:
                            if excl in arr_line[2]:
                                add = False
                                break
                    if add:
                        mirror_data.append(arr_line)
        return mirror_data

    def is_uri_in_sources(self, uri, exclude_suites=None):
        """Check if url is found in apt sources

        Args:
            url (string): repo url
            exclude_suites (list[str], optional): list with suites to exclude for check.
                                                  Defaults to None.

        Returns:
            _type_: _description_
        """
        uri = re.sub('https?://', '', uri).rstrip('/')
        apt_sources = self.get_apt_sources(exclude_suites=exclude_suites)
        for apt_source in apt_sources:
            if uri in apt_source['source-entry'].uri:
                return True
        return False

    def get_repo_suite(self, pattern):
        """Return repo suite by pattern
        Used in scripts/*

        Args:
            pattern (str): regexp pattern to match suite

        Returns:
            str: repo suite
        """
        for apt_source in self.__apt_sources:
            if not apt_source['source-entry'].disabled:
                for suite in apt_source['suites']:
                    match = re.search(pattern=pattern, string=suite, flags=re.IGNORECASE)
                    if match:
                        return suite
        return ''
