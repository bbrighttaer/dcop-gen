import os


def convert_pdcop_to_pydcop(file_path):
    components_dict = _get_pdcop_components(file_path)

    print(components_dict)


def _get_pdcop_components(file_path):
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
                    vals = [eval(v) for v in values_to_util[:-1]]
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
