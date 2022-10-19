import os
import yaml
import json_generation
import json
import pytest


with open("./config.yaml", "r") as yml:
    cfg = yaml.full_load(yml)
    test_datadir = cfg['tests']['test_data_dir']
    compare_jsondir = cfg['tests']['compare_jsons_dir']
    test_dicomjson_dir = cfg['tests']['test_dicomjson_dir']
    test_modeljson_dir = cfg['tests']['test_modeljson_dir']
    model_json_file = cfg['tests']['model_json_file']
    patient_json_file = cfg['tests']['patient_json_file']
    imaging_json_file = cfg['tests']['imaging_json_file']


@pytest.mark.parametrize('hlist',['[122]','[169]','[663]','[709]','[712]','[724]','[836]'])
def test_jsongen(hlist):
    class Namespace:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    args = Namespace(database='dev2', dataclass='general', datadir=test_datadir, basejsondir=None, dbupload=False, file=None, hlist=hlist, jsondir=compare_jsondir, only_models=False)
    json_generation.backbone_caller(args)

    human_id = f"{int(eval(hlist)[0]):05}"
    series = os.listdir(os.path.join(test_dicomjson_dir,human_id))
    for ser in series:
        with open(os.path.join(test_dicomjson_dir,human_id,ser,imaging_json_file), 'r') as f:
            img_dict1 = json.load(f)
            del img_dict1['datetime_creation']
            del img_dict1['URI']
        with open(os.path.join(compare_jsondir,human_id,ser,imaging_json_file), 'r') as f:
            img_dict2 = json.load(f)
            del img_dict2['datetime_creation']
            del img_dict2['URI']
        with open(os.path.join(test_dicomjson_dir,human_id,ser,patient_json_file), 'r') as f:
            pat_dict1 = json.load(f)
            del pat_dict1['datetime_creation']
        with open(os.path.join(compare_jsondir,human_id,ser,patient_json_file), 'r') as f:
            pat_dict2 = json.load(f)
            del pat_dict2['datetime_creation']

        for i,j in zip(img_dict1,img_dict2):
            assert img_dict1[i] == img_dict2[j]
        for i,j in zip(pat_dict1,pat_dict2):
            assert pat_dict1[i] == pat_dict2[j]


@pytest.mark.parametrize('dataclass',['general','realheart'])
def test_jsongen_diffdataclass(dataclass):
    class Namespace:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    args = Namespace(database='dev2', dataclass=dataclass, datadir=test_datadir, basejsondir=None, dbupload=False, file=None, hlist='[836]', jsondir=compare_jsondir, only_models=False)
    json_generation.backbone_caller(args)

    human_id = f"{int(eval(args.hlist)[0]):05}"
    series = os.listdir(os.path.join(test_dicomjson_dir,human_id))
    for ser in series:
        with open(os.path.join(test_dicomjson_dir,human_id,ser,imaging_json_file), 'r') as f:
            img_dict1 = json.load(f)
            del img_dict1['datetime_creation']
            del img_dict1['URI']
        with open(os.path.join(compare_jsondir,human_id,ser,imaging_json_file), 'r') as f:
            img_dict2 = json.load(f)
            del img_dict2['datetime_creation']
            del img_dict2['URI']
        with open(os.path.join(test_dicomjson_dir,human_id,ser,patient_json_file), 'r') as f:
            pat_dict1 = json.load(f)
            del pat_dict1['datetime_creation']
        with open(os.path.join(compare_jsondir,human_id,ser,patient_json_file), 'r') as f:
            pat_dict2 = json.load(f)
            del pat_dict2['datetime_creation']

        for i,j in zip(img_dict1,img_dict2):
            assert img_dict1[i] == img_dict2[j]
        for i,j in zip(pat_dict1,pat_dict2):
            assert pat_dict1[i] == pat_dict2[j]


@pytest.mark.parametrize('hlist',['[3]','[6]','[104]','[190]','[702]','[818]'])
def test_modelsjsongen(hlist):
    class Namespace:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    args = Namespace(database='dev2', dataclass='general', datadir=test_datadir, basejsondir=None, dbupload=False, file=None, hlist=hlist, jsondir=compare_jsondir, only_models=False)
    json_generation.backbone_caller(args)

    args = Namespace(database='dev2', dataclass='general', datadir=test_datadir, basejsondir=compare_jsondir, dbupload=False, file=None, hlist=hlist, jsondir=compare_jsondir, only_models=True)
    json_generation.backbone_caller(args)

    human_id = f"{int(eval(hlist)[0]):05}"
    series = os.listdir(os.path.join(test_modeljson_dir,human_id))
    
    for ser in series:
        with open(os.path.join(test_modeljson_dir,human_id,ser,model_json_file), 'r') as f:
            model_dict1 = json.load(f)
            del model_dict1['datetime_creation']
        with open(os.path.join(compare_jsondir,human_id,ser,model_json_file), 'r') as f:
            model_dict2 = json.load(f)
            del model_dict2['datetime_creation']
        for i,j in zip(model_dict1,model_dict2):
            assert model_dict1[i] == model_dict2[j]
        
        with open(os.path.join(test_modeljson_dir,human_id,ser,model_json_file), 'r') as f:
            pat_dict1 = json.load(f)
            del pat_dict1['datetime_creation']
        with open(os.path.join(compare_jsondir,human_id,ser,model_json_file), 'r') as f:
            pat_dict2 = json.load(f)
            del pat_dict2['datetime_creation']
        for i,j in zip(pat_dict1,pat_dict2):
            assert pat_dict1[i] == pat_dict2[j]
        