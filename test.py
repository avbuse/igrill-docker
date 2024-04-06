import os
import yaml

def sync_env_vars_with_config(env_vars, config_directory):
    mqtt_vars = {}
    device_vars = {}

    for var in env_vars:
        key, value = var.split('=')
        if key.startswith('mqtt'):
            mqtt_vars[key] = value
        else:
            device_vars[key] = value

    for filename, vars_dict in [('mqtt.yaml', mqtt_vars), ('device.yaml', device_vars)]:
        filepath = os.path.join(config_directory, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as file:
                current_config = yaml.safe_load(file) or {}
            current_config.update(vars_dict)
            with open(filepath, 'w') as file:
                yaml.dump(current_config, file)
        else:
            with open(filepath, 'w') as file:
                yaml.dump(vars_dict, file)