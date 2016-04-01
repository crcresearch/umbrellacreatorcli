import subprocess
import re
import os
# import click

# Initialize click
# @click.command()
# @click.argument('command')
def get_calls(command):
    # Find open libraries by program
    trace = find_open_libraries(command)
    # Parse output to return only string
    output = parse_open_libraries(trace)

    # Print list
    for list in output:
        print list

    print output
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
    trace = p.stdout.read().rstrip()

    # Return the results from strace
    return trace

# Function to strip string from quotes
def parse_open_libraries(input):
    # find all strings between quotes
    output = re.findall('"([^"]*)"', input)

    # Returns a list of open libraries
    return output

# Function to find out if files are from a package or are data files
def package_status(paths, os):
    # TODO: Get this working!
    if os == 'Red Hat Enterprise Linux Server':
        command = 'rpm -qf '
    elif os == 'Manjaro Linux':
        command = 'pacman -Qo '
    else:
        command = None

    results = {}
    f_results = {}

    for path in paths:
        s = subprocess.Popen(command + path, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        s.wait()
        trace = s.stdout.read().rstrip()

        results.update({
            path: trace
        })

    if os == 'Red Hat Enterprise Linux Server':
        for key, value in results.items():
            if value not in f_results.values():
                if value == 'file ' + key + ' is not owned by any package':
                    f_results[key] = None
                else:
                    f_results[key] = value

        return f_results
    elif os == 'Manjaro Linux':
        for key, value in results.items():
            if value not in f_results.values():
                if value == 'error: No package owns ' + key:
                    f_results[key] = None
                else:
                    new_value = value.split(' ')
                    f_value = new_value[-2] + '-' + new_value[-1]
                    f_results[key] = f_value
    else:
        return f_results

# if __name__ == "__main__":
#     get_calls()