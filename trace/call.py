import subprocess
import re
# import click

# Initialize click
# @click.command()
# @click.argument('command')
def main(command):
    # Find open libraries by program
    trace = find_open_libraries(command)
    # Parse output to return only string
    output = parse_open_libraries(trace)

    # Print list
    for list in output:
        print list

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
    trace = p.stdout.read()

    # Return the results from strace
    return trace

# Function to strip string from quotes
def parse_open_libraries(input):
    # find all strings between quotes
    output = re.findall('"([^"]*)"', input)

    # Returns a list of open libraries
    return output

# if __name__ == "__main__":
#     main()