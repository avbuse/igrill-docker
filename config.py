from builtins import object
import logging
import os
import yaml
from yamlreader import yaml_load
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import SingleQuotedScalarString

def sync_env_vars_with_config(config_directory):
    env_vars = [
        'device_name', 'device_address', 'device_type', 'device_topic', 'device_interval', 
        'mqtt_host', 'mqtt_port', 'mqtt_auth_username', 'mqtt_auth_password'
    ]
    mqtt_vars = {}
    device_vars = {}

    for var in env_vars:
        value = os.getenv(var)
        if value is not None:
            if var.startswith('mqtt'):
                mqtt_vars[var.replace('mqtt_', '')] = value
            else:
                device_vars[var.replace('device_', '')] = value

    print(f"mqtt_vars: {mqtt_vars}")
    print(f"device_vars: {device_vars}")

    yaml = YAML()

    # Load the config requirements
    from utils import config_requirements

    for filename, vars_dict in [('mqtt.yaml', mqtt_vars), ('device.yaml', device_vars)]:
        filepath = os.path.join(config_directory, filename)
        with open(filepath, 'r') as file:
            template = yaml.load(file) or {}

        print(f"Original template for {filename}: {template}")

        # Check the variable types and save them into the file accordingly
        for key, value in vars_dict.items():
            if filename == 'mqtt.yaml':
                specs = config_requirements['children']['mqtt']['specs']
            elif filename == 'device.yaml':
                specs = config_requirements['children']['devices']['specs']

            required_entries = specs['required_entries']
            optional_entries = specs.get('optional_entries', {})

            if key in required_entries:
                if required_entries[key] == int:
                    vars_dict[key] = int(value)
                elif required_entries[key] == bool:
                    vars_dict[key] = value.lower() == 'true'
                elif required_entries[key] == str:
                    vars_dict[key] = SingleQuotedScalarString(value)
            elif key in optional_entries:
                if optional_entries[key] == int:
                    vars_dict[key] = int(value)
                elif optional_entries[key] == bool:
                    vars_dict[key] = value.lower() == 'true'
                elif optional_entries[key] == str:
                    vars_dict[key] = SingleQuotedScalarString(value)

        if filename == 'device.yaml':
            template['devices'] = [vars_dict]
        elif filename == 'mqtt.yaml':
            template['mqtt'] = vars_dict

        with open(filepath, 'w') as file:
            yaml.dump(template, file)

        print(f"Updated template for {filename}: {template}")
                            
def read_config(config_path, defaults):
    """Read config file from given location, and parse properties"""
    if not os.path.isdir(config_path):
        raise ValueError("{0} is not a directory".format(config_path))

    try:
        return yaml_load(config_path, defaults)
    except yaml.YAMLError:
        logging.exception("Failed to read YAML config from directory: {0}".format(config_path))


def strip_config(config, allowed_keys):
    return {k: v for k, v in config.items() if k in allowed_keys and v}


class Config(object):
    config = None

    def __init__(self, config_path, requirements, defaults):
        self.config = read_config(config_path, defaults)
        self.requirements = requirements
        self.valid = self.validator[type(self.config)](self, 'Base', self.config, self.requirements)

    def parse_config(self, config, requirements):
        return

    def validate_and_strip_dict(self, key, config_dict, config_requirements):
        specs = config_requirements['specs']
        required_entries = specs.get('required_entries', {})
        optional_entries = specs.get('optional_entries', {})
        config_dict = strip_config(config_dict, list(required_entries.keys()) + list(optional_entries.keys()))

        logging.debug("Validating dict {0} with specs: {1}".format(config_dict, specs))
        valid = True
        for required_key, required_type in required_entries.items():
            if required_key in config_dict:
                if not isinstance(config_dict[required_key], required_type):
                    logging.error("Config validation failed: Value of \'{0}\' must be {1}, was {2}".format(required_key, required_type,
                                                                                                           type(config_dict[
                                                                                                                    required_key])))
                    valid = False
            else:
                logging.error("Config validation failed: Missing required field \'{0}\' in \'{1}\'".format(required_key, key))
                valid = False

        for optional_key, optional_type in optional_entries.items():
            if optional_key in config_dict and not isinstance(config_dict[optional_key], optional_type):
                logging.error(
                    "Config validation failed: Value of optional entry \'{0}\' must be {1}, was {2}".format(optional_key, optional_type,
                                                                                                            type(config_dict[
                                                                                                                     optional_key])))
                valid = False

        if 'children' in config_requirements:
            for child_key, child_value in config_requirements['children'].items():
                if valid and child_key in config_dict:
                    valid = self.validator[type(config_dict[child_key])](self, child_key, config_dict[child_key], child_value)
        return valid

    def validate_list(self, key, value_list, specs):
        logging.debug("Validating list {0} with specs: {1}".format(value_list, specs))
        valid = True
        if 'minimum' in specs and len(value_list) < specs['minimum']:
            logging.error("Config validation failed: \'{0}\' needs to have at least {1} entries".format(key, specs['minimum']))
            valid = False

        for value in value_list:
            if valid:
                valid = self.validator[type(value)](self, key, value, specs)

        return valid

    validator = {dict: validate_and_strip_dict,
                 list: validate_list}

    def isvalid(self):
        return self.valid

    def get_config(self, key=None):
        if not key:
            return self.config
        elif key and key in self.config:
            return self.config[key]
        else:
            raise ValueError("Key {} not in config".format(key))
