import argparse
import os.path

import oyaml as yaml


def parse_constraint(con_str):
    # sample: (0,1):(1,1,1)
    agents_str, coefficients_str = con_str.split(':')
    x, y = agents_str.replace('(', '').replace(')', '').split(',')
    a, b, c = coefficients_str.replace('(', '').replace(')', '').split(',')
    func = f'{a} * var{x}**2 + {b} * var{x} * var{y} + {c} * var{y}**2'
    differentials = {
        f'var{x}': f'2 * {a} * var{x} + {b} * var{y}',
        f'var{y}': f'{b} * var{x} + 2 * {c} * var{y}'
    }
    return func, differentials


def main(args):
    lines_4_config = {}
    with open(args.file, 'r') as f:
        line = f.readline()
        while line:
            kv = line.split('=')
            lines_4_config[kv[0]] = kv[1].strip()
            line = f.readline()

    yaml_dict = {
        'name': args.name,
        'objective': 'min',
    }

    # domains
    domains = {}
    domain_info = lines_4_config['domains'].split(' ')
    agent_ids = []
    for domain_str in domain_info:
        agent_id, dvals = domain_str.split(':')
        domains[f'd{agent_id}'] = {
            'values': [int(v) for v in dvals.split(',')],
        }
        agent_ids.append(agent_id)
    yaml_dict['domains'] = domains

    # variables
    variables = {}
    for agent in agent_ids:
        variables[f'var{agent}'] = {
            'domain': f'd{agent}',
        }
    yaml_dict['variables'] = variables

    # constraints
    constraints = {}
    for con in lines_4_config['cons'].split('>'):
        eq1, differentials = parse_constraint(con)
        constraints[f'c{len(constraints)}'] = {
            'type': 'intention',
            'function': eq1,
            'differentials': differentials,
        }
    yaml_dict['constraints'] = constraints

    # agents
    agents = {f'a{agent_id}': {'id': agent_id} for agent_id in agent_ids}
    yaml_dict['agents'] = agents

    # export to yaml
    os.makedirs('./yaml-files', exist_ok=True)
    exported_file = args.file.split('/')[-1] + '.yaml'
    yaml_file = os.path.join('./yaml-files', exported_file)
    with open(yaml_file, 'w') as f:
        yaml.dump(yaml_dict, f)
        print(f'Simulation config file saved: {yaml_file}')

    # create scenario file
    events = [{
        'id': 'w0',
        'delay': 1,
    }]
    for i, cmd in enumerate(lines_4_config['commands'].split(' ')):
        if 'add_agent' in cmd or 'remove_agent' in cmd:
            cmd, agent = cmd.split(':')
            events.append({
                'id': f'e{i}',
                'actions': [{
                    'type': cmd,
                    'agent': f'a{agent}'
                }]
            })
            events.append({
                'id': f'w{i + 1}',
                'delay': 12,
            })

    scenarios = {'events': events}
    exported_file = args.file.split('/')[-1] + '-scenario.yaml'
    yaml_file = os.path.join('./yaml-files', exported_file)
    with open(yaml_file, 'w') as f:
        yaml.dump(scenarios, f)
        print(f'Simulation scenario file saved: {yaml_file}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert DynaGraph sim file to pyDCOP compatible yaml config')
    parser.add_argument('-f', '--file', type=str, required=True, help='sim file path')
    parser.add_argument('-n', '--name', type=str, required=True, help='DCOP name')

    args = parser.parse_args()

    main(args)
