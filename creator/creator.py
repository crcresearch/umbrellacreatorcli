import click
import json
import pprintpp as pp
from strip import CreateUmbrellaSpecification


# Initialize click
@click.command(context_settings=dict(ignore_unknown_options=True,))
# Main program
@click.argument('software_command', nargs=-1)
def creator(software_command):
    # First part of argument should be software name
    software_name = software_command[0]

    # Get command after calling software
    command = ''
    for arg in software_command:
        if arg is not software_command[0]:
            part = arg
            command += part + ' '

    c_command = software_name + ' ' + command

    umbrella = CreateUmbrellaSpecification(software=software_name, command=c_command)

    print("\nThis is a Umbrella Specification Creation command line tool for software preservation.\n"
          "This program will look for information on your system and determine what information is\n"
          "needed for writing a Umbrella Specification file.")
    # file_results = get_open_files(c_command)

    # Edit Output Section
    umbrella.edit_output()

    # pp.pprint(umbrella.specification)

    # Edit Environment Variables
    umbrella.edit_environ()

    specification = json.dumps(umbrella.specification, indent=4, sort_keys=True)
    print('\n' + specification + '\n')

    umbrella.save_specification()

if __name__ == "__main__":
    creator()
