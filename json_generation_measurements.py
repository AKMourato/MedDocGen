"""Script to generate measurement collections JSONs"""
import os
import sys
import json
import re
import argparse
from ast import literal_eval
import yaml
import pandas as pd
import numpy as np
import pyvista as pv


from main.utils.measurement_defaultdicts import (
    measurement_category_dict,
    measurement_collection_dict,
    measurement_type_dict,
)
from main.utils.helpers import (
    measurement_type_values,
    check_and_create_folder,
    sharepoint_download,
)

# arbitrary test function, will be pushed to Virtokit soon
def model_volume(path_to_model):
    """Function to calculate a model volume"""
    model = pv.read(path_to_model)
    return np.round(model.volume / 1000, 3)


def jsongen_parser():
    """
    Argparser function for the measurement JSON generation process.

    Args
    ----------
        jsondir (str) : JSON destination directory
        datadir (str, optional) :  Data directory
        categories (list): Categories list
        measurement (str): Measuerment type
        hlist (list, optional) :  Human list

    Return
    -------
        parser (:obj: Namespace)

    """

    parser = argparse.ArgumentParser(
        prog="json_generation",
        usage="%(prog)s [options]",
        description="Generate patient JSON files",
    )

    parser.add_argument(
        "--jsondir",
        metavar="JSON destination directory",
        help="the path to the directory where the JSONs will be created",
    )

    parser.add_argument(
        "--datadir",
        metavar="Data directory",
        default="/home/database/v-patients/",
        help="the absolute path to the patients DICOM directory",
    )

    parser.add_argument(
        "--categories",
        metavar="Category list",
        default=[],
        nargs="+",
        help="categories for categories collection",
    )

    parser.add_argument(
        "--measurement",
        metavar="Type of measurement",
        choices=["LV Volume"],
        help="see predefined measurements",
    )

    parser.add_argument(
        "--hlist",
        metavar="Human list",
        default=None,
        help="list containing the humans to be generated",
    )

    return parser


def measurement_jsongen(args):
    """
    Creates and saves measurement related JSONs

    Args
    ----------
    args: see jsongen_parser

    """

    # download database-dl to fill in timestamp
    with open("./config.yaml", "r") as yml:
        cfg = yaml.full_load(yml)

    sharepoint_download(
        cfg["sharepoint-download-credentials"],
        cfg["default-server-paths"]["database-dl"],
    )
    df = pd.read_excel(cfg["default-server-paths"]["database-dl"])
    df = df.replace(np.nan, "None")

    version = 1
    root_dir = args.datadir

    # test if human list is readable
    if args.hlist is not None:
        try:
            if not isinstance(literal_eval(args.hlist), list):
                sys.exit("Human list must be a list of integers")
        except TypeError:
            sys.exit("Human list must be a list of integers")
    patients = literal_eval(args.hlist)

    # measurement type collections needs some specifications based on the measurement
    type_values = measurement_type_values(args.measurement)

    # first create parent category
    check_and_create_folder(args.jsondir)

    # categories may already uploaded
    if args.categories != []:
        category_path = os.path.join(args.jsondir, "Category")
        check_and_create_folder(category_path)
        for i, category in enumerate(args.categories):
            measurement_category = measurement_category_dict(
                version=version, name=category
            )
            with open(
                os.path.join(category_path, "measurement_category_" + str(i) + ".json"),
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(measurement_category, file)

    # next create measurement type collection
    if type_values["name"] is not None:
        type_path = os.path.join(args.jsondir, "Type")
        check_and_create_folder(type_path)
        measurement_type = measurement_type_dict(
            version=version,
            name=type_values["name"],
            unit=type_values["unit"],
            is_categorical=type_values["is_categorical"],
            is_time_dependent=type_values["is_time_dependent"],
        )
        with open(
            os.path.join(type_path, "measurement_type.json"), "w", encoding="utf-8"
        ) as file:
            measurement_type = json.dumps(measurement_type)
            measurement_type = json.loads(measurement_type)
            json.dump(measurement_type, file)

    # lasty, create the measurements collections
    for patient in patients:
        print(patient)
        patient = f"{patient:05d}"
        models = os.listdir(os.path.join(root_dir, patient, "dec_models/"))
        models = [
            str
            for str in models
            if any(i in str for i in set([type_values["model_required"]]))
        ]
        # of more than one timestamp is there
        # timestamp will be shown  with _95 in filename
        for model in models:
            # timestamp given in model name?
            info = re.findall(r"\d+", model)
            if len(info) == 3:
                timestamp = float(info[2]) / 100
            else:
                # if not, check database-dl for ES/ED
                query = (
                    "PatientID =="
                    + str(float(info[0]))
                    + "& Series == "
                    + str(int(info[1]))
                )
                phase = df.query(query)["Phase"].iloc[0]

                if phase == "ED":
                    timestamp = 2
                elif phase == "ES":
                    timestamp = -1
                else:
                    return "No timestamp information for patient: " + patient

            # get the definded measurement
            if args.measurement == "LV Volume":
                value = model_volume(
                    os.path.join(root_dir, patient, "dec_models", model)
                )

            measurement_collection = measurement_collection_dict(
                value=value, timestamp=timestamp
            )

            # check if out_dir exists, if not create it
            patient_path = os.path.join(args.jsondir, patient)
            check_and_create_folder(patient_path)
            with open(
                os.path.join(
                    patient_path, "measurement_collection_" + str(timestamp) + ".json"
                ),
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(measurement_collection, file)


if __name__ == "__main__":
    arguments = jsongen_parser().parse_args()
    print("Command Line Interface Args:", arguments)
    measurement_jsongen(arguments)

#             _____
#           .'  |  `.
#          /    |    \
#         |-----|-----|
#          \    |    /
#           '.__|__.'
#              \|/
#               |
