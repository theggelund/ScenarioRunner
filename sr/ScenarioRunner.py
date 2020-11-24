import argparse
import os
import subprocess
import sys
import yaml
import shlex
import platform


class Result:
    def __init__(self, return_code = 0):
        self.return_code = return_code


def dict_or_empty(input: dict):
    if input is None:
        return {}

    return input


def load_configuration(filename: str):
    with open(filename) as file:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        return yaml.load(file, Loader=yaml.FullLoader)


def write_to_file(filename: str, content):
    with open(filename, "w") as file:
        file.write(content)


def merge_lists(a: list, b: list):
    if b is None:
        return list(a)

    return list(set(a + b))


def merge_dictionaries(a: dict, b: dict):

    if b is None:
        return dict(a)

    result = {}

    for i, key in enumerate(a):
        a_value = a[key]
        b_value = b.get(key)

        if b_value is None:
            result[key] = a_value
            continue

        if type(a_value) is dict:
            result[key] = merge_dictionaries(a_value, b_value)
            continue

        if type(a_value) is list:
            result[key] = merge_lists(a_value, b_value)

    return result


def execute(command_line, action_config, env: dict = None):
    response = None
    capture_output = False

    stdout_file = action_config.get('stdout_file')
    stderr_file = action_config.get('stderr_file')

    expected_exitcode = action_config.get('exitcode')
    if expected_exitcode is None:
        expected_exitcode = 0

    if stdout_file is not None or stderr_file is not None:
        capture_output = True

    try:
        print(f'Executing {command_line}')
        response = subprocess.run(command_line, capture_output=capture_output, env=env)
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        print(f"Command failed with {ex}")

    if response is None:
        raise Exception('An error occured while executing command')

    if response.returncode != expected_exitcode:
        raise Exception(f'Exitcode: {response.returncode}')

    if stdout_file is not None:
        write_to_file(stdout_file, response.stdout)

    if stderr_file is not None:
        write_to_file(stderr_file, response.stderr)

    return response


def parse_args(input_value, output: list, name: str, required: bool = False):
    posix = platform.system() != 'Windows'

    if input_value is None and required:
        raise Exception(f"Missing '{name}'. Must be either string og list")
    elif input_value is None:
        return

    if type(input_value) is str:
        output.extend(shlex.split(input_value, posix=posix))
    elif type(input_value) is list:
        for input_item in input_value:
            output.extend(shlex.split(input_item, posix=posix))
    else:
        raise Exception(f"'{name}' supports only string or list")


def invoke_shell(args, action_config, scenario_config, global_config):
    command_line = []

    env = merge_environment_variables(action_config, global_config, scenario_config)

    parse_args(action_config.get('cmd'), command_line, 'cmd')
    parse_args(action_config.get('args'), command_line, 'args')

    return execute(command_line, action_config, env)


def merge_environment_variables(action_config, global_config, scenario_config):
    return {
        **os.environ,
        **dict_or_empty(global_config.get('env')),
        **dict_or_empty(scenario_config.get('env')),
        **dict_or_empty(action_config.get('env'))}


def extend_when_not_null(list: list, value):
    if value is not None:
        list.extend(value)


def invoke_docker_compose(args, action_config, scenario_config, global_config):
    command_line = ['docker-compose']

    env = merge_environment_variables(action_config, global_config, scenario_config)

    # combine global, scenario and action compose_files
    compose_files = []

    extend_when_not_null(compose_files, global_config.get('compose_files'))
    extend_when_not_null(compose_files, scenario_config.get('compose_files'))
    extend_when_not_null(compose_files, action_config.get('compose_files'))

    if len(compose_files) == 0:
        print("'compose_files' must be specified either globally, in scenario or in action")
        raise ValueError()

    for file in compose_files:
        command_line.extend(['-f', os.path.normpath(file)])

    parse_args(action_config.get('cmd'), command_line, 'cmd')
    parse_args(action_config.get('args'), command_line, 'args')

    return execute(command_line, action_config, env)


def invoke(args, scenario_config: dict, global_config: dict):
    actions = scenario_config.get('actions')

    if actions is None:
        print(f'No actions specified for scenario {args.prog}')
        return None

    for action_config in actions:
        action_result = None

        try:
            if action_config.get('docker-compose') is not None:
                action_result = invoke_docker_compose(
                    args,
                    action_config.get('docker-compose'),
                    scenario_config,
                    global_config)

            elif action_config.get('shell') is not None:
                action_result = invoke_shell(
                    args,
                    action_config.get('shell'),
                    scenario_config,
                    global_config)
            else:
                print(f'Unable to run action for {action_config}')

        except Exception as ex:
            print(f"Failed running action. Error {ex}")
            return Result(-1)

        if action_result is None:
            continue

        if action_result.returncode != 0:
            break

    return Result(action_result.returncode)


def initiate(configuration: dict):
    parser = argparse.ArgumentParser(prog='sr', description='Run preconfigured scenarios')

    global_config = configuration.get('global')
    if global_config is None:
        global_config = {}

    scenarios = configuration.get('scenarios')
    if scenarios is None:
        raise ValueError('No scenarios specified')

    subparsers = parser.add_subparsers(title='Available scenarios')

    for scenario_name in scenarios:
        scenario_config = scenarios[scenario_name]

        parser_args = {'prog': scenario_name, 'description': scenario_config.get('description')}

        scenario_parser = subparsers.add_parser(scenario_name, **parser_args)

        method = lambda cmd_args, s_cfg=scenario_config, g_cfg=global_config: invoke(cmd_args, s_cfg, g_cfg)

        scenario_parser.set_defaults(func=method)

    return parser


# expects first argument at sys_args[1] 
def main_with_args(sys_args: list):
    if len(sys_args) >= 3 and sys_args[1] == '--file':
        configuration_path = sys_args[2]

        if not os.path.isfile(configuration_path):
            raise FileExistsError(f"File '{configuration_path}' does not exist")

        os.chdir(os.path.dirname(configuration_path))

        sys_args = sys_args[3:]
    else:
        sys_args = sys_args[1:]

        configuration_path = os.path.join(os.getcwd(), 'sr.yml')

        if not os.path.isfile(configuration_path):
            raise FileExistsError(f"File '{configuration_path}' does not exist")

    configuration = load_configuration(configuration_path)
    parser = initiate(configuration)

    if len(sys_args) < 1:
        parser.print_usage()
        return -1

    args = parser.parse_args(sys_args)
    response = args.func(args)

    return response.return_code


def main():
    return main_with_args(sys.argv)
