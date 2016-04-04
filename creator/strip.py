import click
import ctypes
from psutil import virtual_memory
import platform, sys, ld, urllib, os, tarfile, multiprocessing, math, re
import pprintpp as pp
from umbrella import get_md5_and_file_size
import trace_program

# Project
def get_project():
    project_name = click.prompt("First, lets name the Umbrella project: ", default=None, show_default=False)
    project_note = click.prompt("Enter a description for this project: ", default=None, show_default=False)

    project = {
        'name': project_name,
        'note': project_note
    }

    return project

# Kernel
def get_kernel():
    name = platform.system()
    version = platform.release()

    kernel = {
        "version": version,
        "name": name
    }

    return kernel

# Hardware
def get_hardware():
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

    hardware = {
        "cores": int(cores),
        "disk": unicode(int(disk)) + 'GB',
        "arch": arch,
        "memory": unicode(int(actual_memory)) + 'GB'
    }

    return hardware

# Operating System
def get_os():
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

    format = click.prompt("Please enter file format of the operating system install file (tgz or plain): ", default="tgz",
                          show_default=True)
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

    os = {
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

    return os

# Software
def get_software(package):
    software = {
        package: {

        }
    }
    return software

# Environmental Variables
def get_environ():
    environ_variables = {
        "PWD"   : os.environ['PWD'],
        "PATH"  : os.environ['PATH']
    }

    return environ_variables

def edit_environ(original):
    # Get original dictionary
    environ_variables = original

    print("Environmental Variables:\n"
          "Edit the environmental variables.  If you would like the environmental variables to be\n"
          "blank in the specification, just enter \"None\".  Press \"Enter\" to keep the original\n"
          "values.")

    path = click.prompt("Please enter PATH: ", default=environ_variables['PATH'], show_default=False)
    pwd = click.prompt("Please enter PWD: ", default=environ_variables['PWD'], show_default=False)

    if path == ('None' or 'none' or 'NONE'):
        environ_variables.pop('PATH')
    else:
        environ_variables['PATH'] = path
        pp.pprint(environ_variables)

    if pwd == ('None' or 'none' or 'NONE'):
        environ_variables.pop('PWD')
    else:
        environ_variables['PWD'] = pwd
        pp.pprint(environ_variables)

    option = click.confirm("Would you like to add another environmental variable?")

    while option == True:
        other_key = click.prompt("Please enter environmental variable key: ", default=None, show_default=False)
        other_value = click.prompt("Please enter environmental variable value: ", default=None, show_default=False)

        environ_variables[other_key] = other_value

        option = click.confirm("Would you like to add another environmental variable?")

    # pp.pprint(environ_variables)

    return environ_variables

# Data
def get_data(file_results, software):
    data_paths = []
    data = {}

    # print(file_results) # test

    for path, value in file_results.items():
        # print(value) # test
        if value == None:
            data_paths.append(path)

    data_list = strip_files(data_paths)
    # print(data_list) # test

    # print(software) # test
    # Check for software file
    while software in data_list:
        data_list.remove(software)
    # print(data_list) # test

    for file in data_list:
        data =  {
            file: {
                "format": "plain",
                "checksum": "checksum",
                "source": [],
                "mountpoint": "/tmp/" + file,
                "id": "checksum",
                "size": "file_size"
            }
        }

    return data

def get_pm(file_results, software):
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
    distro = ld.name(pretty=False)
    open_files = trace_program.get_calls(command)
    results = trace_program.package_status(open_files, distro)

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
    c_files = []
    for file in paths:
        c_file = os.path.basename(os.path.normpath(file))
        c_files.append(c_file)

    # Return the files without paths
    return c_files