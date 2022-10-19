import sys
import os
import json
import argparse
import shutil


def merge_parser():
    parser = argparse.ArgumentParser(
        prog="merge_acquisitions", usage="%(prog)s [options]"
    )

    parser.add_argument(
        "human_id", metavar="Human internal id", help="Human internal id, e.g: 369"
    )
    parser.add_argument(
        "-s",
        "--series",
        metavar="Series",
        nargs="+",
        default=None,
        help="Series to be merged, e.g: SER00003 SER00006 ",
    )
    parser.add_argument(
        "-b",
        "--basejsondir",
        metavar="Base JSON directory",
        default="/home/dev/jsons",
        help="the absolute path to the JSON directory where the original JSONs are.",
    )
    parser.add_argument(
        "-d",
        "--destjsondir",
        metavar="Destination JSON directory",
        default="/home/dev/jsons/",
        help="the absolute path to the JSON directory where the new JSONs will be created.",
    )
    parser.add_argument(
        "-m",
        "--models_dir",
        metavar="v-patients directory",
        default="/home/database/v-patients/",
        help="the absolute path to v-patients directory",
    )
    return parser


def merge(args):

    human_id = args.human_id
    series = args.series
    basejsondir = args.basejsondir
    destjsondir = args.destjsondir
    models_dir = args.models_dir

    human_id = f"{int(human_id):05}"
    if series is None:
        series = list(
            set(
                [
                    int((i.split("-")[1]).replace("ser", ""))
                    for i in os.listdir(
                        os.path.join(models_dir, human_id, "dec_models")
                    )
                    if "ser_merged" not in i
                ]
            )
        )
        if len(series) != 2:
            sys.exit("Error: {} serie(s) present in vpatients.".format(len(series)))
        series = ["SER" + f"{int(x):05}" for x in sorted(series)]

    s1_path = os.path.join(basejsondir, human_id, series[0])
    s2_path = os.path.join(basejsondir, human_id, series[1])
    s1_name = os.path.basename(s1_path)
    s2_name = os.path.basename(s2_path)
    # new folder name
    newser_name = (
        "SER_"
        + str(int(s1_name.replace("SER", "")))
        + "_"
        + str(int(s2_name.replace("SER", "")))
    )
    destser_dir = os.path.join(destjsondir, human_id, newser_name)
    os.makedirs(destser_dir, exist_ok=True)

    for i in os.listdir(s1_path):
        shutil.copyfile(os.path.join(s1_path, i), os.path.join(destser_dir, i))

    with open(os.path.join(destser_dir, "patient_collection.json"), "r") as f:
        patient_coll_dict = json.load(f)

    serlist = []
    for i in [s1_name, s2_name]:
        serlist.append(i)
    patient_coll_dict["internal_info"]["series"] = serlist

    with open(os.path.join(destser_dir, "model_collection.json"), "r") as f:
        model_coll_dict = json.load(f)

    with open(
        os.path.join(basejsondir, human_id, s2_name, "model_collection.json"), "r"
    ) as f:
        model_coll_dict_2 = json.load(f)

    t1 = []
    t2 = []
    for i, j in zip(model_coll_dict["models"], model_coll_dict_2["models"]):
        t1.append(i["timestamp"])
        t2.append(j["timestamp"])

    for i in t2:
        submodeldict = {"timestamp": i, "sub_models": [], "landmarks": []}
        if i not in t1:
            model_coll_dict["models"].append(submodeldict)

    for e1, i1 in enumerate(model_coll_dict_2["models"]):
        for e2, i2 in enumerate(model_coll_dict["models"]):
            if i1["timestamp"] == i2["timestamp"]:
                model_coll_dict["models"][e2]["sub_models"].extend(
                    model_coll_dict_2["models"][e1]["sub_models"]
                )

    with open(
        os.path.join(basejsondir, human_id, s2_name, "patient_collection.json"), "r"
    ) as f:
        patient_coll_dict_2 = json.load(f)

    if patient_coll_dict["ed_timestamp"] is None:
        patient_coll_dict["ed_timestamp"] = patient_coll_dict_2["ed_timestamp"]
        if (
            patient_coll_dict["ed_timestamp"] is None
            and patient_coll_dict["es_timestamp"] != -1
        ):
            print("Warning: check ed_timestamp.")

    if patient_coll_dict["es_timestamp"] is None:
        patient_coll_dict["es_timestamp"] = patient_coll_dict_2["es_timestamp"]
        if (
            patient_coll_dict_2["es_timestamp"] is None
            and patient_coll_dict["ed_timestamp"] != 2
        ):
            print("Warning: check es_timestamp.")

    with open(os.path.join(destser_dir, "patient_collection.json"), "w") as f:
        json.dump(patient_coll_dict, f)

    with open(os.path.join(destser_dir, "model_collection.json"), "w") as f:
        json.dump(model_coll_dict, f)


if __name__ == "__main__":
    args = merge_parser().parse_args()
    print("Command Line Interface Args:", args)
    merge(args)
    print("Operation successfull.")
