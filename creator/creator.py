import click
import pprintpp as pp
import strip

# Initialize click
@click.command(context_settings=dict(ignore_unknown_options=True,))

# Main program
@click.argument('software_command', nargs=-1)
def creator(software_command):
    print(software_command)
    umbrella_specification = dict()

    # First part of argument should be software name
    software_name = software_command[0]

    # Get command after calling software
    command = ''
    for arg in software_command:
        if arg is not software_command[0]:
            part = arg
            command += part + ' '

    c_command = software_name + command
    print(c_command)

    print("\nThis is a Umbrella Specification Creation command line tool for software preservation.\n"
          "This program will look for information on your system and determine what information is\n"
          "needed for writing a Umbrella Specification file.\n")

    # Get Project Name and Description
    project = strip.get_project()

    umbrella_specification['comment'] = project['name']
    umbrella_specification['note'] = project['note']

    # Get Kernel
    kernel = strip.get_kernel()
    umbrella_specification.update({"kernel": kernel})

    # Get Hardware
    hardware = strip.get_hardware()
    umbrella_specification.update({"hardware": hardware})

    # Get Operating System
    os = strip.get_os()
    umbrella_specification.update({"os": os})

    # Get Software
    software = strip.get_software(software_name)
    umbrella_specification.update({"software": software})

    # Get Data
    data = strip.get_data(c_command)
    umbrella_specification.update({"data": data})

    # Get Environmental Variables
    environ = strip.get_environ()
    pp.pprint(environ)

    # pp.pprint(umbrella_specification)

    if click.confirm("Would you like to edit your environmental variables?"):
        new_environ = strip.edit_environ(environ)

        umbrella_specification.update({"environ": new_environ})
    else:
        umbrella_specification.update({"environ": environ})

    pp.pprint(umbrella_specification)

if __name__ == "__main__":
    creator()