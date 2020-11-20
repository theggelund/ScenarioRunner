import argparse
import os
import subprocess
import sys
import yaml


def load_configuration(filename: str):
    with open(filename) as file:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        return yaml.load(file, Loader=yaml.FullLoader)


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


def execute(command_line):
    response = None

    try:
        print(f'Executing {command_line}')
        response = subprocess.run(command_line)
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        print(f"Command failed with {ex}")

    if response is not None and response.returncode != 0:
        print(f'Exitcode: {response.returncode}')
        return response.returncode


def parse_args(input_value, output: list, name: str):
    if input_value is None:
        return

    if type(input_value) is str:
        output.append(input_value)
    elif type(input_value) is list:
        output.extend(input_value)
    else:
        raise Exception(f"'{name}' supports only string or list")


def invoke_shell(args, action_config, scenario_config):
    command_line = []

    parse_args(action_config.get('cmd'), command_line, 'cmd')
    parse_args(action_config.get('args'), command_line, 'args')

    return execute(command_line)


def invoke_docker_compose(args, action_config, scenario_config):
    command = action_config.get('cmd')
    if command is None or type(command) is not str:
        raise KeyError("cmd must be specified for docker-compose and must be a string")

    command_line = ['docker-compose']

    # combine global, scenario and action compose_files
    compose_files = scenario_config.get('compose_files')
    if compose_files is None:
        compose_files = action_config.get('compose_files')
        if compose_files is None:
            print(f"'compose_files' must be specified either globally, in scenario or in action")
            raise ValueError()

    for file in compose_files:
        command_line.extend(['-f', file])

    command_line.append(command)

    parse_args(action_config.get('args'), command_line, 'args')

    return execute(command_line)


def invoke(args, scenario_config: dict):
    actions = scenario_config.get('actions')
    if actions is None:
        print(f'No actions specified for scenario {args.prog}')
        return

    try:
        for action_config in actions:
            action_result = None

            if action_config.get('docker-compose') is not None:
                action_result = invoke_docker_compose(args, action_config.get('docker-compose'), scenario_config)
            elif action_config.get('shell') is not None:
                action_result = invoke_shell(args, action_config.get('shell'), scenario_config)
            else:
                print(f'Unable to run action for {action_config}')

            if action_result is not None:
                if action_result != 0:
                    return action_result

    except Exception as ex:
        print(f"Failed {ex}")


def main():
    config = load_configuration(os.path.join(os.path.curdir, 'sr.yml'))
    parser = argparse.ArgumentParser(prog='sr', description='Run preconfigured scenarios')

    global_config = config.get('global')
    if global_config is None:
        global_config = {}

    scenarios = config.get('scenarios')
    if scenarios is None:
        raise ValueError('No scenarios specified')

    subparsers = parser.add_subparsers(title='Available scenarios')

    for scenario_name in scenarios:
        scenario_config = merge_dictionaries(scenarios[scenario_name], global_config)

        parser_args = {'prog': scenario_name, 'description': scenario_config.get('description')}

        scenario_parser = subparsers.add_parser(scenario_name, **parser_args)

        scenario_parser.set_defaults(func=lambda cmd_args, cfg=scenario_config: invoke(args, cfg))

    if len(sys.argv) < 2:
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args()
    args.func(args)
