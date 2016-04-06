import click
import ctypes
from psutil import virtual_memory
import platform, sys, ld, urllib, os, tarfile, multiprocessing, math, re
import pprintpp as pp
from umbrella import get_md5_and_file_size
import trace_program


class CreateUmbrellaSpecification:
    def __init__(self, command):
        # Get the name of the software (usually the first command in string)
        software_name = command[0]

        # Get the rest of the command after software
        p_command = ''
        for arg in command:
            if arg is not command[0]:
                part = arg
                p_command += part + ' '

        # Initialize self.specification
        self.specification = {
            "cmd": command
        }
        # Use strace to scan system calls and get open/write file_results
        file_results = get_open_files(command)

        # Get information about the system, software, data files, package manager, and output files
        self.get_kernel()
        self.get_hardware()
        self.get_software(software_name)
        self.get_data(file_results, software_name)
        self.get_environ()

    # Project
    def get_project(self):
        project_name = click.prompt("First, lets name the Umbrella project: ", default=None, show_default=False)
        project_note = click.prompt("Enter a description for this project: ", default=None, show_default=False)

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
        if sys.platform == 'win32':
            dirname = 'C:\\'
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(dirname), None, None, ctypes.pointer(free_bytes))
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
        name = None
        version = None

        if sys.platform == 'win32':
            name = platform.system() + ' ' + platform.release()
            version = platform.version()
        elif sys.platform == ('linux' or 'linux2'):
            name = ld.name(pretty=False)
            version = ld.version(pretty=False)
        elif sys.platform == 'darwin':
            name = platform.system() + ' ' + platform.mac_ver()[0]
            version = platform.mac_ver()[0]

        format = click.prompt("Please enter file format of the operating system install file (tgz or plain): ",
                              default="tgz", show_default=True)
        action = click.prompt("Please enter the file action (unpack or none): ", default="unpack", show_default=True)
        uncompressed_size = click.prompt("Please enter the uncompressed size of the: ")

        option = True
        urls = []
        while option == True:
            url = click.prompt("Please enter the URL where the operating system file is hosted: ")
            urls.append(url)

            option = click.confirm("Would you like to add another URL?")

        os_md5, os_size = get_md5_and_file_size(urllib.urlopen(urls[0]))
        # uncompressed_size = os.popen('gzip -l %s' % urllib.urlopen(url[0]))

        self.os = {
            "name": name,
            "version": version,
            "source": urls,
            "format": format,
            "action": action,
            "checksum": os_md5,
            "id": os_md5,
            "size": os_size,
            "uncompressed_size": uncompressed_size
        }

        return self.os

    # Software
    def get_software(self, software):
        self.specification.update({
            'software': {
                software: {

                }
            }
        })

        return self.specification

    # Environmental Variables
    def get_environ(self):
        self.specification.update({
            "environ": {
                "PWD"   : os.environ['PWD'],
                "PATH"  : os.environ['PATH']
            }
        })

        return self.specification

    def edit_environ(self):
        # Get original dictionary
        # environ_variables = original

        print("Environmental Variables:\n"
              "Edit the environmental variables.  If you would like the environmental variables to be\n"
              "blank in the specification, just enter \"None\".  Press \"Enter\" to keep the original\n"
              "values.")

        path = click.prompt("Please enter PATH: ", default=self.specification['environ']['PATH'], show_default=False)
        pwd = click.prompt("Please enter PWD: ", default=self.specification['environ']['PWD'], show_default=False)

        if path == ('None' or 'none' or 'NONE'):
            self.specification['environ'].pop('PATH')
        else:
            self.specification['environ']['PATH'] = path
            pp.pprint(self.specification['environ'])

        if pwd == ('None' or 'none' or 'NONE'):
            self.specification['environ'].pop('PWD')
        else:
            self.specification['environ']['PWD'] = pwd
            pp.pprint(self.specification['environ'])

        option = click.confirm("Would you like to add another environmental variable?")

        while option == True:
            other_key = click.prompt("Please enter environmental variable key: ", default=None, show_default=False)
            other_value = click.prompt("Please enter environmental variable value: ", default=None, show_default=False)

            self.specification['environ'][other_key] = other_value

            option = click.confirm("Would you like to add another environmental variable?")

        # pp.pprint(environ_variables)

        return self.specification

    # Data
    def get_data(self, file_results, software):
        data_paths = []
        self.specification.update({"data": {}})

        # print(file_results) # test

        for path, value in file_results.items():
            # print(value) # test
            if value == None:
                data_paths.append(path)

        data_list = strip_files(data_paths)
        # print(data_list) # test

        # print(software) # test
        # Check for software file
        if software in data_list:
            data_list.pop(software)

        # print(data_list) # test
        # print(data_paths) # test

        for count, file in enumerate(data_list):
            source = []
            for p in data_paths:
                if file in p:
                    mountpoint = p
                    # print(mountpoint) # print
            # mountpoint = [x for x in data_paths if file in x]
            source.append(mountpoint)

            print(source) # test

            data_md5, data_size = get_md5_and_file_size(urllib.urlopen(source[0]))

            self.specification["data"].update({
                file: {
                    "format": "plain",
                    "checksum": data_md5,
                    "source": source,
                    "mountpoint": mountpoint,
                    "id": data_md5,
                    "size": data_size
                }
            })

        return self.specification

    def get_pm(self, file_results, software):
        package_paths = []

        # print results # test

        for path, value in file_results.items():
            # print value  # test
            if value != None and value != False:
                package_paths.append(value)

        # print(software)  # test

        packages = {
            "config": {},
            "list": " ".join(package_paths),
            "name": "yum"
        }

        return packages

def get_open_files(command):
    # print(command) # test
    distro = ld.name(pretty=False)
    open_files = trace_program.get_calls(command)
    # print(open_files) # test
    results = trace_program.package_status(open_files, distro)

    # print(results) # test

    return results

# Function for getting uncompressed_size
def get_uncompressed_size(gzfile):
    uncompressed_size = 0
    if(gzfile.endswith("tar.gz")):
        tar = tarfile.open=(gzfile)
        tar.extractall()
        uncompressed_size = sum(file.file_size for file in tar.infolist())
        tar.close()
    else:
        print("Not a tar.gz file: '%s '" % sys.argv[0])

    print(uncompressed_size)

# Function to strip out only the files from a path
def strip_files(paths):
    c_files = {}
    for file in paths:
        c_file = os.path.basename(os.path.normpath(file))
        c_files.update({
            c_file: file
        })

    # Return the files without paths
    return c_files