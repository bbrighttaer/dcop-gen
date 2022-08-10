import os
import random

import oyaml as yaml


def _convert_to_yaml_dict(components_dict):
    yaml_dict = {}
    domains = {}
    variables = {}
    constraints = {}

    # D-DCOP
    events = [{'id': 'w0', 'delay': 1}]
    scenario_dict = {
        'inputs': {
            'origin': 'pd-dcop-sim-file'
        },
        'events': events,
    }

    # decision variables
    for var, domain in components_dict['decision_vars']:
        domains[f'd_{var}'] = {'values': domain}
        variables[var] = {
            'domain': f'd_{var}',
            'type': 'decision'
        }

    # random variables
    random_var_events = []
    for var, domain in components_dict['random_vars']:
        domains[f'd_{var}'] = {'values': domain}
        variables[var] = {
            'domain': f'd_{var}',
            'type': 'random'
        }
        random_var_events += [(var, v) for v in domain]
    random.shuffle(random_var_events)
    events += [{
        'id': f'e{i+1}',
        'actions': [{'type': 'random-variable-change', 'variable_name': evt[0]}, {'id': f'w{i+1}', 'delay': 1}]
    } for i, evt in enumerate(random_var_events)]

    # constraints
    for constraint_name, constraint in components_dict['constraints'].items():
        constraints[constraint_name] = {
            'type': constraint['type'],
            'variables': constraint['variables'],
            'values': {
                util: ' | '.join([' '.join(group) for group in groups])
                for util, groups in constraint['values'].items()
            },
        }

    yaml_dict['domains'] = domains
    yaml_dict['variables'] = variables
    yaml_dict['constraints'] = constraints
    yaml_dict['initial_distributions'] = components_dict['initial_distributions']
    yaml_dict['transition_matrices'] = components_dict['transition_matrices']

    return yaml_dict, scenario_dict


def convert_pdcop_to_pydcop(file_path):
    file_name = file_path.split("/")[-1].split(".")[0]
    yaml_dict = {
        'name': f'pd-dcop_{file_name}',
        'objective': 'max'
    }
    components_dict = _get_pddcop_components(file_path)
    prob_def_dict, scenario_dict = _convert_to_yaml_dict(components_dict)
    yaml_dict.update(prob_def_dict)

    # export to yaml
    base_dir = './yaml-files'
    os.makedirs(base_dir, exist_ok=True)

    # prob definition
    exported_file = f'{file_name}.yaml'
    yaml_file = os.path.join(base_dir, exported_file)
    with open(yaml_file, 'w') as f:
        yaml.dump(yaml_dict, f)
        print(f'Simulation config file saved: {yaml_file}')

    # scenario definition
    yaml_file = os.path.join(base_dir, f'{file_name}.scenario.yaml')
    with open(yaml_file, 'w') as f:
        yaml.dump(scenario_dict, f)
        print(f'Scenario config file saved: {yaml_file}')


def _get_pddcop_components(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    # parsing
    components = text.split(';')
    components_dict = {
        'decision_vars': [],
        'random_vars': [],
        'constraints': {},
        'initial_distributions': {},
        'transition_matrices': {},
    }
    for component in components:
        # decision and random variables
        if 'decision' in component or 'random' in component:
            parts = component.split('=')
            var_name = parts[0].strip().split('_')[1]
            domain_bounds = eval(parts[1])
            domain = list(range(domain_bounds[0], domain_bounds[1] + 1))

            if 'decision' in component:
                components_dict['decision_vars'].append((var_name, domain))
            else:
                components_dict['random_vars'].append((var_name, domain))

        # constraints
        elif 'constraint' in component:
            parts = component.split('=')
            v1, v2 = parts[0].strip().split('_')[1:]
            constraint = {
                'type': 'extensional',
                'variables': [v1, v2],
            }
            value_mappings = parts[1].strip().removeprefix('[').removesuffix(']').split('|')
            val_table = {}
            for mapping in value_mappings:
                mapping = mapping.strip()
                if mapping:
                    values_to_util = mapping.split(',')
                    util = eval(values_to_util[-1])
                    vals = [v.strip() for v in values_to_util[:-1]]
                    if util in val_table:
                        val_table[util].append(vals)
                    else:
                        val_table[util] = [vals]

            constraint['values'] = val_table

            components_dict['constraints'][parts[0].strip()] = constraint

        # initial distributions
        elif 'initial_distribution' in component:
            parts = component.strip().split('=')
            components_dict['initial_distributions'][parts[0].split('_')[-1]] = eval(parts[1])

        # transition functions
        elif 'transition' in component:
            parts = component.strip().split('=')

            matrix = [eval(f'[{row}]') for row in parts[1].strip().removeprefix('[').removesuffix(']').split('|')[:-1]]

            components_dict['transition_matrices'][parts[0].split('_')[-1]] = matrix
    return components_dict


def main():
    base_dir = 'pdcop_input_files/meeting_x4_y2_dx5_dy5/'
    convert_pdcop_to_pydcop(os.path.join(base_dir, 'instance_0_x4_y2_dx5_dy5.dzn'))


if __name__ == '__main__':
    main()
