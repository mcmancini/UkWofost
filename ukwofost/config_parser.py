# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP - University of Exeter (UK)
# Mattia C. Mancini (m.c.mancini@exeter.ac.uk), September 2023
"""
Read an ini or json config file storing all the necessary
variables and parameters for setting the UK based implementation
of the WOFOST crop yield model
"""

import configparser
import json
import os
import yaml


# pylint: disable=R0903
class ConfigReader:
    """
    Class to parse and format a configuration file containing all
    the necessary parameters setting the database on fertilisation
    in the UK
    """

    def __init__(self, config_file_path):
        self._get_config(config_file_path)

    def get(self, value):
        """
        Method to retrieve any value from an instance of the ConfigReader object
        """
        return getattr(self, value, {})

    def _get_config(self, config_file_path):
        """
        Parse items from the config file (INI or JSON)
        :param config_file_path: The path of the configuration file
        """
        _, file_extension = os.path.splitext(config_file_path.lower())

        if file_extension == ".ini":
            self._parse_ini_config(config_file_path)
        elif file_extension == ".json":
            self._parse_json_config(config_file_path)
        elif file_extension == ".yaml":
            self._parse_yaml_config(config_file_path)
        else:
            raise ValueError("Unsupported file format")

    def _parse_ini_config(self, config_file_path):
        """
        Parse items from an .ini config file
        :param config_file_path: The path of the .ini configuration file
        """
        config = configparser.ConfigParser()
        config.read(config_file_path)
        for section_name in config.sections():
            section = config[section_name]
            section_dict = {
                key: os.path.expandvars(value) for key, value in section.items()
            }
            setattr(self, section_name, section_dict)

    def _parse_json_config(self, config_file_path):
        """
        Parse items from a .json config file
        :param config_file_path: The path of the .json configuration file
        """
        with open(config_file_path, "r", encoding="utf-8") as json_file:
            json_data = json.load(json_file)
        for key, value in json_data.items():
            setattr(self, key, value)

    def _parse_yaml_config(self, config_file_path):
        """
        Parse items from a .yaml config file
        :param config_file_path: The path of the .yaml configuration file
        """
        with open(config_file_path, "r", encoding="utf-8") as file:
            yaml_data = yaml.safe_load(file)
        for key, value in yaml_data.items():
            setattr(self, key, value)

    def __str__(self):
        """
        Format and return a string representation of the AppConfig object
        """
        result = ""
        for section_name in dir(self):
            if not callable(
                getattr(self, section_name)
            ) and not section_name.startswith("__"):
                result += f"[{section_name}]\n"
                section = getattr(self, section_name)
                for key, value in section.items():
                    result += f"{key} = {value}\n"
        return result


# pylint: enable=R0903
