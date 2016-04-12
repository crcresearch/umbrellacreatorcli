import click
import ctypes
import platform
import sys
import ld
import urllib
import os
import multiprocessing
import math
import pprintpp as pp
import trace_program
import json
from umbrella import get_md5_and_file_size
from psutil import virtual_memory


class CreateUmbrellaSpecification:
    def __init__(self, software, command):
        # Get the name of the software (usually the first command in string)
        self.software = software
        self.command = command

        # Get platform, os, and version
        if sys.platform.startswith('win32'):
            self.distro = platform.system() + ' ' + platform.release()
            self.version = platform.version()
        elif sys.platform.startswith('linux'):
            self.distro = ld.name(pretty=False)
            self.version = ld.version(pretty=False)
        elif sys.platform.startswith('darwin'):
            self.distro = platform.system() + ' ' + platform.mac_ver()[0]
            self.version = platform.mac_ver()[0]

        # Initialize self.specification
        self.specification = {
            "cmd": self.command
        }

        # Use strace to scan system calls and get open/write file_results
        data_file_results = self.get_open_files()
        output_file_results = self.get_open_files(file_type='O_WRONLY')
        software_file_results = self.get_open_files(file_type='software')

        # Get information about the system, software, data files, package manager, and output files
        self.get_project()
        self.get_kernel()
        self.get_hardware()
        self.get_os()
        self.get_software(software_file_results)
        self.get_data(data_file_results)
        self.get_output(output_file_results)
        self.get_environ()
        self.get_pm(data_file_results)

    # Project
    def get_project(self):

        print("\nPROJECT INFORMATION:")

        project_name = click.prompt("First, lets name the Umbrella project", default=None, show_default=False)
        project_note = click.prompt("Enter a description for this project", default=None, show_default=False)

        self.specification.update({
            "name": project_name,
            "note": project_note
        })

        return self.specification

    # Kernel
    def get_kernel(self):
        name = platform.system()
        version = platform.release()

        self.specification.update({
            "kernel": {
                "version": version,
                "name": name
            }
        })

        return self.specification

    # Hardware
    def get_hardware(self):
        if sys.platform.startswith('win32'):
            dirname = 'C:\\'
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(dirname), None, None,
                                                       ctypes.pointer(free_bytes))
            actual_disk_size = math.ceil(free_bytes.value/1.073741824e9)
        else:
            dirname = '/'
            stats = os.statvfs(dirname)
            disk_size = stats.f_bsize * stats.f_blocks
            actual_disk_size = math.ceil(disk_size/1.073741824e9)

        cores = multiprocessing.cpu_count()
        disk = actual_disk_size
        arch = platform.machine()
        memory = virtual_memory()
        actual_memory = math.ceil(memory.total/1.073741824e9)

        self.specification.update({
            "hardware": {
                "cores": unicode(int(cores)),
                "disk": unicode(int(disk)) + 'GB',
                "arch": arch,
                "memory": unicode(int(actual_memory)) + 'GB'
            }
        })

        return self.specification

    # Operating System
    def get_os(self):
        print("\nOPERATING SYSTEM:")

        os_format = click.prompt("Please enter file format of the operating system install file (tgz or plain)",
                                 default="tgz", show_default=True)
        os_action = click.prompt("Please enter the file action (unpack or none)", default="unpack", show_default=True)

        uncompressed_size = click.prompt("Please enter the uncompressed size of the tgz file",
                                         default="none", show_default=True)

        option = True
        urls = []
        while option:
            url = click.prompt("Please enter the URL where the operating system file is hosted")
            urls.append(url)

            option = click.confirm("Would you like to add another URL?")

        os_file = urllib.urlopen(urls[0])
        os_md5, os_size = get_md5_and_file_size(os_file)

        self.specification.update({
            "os": {
                "name": self.distro,
                "version": self.version,
                "source": urls,
                "format": os_format,
                "action": os_action,
                "checksum": os_md5,
                "id": os_md5,
                "size": unicode(os_size)
            }
        })

        # Uncompressed size is not mandatory
        if uncompressed_size is not 'none':
            self.specification['os'].update({
                "uncompressed_size": uncompressed_size
            })

        return self.specification

    # Software
    def get_software(self, file_results):
        software_paths = []

        print("\nSOFTWARE:")

        for path, value in file_results.items():
            software_paths.append(path)

        software_list = strip_files(software_paths)

        for count, software_file in enumerate(software_list):
            source = []

            print("File: " + software_file)
            software_format = click.prompt("Please enter file format of the software install file (tgz or plain)",
                                           default="tgz", show_default=True)
            software_action = click.prompt("Please enter the file action (unpack or none)",
                                           default="unpack", show_default=True)
            uncompressed_size = click.prompt("Please enter the uncompressed size of the tgz file",
                                             default="none", show_default=True)

            for s in software_paths:
                if software_file in s:
                    mountpoint = s

            source.append(mountpoint)

            # print source # test
            # print software_file # test

            software_md5, software_size = get_md5_and_file_size(urllib.urlopen(source[0]))

            self.specification.update({
                'software': {
                    software_file: {
                        "format": software_format,
                        "action": software_action,
                        "checksum": software_md5,
                        "source": source,
                        "mountpoint": mountpoint,
                        "uncompressed_size": uncompressed_size,
                        "id": software_md5,
                        "size": software_size
                    }
                }
            })

        return self.specification

    # Environmental Variables
    def get_environ(self):
        self.specification.update({
            "environ": {
                "PWD": os.environ['PWD'],
                "PATH": os.environ['PATH']
            }
        })

        return self.specification

    def edit_environ(self):
        # Get original dictionary
        # environ_variables = original

        print("\nENVIRONMENTAL VARIABLES:")
        print("PATH: " + self.specification['environ']['PATH'])
        print("PWD: " + self.specification['environ']['PWD'])

        option = click.confirm("\nWould you like to edit your environmental variables?")
        while option:
            print("\nEdit the environmental variables.  If you would like the environmental variables to be\n"
                  "blank in the specification, just enter \"None\".  Press \"Enter\" to keep the original\n"
                  "values.")

            path = click.prompt("\nPlease enter PATH", default=self.specification['environ']['PATH'], show_default=False)
            pwd = click.prompt("Please enter PWD", default=self.specification['environ']['PWD'], show_default=False)

            if path == ('None' or 'none' or 'NONE'):
                self.specification['environ'].pop('PATH')
            else:
                self.specification['environ']['PATH'] = path

            if pwd == ('None' or 'none' or 'NONE'):
                self.specification['environ'].pop('PWD')
            else:
                self.specification['environ']['PWD'] = pwd

            # Print Environmental Variables so far
            print("\nPWD or PATH:")
            if self.specification['environ']['PWD']:
                print("PWD: " + self.specification['environ']['PWD'])
            if self.specification['environ']['PATH']:
                print("PATH: " + self.specification['environ']['PATH'])

            # pp.pprint(self.specification['environ']) # test

            option = click.confirm("\nWould you like to add a custom environmental variable?")
            while option:
                other_key = click.prompt("Please enter environmental variable key", default=None,
                                         show_default=False)
                other_value = click.prompt("Please enter environmental variable value", default=None,
                                           show_default=False)

                self.specification['environ'][other_key] = other_value

                # Print Environmental Variables so far
                print("\nEnvironmental Variables:")
                for key in self.specification['environ']:
                    print(key + ": " + self.specification['environ'][key] )

                option = click.confirm("\nWould you like to add another environmental variable?")

            option = click.confirm("Would you like to edit your environmental variables again?")

        return self.specification

    # Data
    def get_data(self, file_results):
        data_paths = []
        self.specification.update({"data": {}})

        for path, value in file_results.items():
            if value is None:
                data_paths.append(path)

        data_list = strip_files(data_paths)
        print data_list # test

        # Check for software file
        if self.software in data_list:
            data_list.pop(self.software)

        for count, data_file in enumerate(data_list):
            source = []

            for p in data_paths:
                if data_file in p:
                    mountpoint = p
            # mountpoint = [x for x in data_paths if file in x]
            source.append(mountpoint)

            data_md5, data_size = get_md5_and_file_size(urllib.urlopen(source[0]))

            self.specification["data"].update({
                data_file: {
                    "format": "plain",
                    "checksum": data_md5,
                    "source": source,
                    "mountpoint": mountpoint,
                    "id": data_md5,
                    "size": unicode(data_size)
                }
            })

        return self.specification

    def get_pm(self, file_results):
        package_paths = []

        for path, value in file_results.items():
            if value is not None and value is not False:
                package_paths.append(value)

        if self.distro == 'Red Hat Enterprise Linux Server':
            mountpoint = '/etc/yum.repo.d/epel.repo'
            pm_md5, pm_size = get_md5_and_file_size(urllib.urlopen(mountpoint))

            self.specification.update({
                "package_manager": {
                    "config": {
                        "epel.repo": {
                            "format": "plain",
                            "checksum": pm_md5,
                            "size": pm_size,
                            "id": pm_md5,
                            "mountpoint": mountpoint
                        }
                    },
                    "list": " ".join(package_paths),
                    "name": "yum"
                }
            })
        elif self.distro == 'Manjaro Linux':
            mountpoint = '/etc/pacman.conf'
            pm_md5, pm_size = get_md5_and_file_size(urllib.urlopen(mountpoint))

            self.specification.update({
                "package_manager": {
                    "config": {
                        "pacman.conf": {
                            "format": "plain",
                            "checksum": pm_md5,
                            "size": pm_size,
                            "id": pm_md5,
                            "mountpoint": mountpoint
                        }
                    },
                    "list": " ".join(package_paths),
                    "name": "pacman"
                }
            })
        else:
            print("\nYour operating system is not compatible with Umbrella")

        return self.specification

    def get_output(self, file_results):
        output_files = []

        for path, value in file_results.items():
            if value is None:
                output_files.append(path)

        self.specification.update({
            "output": {
                "files": output_files,
                "dirs": []
            }
        })

        return self.specification

    def edit_output(self):
        print('\nOUTPUT FILES:')

        for output_files in self.specification['output']['files']:
            print(output_files)

        option = click.confirm("\nWould you like to add more output files or directories?")
        while option:
            new_file = click.prompt("Please enter another output file (including path)", default='None',
                                    show_default=True)
            new_directory = click.prompt("Please enter a output directory", default='None',
                                         show_default=True)

            if new_file is not 'None':
                self.specification['output']['files'].append(new_file)

            if new_directory is not 'None':
                self.specification['output']['dirs'].append(new_directory)

            print('\nFiles:')
            for output_files in self.specification['output']['files']:
                print(output_files)

            print('\nDirectories:')
            for output_dirs in self.specification['output']['dirs']:
                print(output_dirs)

            option = click.confirm("\nWould you like to add more output files or directories?")

    def save_specification(self):
        option = click.confirm("\nWould you like to save the umbrella specification to disk?")

        while option:
            path = click.prompt("\nWhere would you like to save the file? \n"
                                  "Enter path and file name, e.g., /home/username/Desktop/mySpecification.umbrella \n"
                                  "The file must end with the .umbrella file extension")

            if path.endswith('.umbrella'):
                with open(path, 'w') as outfile:
                    json.dump(self.specification, outfile, indent=4)
                option = False
            else:
                print("You did not include the .umbrella file extension to your file name.  Please try again.")
                option = True

    def get_open_files(self, file_type='O_RDONLY'):
        open_files = trace_program.get_calls(self.command, file_type)
        results = trace_program.package_status(open_files, self.distro)

        return results


# Function to strip out only the files from a path
def strip_files(paths):
    c_files = {}
    for open_file in paths:
        c_file = os.path.basename(os.path.normpath(open_file))
        c_files.update({
            c_file: open_file
        })

    # Return the files without paths
    return c_files
