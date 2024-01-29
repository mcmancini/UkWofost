# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), December 2023
# ========================================================
"""
Define a general Crop class to initialise any crop with associated
agromanagment. This could be a standard agromanagement (contained
in a yaml file to be parsed with the ConfigReader in config_parser.py)
"""
import datetime as dt
import yaml


class Crop:
    """
    General crop class that includes standard agromanagement
    which can be altered if in a rotation, or due to
    specific farm management practices. This class handles
    both arable crops and grasslands (for the time being only
    rye grass has been parametrised). A crop is instantiated
    as follows: wheat = Crop(2023, 'wheat', **wheat_args)
    ------------------------------------------------------------
    The required parameters are as follows:
    : param calendar_year: the year in which the crop is grown.
            For a winter crop, the calendar year is the year in
            which the crop is established in the ground; harvest
            will happen the following year. For spring crops,
            the entire crop cycle happens in the calendar_year.
    : param crop: name of the crop to be cultivated. It needs to
            match the name of any of the parametrised WOFOST crops
    : param **kwargs: these are key-value pairs of parameters, some
            of which are required, some optional.
    - Required **kwargs:
    : param 'variety': required only for arable crops and grassland,
        but not for 'fallow' crop. The variety name must match
        the varieties included in the parametrised WOFOST crops.
    - Optional **kwargs:
    : param 'apply_npk': a list of dictionaries containing
            fertilisation events defined as follows:
            kwargs['apply_npk'] = [npk_1, ...] where
            npk_1 = {
                'month': 5,
                'day': 1,
                'N_amount': 40, #kg/ha
                'P_amount': 40, #kg/ha
                'K_amount': 40  #kg/ha
            }
            Multiple fertilisation events can be defined
    : param 'mowing': for grassland. A list of dictionaries
            containing grass defoliation events defined as follows:
            kwargs['mowing'] = [mowing_1, ...] where
            mowing_1 = {
                'month': 5,
                'day': 1,
                'biomass_remaining': 320 #kg/ha
            }
            Multiple grass defoliation events can be defined.
    : param 'num_years' for grassland: Duration in years of the grassland
            crop. If grass is in a rotation with other crops, then the crops
            after grassland need to be planted after 'num_years' of the grassland
    Any other aprameter in the agromanagement can be overwritten: e.g.:
    : param 'crop_start_date': sowing date of a crop (dt.date format)
    : param 'crop_end_date': harvest time if timed, rather than dependent
            on the phenological development of the crop
    : param 'max_duration': max duration of the crop in days
    : params 'TimedEvents': list of events defined by their timing
    : params 'StateEvents': list of events depending on phenology rather than
             timing. More information on agromanagment can be found at
             https://tinyurl.com/bdcmj5b7
    """

    DEFAULT_ARGS = {"TimedEvents": "Null"}

    def __init__(self, calendar_year, crop, **kwargs):
        self.crop = crop
        self.crop_type = self._categorize_crop()
        self.calendar_year = calendar_year
        self.agromanagement = self._generate_agromanagement(**kwargs)

    # pylint: disable=R0914, R0912
    def _generate_agromanagement(self, **kwargs):
        """
        Generate agromanagement data for a specified crop. This includes
        crop calendar year, sowing timing, and timing of agromanagement
        practices (fertilisation, mowing, irrigation). Agromanagement
        events can be define thrugh **kwargs or can be default ones for
        specified crops. Defaults are contained in the config.py file, and
        called in the creation of crop instances
        """
        args = self.DEFAULT_ARGS.copy()
        args.update(kwargs)

        # Variety
        if self.crop.lower() != "fallow":
            if "variety" not in args or args["variety"] is None:
                raise ValueError("Missing argument: 'variety' argument is required.")
            self.variety = args["variety"]
        else:
            self.variety = None

        # Start of the crop
        if "crop_start_date" not in args:
            if "crop_start_month" not in args and "crop_start_day" not in args:
                raise ValueError(
                    f"Please provide a crop start date for {self.crop} as "
                    f"kwargs['crop_start_day'] and kwargs['crop_start_month'] or "
                    f"kwargs['crop_start_date']"
                )
            start_crop_calendar = dt.date(
                self.calendar_year, args["crop_start_month"], 1
            )
            crop_start_date = dt.date(
                self.calendar_year,
                args["crop_start_month"],
                args["crop_start_day"],
            )
            args["start_crop_calendar"] = start_crop_calendar
            args["crop_start_date"] = crop_start_date
        else:
            crop_start_date = args["crop_start_date"]
            args["start_crop_calendar"] = dt.date(
                crop_start_date.year, crop_start_date.month, 1
            )

        event_types = {
            "apply_npk": {
                "event_signal": "apply_npk",
                "name": "Timed N/P/K application table",
                "comment": "All fertilizer amounts in kg/ha",
                "line_template": (
                    "- {timing}: {{N_amount: {event[N_amount]}, "
                    "P_amount: {event[P_amount]}, K_amount: {event[K_amount]}}}"
                ),
            },
            "mowing": {
                "event_signal": "mowing",
                "name": "Schedule a grass mowing event",
                "comment": "Remaining biomass in kg/ha",
                "line_template": (
                    "- {timing}: {{biomass_remaining: {event[biomass_remaining]}}}"
                ),
            },
        }

        event_yaml_lines = []

        for event_type, event_data in event_types.items():
            if event_type in args and args[event_type] is not None:
                event_lines = []
                for event in args[event_type]:
                    timing = self._def_timing_event(
                        self.variety, args["crop_start_date"], event
                    )
                    line = event_data["line_template"].format(
                        timing=timing, event=event
                    )
                    event_lines.append(line)
                events_table = "\n                    ".join(event_lines)

                event_yaml = f"""
                -   event_signal: {event_data['event_signal']}
                    name: {event_data['name']}
                    comment: {event_data['comment']}
                    events_table:
                    {events_table}
                """
                event_yaml_lines.append(event_yaml)

        # Combine all event YAMLs
        events_yaml = "\n".join(event_yaml_lines)

        # Combine all in agromanagement
        if self.crop != "fallow":
            _agromanagement_yaml = f"""
            - {args['start_crop_calendar']}:
                CropCalendar:
                    crop_name: {self.crop}
                    variety_name: {self.variety}
                    crop_start_date: {args['crop_start_date']}
                    crop_start_type: sowing
                    crop_end_date:
                    crop_end_type: {args['crop_end_type']}
                    max_duration: {args['max_duration']}
                TimedEvents:
                    {events_yaml}
                StateEvents: Null
            """
        else:
            _agromanagement_yaml = f"""
            - {args['start_crop_calendar']}:
                CropCalendar: null
                TimedEvents: null
                StateEvents: null
            """

        # Remove empty lines
        _agromanagement_yaml = "\n".join(
            [line for line in _agromanagement_yaml.split("\n") if line.strip()]
        )
        return _agromanagement_yaml

    # pylint: enable=R0914, R0912
    @staticmethod
    def _def_timing_event(variety, crop_start_date, event):
        """
        Generate date of timing event combining calendar year of a crop and
        timing (month and day) passed trough crop **kwargs. These can be
        fertilisation, mowing or irrigation events.
        """
        if "winter" in variety.lower():
            if "date" not in event:
                timing = dt.date(crop_start_date.year + 1, event["month"], event["day"])
            else:
                timing = event["date"]
        else:
            if "date" not in event:
                timing = dt.date(crop_start_date.year, event["month"], event["day"])
                if timing < crop_start_date:
                    # this deals with a crop calendar year starting in the fall and
                    # timing events in the following year
                    timing = timing.replace(year=timing.year + 1)
            else:
                timing = event["date"]
        return timing

    @property
    def crop_type(self):
        """
        Define crop type (arable crop or grass) from name
        """
        return self._crop_type

    @crop_type.setter
    def crop_type(self, value):
        self._crop_type = value

    def _categorize_crop(self):
        """
        Assign crop type based on input: either crop, grass, or fallow
        """
        if "grass" in self.crop.lower():
            return "grass"
        return "crop"

    def __str__(self):
        msg = "======================================================\n"
        msg += "               Crop characteristics\n"
        msg += "---------------------Description----------------------\n"
        msg += "Crop: " + self.crop + "\n"
        if self.variety is not None:
            msg += "Variety: " + self.variety + "\n"
        msg += "Crop type: " + self.crop_type + "\n"
        msg += "-------------------Agro-management--------------------\n"
        msg += self.agromanagement

        return msg


