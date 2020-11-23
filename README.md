# Scenario Runner (sr)

You could use a shell script, it's more advanced or you could use scenario runner.

Install with
```pip install scenario-runner```

Create a file named 'sr.yml' in a directory where you want it to run. 
```yaml
scenarios:
  run_my_tests:
    description: 'Run all my tests'
    actions:
      - docker-compose:
          compose_files:
            - 'docker/docker-compose.yml'
            - 'docker/test.docker-compose.yml'
          cmd: up
          args: 
            - '--force-recreate'
            - '-d'
            - '--abort-on-container-exit'
            - '--exit-code-from'
            - 'test'
```

Then you run the scenario with `sr run_my_tests`

## Structure of sr.yml

```yaml

key: value

scenarios:    # all the scenarios with name as key
  scenario_name:
    description: 'Describe the scenario. This can be viewed by running sr --help
    actions:     # all the actions in the scenario as a list
      - action_type:
          ...
```

## Action types

__docker-compose__

| key | description |
| :- | :- |
| compose_files | All compose files used when running docker-compose. Can be specified in action, scenario or globally |
| cmd | docker-compose [cmd] to run. See docker-compose --help for available commands |
| args | Arguments for docker-compose after cmd. Can be a list of strings or string |

__shell__

| key | description |
| :- | :- |
| cmd | cmd to run |
| args | args for cmd. Can be a list of strings or string |
