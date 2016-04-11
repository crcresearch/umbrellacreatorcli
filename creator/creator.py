import click
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

    # Get Project Name and Description
    umbrella.get_project()

    # umbrella_specification['comment'] = project['name']
    # umbrella_specification['note'] = project['note']

    # Get Kernel
    # kernel = strip.get_kernel()
    # umbrella_specification.update({"kernel": kernel})

    # Get Hardware
    # hardware = strip.get_hardware()
    # umbrella_specification.update({"hardware": hardware})

    # Get Operating System
    umbrella.get_os()
    # os = strip.get_os()
    # umbrella_specification.update({"os": os})

    # Get Software
    umbrella.get_software()
    # software = strip.get_software(software_name)
    # umbrella_specification.update({"software": software})

    # Get Data
    # data = strip.get_data(file_results, software_name)
    # umbrella_specification.update({"data": data})

    # Get Package Manager
    # pm = strip.get_pm(file_results, software_name)
    # umbrella_specification.update({"package_manager": pm})

    # Get Environmental Variables
    umbrella.get_environ()
    pp.pprint(umbrella.specification)

    # Edit Output Section
    umbrella.edit_output()

    # pp.pprint(umbrella_specification)

    if click.confirm("Would you like to edit your environmental variables?"):
        umbrella.edit_environ()

    pp.pprint(umbrella.specification)

if __name__ == "__main__":
    creator()