class CropRotation:
    """
    Class generating crop rotations combining agromanagement
    from a succession of crops and/or grasses
    --------------------------------------------------------
    The required parameters are as follows:
    : param crop: a list of instances of the class
            'Crop' with associated agromanagemnets and
            timings. Rotations do not have a limit in the
            number of crops that they can contain.
    """

    def __init__(self, crops):
        self.rotation = yaml.safe_load(self._generate_rotation(crops))
        self.crop_list = self._list_crops()
        self.yaml_rotation = self._generate_rotation(crops)

    def _generate_rotation(self, crops):
        rotation_yaml = ""
        for crop in crops:
            rotation_yaml += crop.agromanagement + "\n"
        return rotation_yaml

    def _list_crops(self):
        crops = self.find_value("crop_name")
        varieties = self.find_value("variety_name")
        return [{crop: variety} for crop, variety in zip(crops, varieties)]

    def find_value(self, key):
        """
        Find value associated to 'key', if existing
        """
        result = self._recursive_search(self.rotation, key)
        if result is None:
            print(f"Key '{key}' not found in the dictionary.")
        return result

    def _recursive_search(self, data, key):
        """
        Recursive search into yaml_dict to find specified key
        regardless of level of nesting into yaml_dict
        """
        results = []

        if isinstance(data, dict):
            for k, v in data.items():
                if k == key:
                    results.append(v)
                elif isinstance(v, (dict, list)):
                    results.extend(self._recursive_search(v, key))

        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    results.extend(self._recursive_search(item, key))

        return results

    def __str__(self):
        msg = "======================================================\n"
        msg += "               Rotation characteristics\n"
        msg += "---------------------Description----------------------\n"
        crop_succession = ", ".join(
            ", ".join(crop_dict.keys()) for crop_dict in self.crop_list
        )
        msg += "Crop succession: " + crop_succession + "\n"
        crop_varieties = ", ".join(
            ", ".join(crop_dict.values()) for crop_dict in self.crop_list
        )
        msg += "Crop varieties: " + crop_varieties + "\n"
        msg += "======================================================\n\n"
        msg += self.yaml_rotation
        return msg
