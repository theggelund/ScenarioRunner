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


def test_when_multiple_actions_correct_action_is_executed(tmp_path: pathlib.Path):
    cmd = 'files/echo.sh'
    cmd2 = 'files/echo2.sh'

    if platform.system() == 'Windows':
        cmd = 'files\\echo.bat'
        cmd2 = 'files\\echo2.bat'

    tmp_file = tmp_path / "output"

    config = f'''
scenarios:
  abc:
    actions:
      - shell:
          cmd: {cmd}
          args: {tmp_file}
  def:
    actions:
      - shell:
          cmd: {cmd2}
          args: {tmp_file}
    '''

    config = yaml.load(config, Loader=yaml.FullLoader)
    parser = ScenarioRunner.initiate(config)

    args = parser.parse_args(['def'])
    response: ScenarioRunner.Result = args.func(args)

    assert response.return_code == 0
    assert tmp_file.read_text().rstrip(' \r\n') == "def"


