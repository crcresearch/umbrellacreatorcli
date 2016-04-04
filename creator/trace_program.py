import subprocess
import re
import os
# import click

# Initialize click
# @click.command()
# @click.argument('command')
def get_calls(command, file_type='O_RDONLY'):
    # Find open libraries by program
    trace = find_open_libraries(command)
    # Parse output to return only string
    output = parse_open_libraries(trace, file_type)

    # Print list
    # for list in output:
    #     print(list) # test

    # print(output) # test
    return output

# Function to only return open libraries from strace
def find_open_libraries(command):
    # Establish strace command
    strace = "strace"
    # Use grep to search for all instances of 'open('
    open_calls = '2>&1|grep "open("'
    # Complete the command
    call = strace + ' ' + command + ' ' + open_calls

    # Run strace through pythons subprocess library
    p = subprocess.Popen(call, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    p.wait()
    trace = p.stdout.read().split('\n')
    # print(trace) # test

    # Return the results from strace
    return trace

# Function to strip string from quotes
def parse_open_libraries(input, file_type):
    # Check for O_RDONLY or O_WRONLY
    # Get RDONLY or WRONLY files from system call
    for i, item in enumerate(input):
        # print(item) # test
        if file_type == 'O_WRONLY':
            if 'O_WRONLY' not in item:
                input.pop(i)
            else:
                new_value = re.findall('"([^"]*)"', item)
                input[i] = new_value[0]

        elif file_type == 'O_RDONLY':
            if 'O_RDONLY' not in item:
                input.pop(i)
            else:
                new_value = re.findall('"([^"]*)"', item)
                input[i] = new_value[0]

    print input # test

    return input

# Function to find out if files are from a package or are data files
def package_status(paths, os):
    # paths must be a tuple
    # Check OS version
    if os == 'Red Hat Enterprise Linux Server':
        command = 'rpm -qf '
    elif os == 'Manjaro Linux':
        command = 'pacman -Qo '
    else:
        command = None

    # Define dictionaries
    results = {}
    f_results = {}

    # check whether the open file is part of a package
    for i, path in enumerate(paths):
        s = subprocess.Popen(command + path, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        trace = s.stdout.read().replace('\n', '')
        print('Path: ' + path) # test
        print('Trace: ' + trace) # test
        results.update({
            path: trace
        })

    # What do you do if it is/is not part of a package
    if os == 'Red Hat Enterprise Linux Server':
        for key, value in results.items():
            # Check for duplicates
            if value not in f_results.values():
                # Check for errors
                if value == 'file ' + key + ' is not owned by any package':
                    f_results[key] = None
                # If no errors
                else:
                    f_results[key] = value

        return f_results
    elif os == 'Manjaro Linux':
        print 'start'
        for key, value in results.items():
            print key # test
            print value # test
            # Check for duplicates
            if value not in f_results.values():
                # Check for errors
                if value == 'error: No package owns ' + key:
                    f_results[key] = None
                    print '1 ' + str(f_results)
                elif (value == 'error: failed to read file \'' + key + '\': No such file or directory') \
                        or (value == 'error: failed to find \'' + key + '\' in PATH: No such file or directory'):
                    f_results[key] = False
                    print '2 ' + str(f_results)
                # If no errors
                else:
                    new_value = value.split(' ')
                    f_value = new_value[-2] + '-' + new_value[-1]
                    f_results[key] = f_value
                    print '3 ' + str(f_results)
    else:
        return f_results

    return f_results

# if __name__ == "__main__":
#     get_calls()