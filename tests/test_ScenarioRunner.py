import os, sys, platform

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest, pathlib, yaml
from sr import ScenarioRunner


def test_can_run_shell(tmp_path: pathlib.Path):
    cmd = 'ifconfig'

    if platform.system() == 'Windows':
        cmd = 'ipconfig'

    config = f'''
scenarios:
  abc:
    actions:
      - shell:
          cmd: {cmd}
    '''

    config = yaml.load(config, Loader=yaml.FullLoader)
    parser = ScenarioRunner.initiate(config)

    args = parser.parse_args(['abc'])
    response: ScenarioRunner.Result = args.func(args)

    assert response.return_code == 0

