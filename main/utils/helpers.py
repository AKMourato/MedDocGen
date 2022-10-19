import os
import math
import shutil
from main.utils.matching_dict import heart_suffix, thorax_suffix
import json
from py_topping.data_connection.sharepoint import lazy_SP365
import time

def create_jsondirs(datadir,jsondir,humans):
    """
    Function to create the JSON destination directory and their subdirs according to the human IDs.

    Args
    ------
        datadir (str) :  Data directory
        jsondir (str) : JSON destination directory
        humans (list) :  list of human IDs
        
    """

    for i in humans:
        os.makedirs(os.path.join(jsondir,i), exist_ok=True)
        for std in os.listdir(os.path.join(datadir,i)):
            if std.startswith('STD'):
                for folder in os.listdir(os.path.join(datadir,i,std)):
                    os.makedirs(os.path.join(jsondir,i,folder), exist_ok=True)

    print('JSONs directory created.')


def calculate_bmi(patientdict):
    """
    Function to calculate the Body Mass Index (BMI) based on weight in kg and height in meter
    
    Args
    ------
        patientdict (dict) :  patient dict 
        
    Return
    ------
        None
        bmi (float) 

    """

    if patientdict['weight'] is None or patientdict['height'] is None:
        return None
    bmi = round(patientdict['weight']/math.pow(patientdict['height']/100, 2),2)
    if math.isnan(bmi):
        return None
    return bmi


def calculate_mosteller_bsa(patientdict):
    """    
    Calculate Mosteller Body Surface Area (BSA)[m2] based on weight in kg and height in centimeter
    
    Args
    ------
        patientdict (dict) :  patient dict 
        
    Return
    ------
        None
        bmi (float) 
    """
    if patientdict['weight'] is None or patientdict['height'] is None:
        return None
    bsa = round(math.sqrt(patientdict['weight']*patientdict['height']/3600),2)
    if math.isnan(bsa):
        return None
    return bsa

def structure_matching(human,folder,stl,submodel_info):
    """    
    Function to perform the organ structure matching between stls' suffix and standard model_names.    
    
    Args
    ------
        human (str) :  human ID
        folder (str) : folder which contains the stls
        stl (str) : stl filename
        submodel_info (dict) : model_dict structure that stores submodels information
        
    Return
    ------
        submodel_info (dict) : model_dict structure that stores submodels information 
    """

    organ = (stl.split('-')[-1]).split('.')[0]
    if 'heart' in stl:
        submodel_info['name'] = heart_suffix[organ]
        submodel_info['blob'] = os.path.join('v-patients/',human,folder,stl)
    elif 'thorax' in stl:
        submodel_info['name'] = thorax_suffix[organ]
        submodel_info['blob'] = os.path.join('v-patients/',human,folder,stl)
    if 'skin' in stl:
        submodel_info['name'] = 'Skin'
        submodel_info['blob'] = os.path.join('v-patients/',human,folder,stl)
    if 'RA_SVC_IVC' in stl and '_CS' not in stl:
        submodel_info['name'] = 'Right Atrium with SVC and IVC'
        submodel_info['blob'] = os.path.join('v-patients/',human,folder,stl)
    if 'LA_PV' in stl:
        submodel_info['name'] = "Left Atrium and Pulmonary Veins"
        submodel_info['blob'] = os.path.join('v-patients/',human,folder,stl)
    if 'RA_SVC_IVC_CS' in stl:
        submodel_info['name'] = 'Right Atrium with SVC, IVC and Coronary Sinus'
        submodel_info['blob'] = os.path.join('v-patients/',human,folder,stl)
    

    #if 'diaphragm' in stl:
    #    submodel_info['name'] = 'Diaphragm'
    #    submodel_info['blob'] = os.path.join('v-patients/',human,folder,stl)
    
    return submodel_info

def correct_phase_info(file,modeldict,human,series,jsons_dir,ser,df):
    """    
    Function to get heart phase information from database-dl and correct
    both models and patient collection documents. 
    
    Args
    ------
        file (str) :  excel file
        modeldict (dict) : models dict
        human (str) :  human ID
        series (str) : series value
        jsons_dir (str) : default jsons dir
        ser (str) : series name
        
    Return
    ------
        modeldict (dict) : models dict 
    """

    for e,i in enumerate(modeldict['models']):
        if i['timestamp'] == None:
            heart_phase = df[(df['PatientID']== int(human)) & (df['Series']== int(series))].iloc[0]['Phase']
            phase_correction = {'ES':-1,'ED':2}
            if heart_phase != 'None':
                phase = phase_correction[heart_phase]
                modeldict['models'][e]['timestamp'] = phase
                with open(os.path.join(jsons_dir,human,ser,'patient_collection.json') , 'r') as f:
                    patientdict = json.load(f)
                if heart_phase == 'ES':
                    patientdict['es_timestamp'] = phase_correction[heart_phase]
                elif heart_phase == 'ED':
                    patientdict['ed_timestamp'] = phase_correction[heart_phase]
                with open(os.path.join(jsons_dir,human,ser,'patient_collection.json') , 'w') as f:
                    json.dump(patientdict, f)
        else:
            #cardiac phase insertion of non-null models' jsons in patient_collection
            frames = sorted(list(df[(df['PatientID']== int(human)) & (df['Series']== int(series))]['Timestamp']),key=int)
            if any(frame > 100 for frame in frames):
                matching = {}
                for timestamp in frames:
                    #print(round(frames.index(timestamp)/len(frames),2), timestamp)
                    matching[round(frames.index(timestamp)/len(frames),2)] = timestamp
                heart_phase = df[(df['PatientID']== int(human)) & (df['Series']== int(series)) & (df['Timestamp'] == int(matching[i['timestamp']]))].iloc[0]['Phase']
            else:
                heart_phase = df[(df['PatientID']== int(human)) & (df['Series']== int(series)) & (df['Timestamp'] == int(round(i['timestamp']*100)))].iloc[0]['Phase']
            if heart_phase != 'None':
                with open(os.path.join(jsons_dir,human,ser,'patient_collection.json') , 'r') as f:
                    patientdict = json.load(f)
                if heart_phase == 'ES':
                    patientdict['es_timestamp'] = i['timestamp']
                if heart_phase == 'ED':
                    patientdict['ed_timestamp'] = i['timestamp']
                with open(os.path.join(jsons_dir,human,ser,'patient_collection.json') , 'w') as f:
                    json.dump(patientdict, f)
 
    return modeldict

def sharepoint_download(credentials, excel_file):
    sp = lazy_SP365(site_url = credentials['url']
                   , client_id = credentials['client_id']
                   , client_secret = credentials['client_secret'])

    sp.download(sharepoint_location = credentials['location']
                , local_location = excel_file)
    time.sleep(3)

def measurement_type_values(measurement):
    """
    Collects needed information for the measurement_type collection
    """
    type_dict_values = {"name": None, "unit": None, "is_categorical": None, "is_time_dependent": None, "model_required": None}
    if measurement == "LV Volume":
        type_dict_values["name"] = "LV Volume"
        type_dict_values["unit"] = "ml"
        type_dict_values["is_categorical"] = False
        type_dict_values["is_time_dependent"] = True
        type_dict_values["model_required"] = "LV"
    return type_dict_values

def check_and_create_folder(path, delete_if_exists=False):
    """
    Checks if folder exits, if not the folder gets created. 
    For the test functions, there is also the option to delete
    thw specified folder (for proper testing).
    
    """
    if delete_if_exists:
        shutil.rmtree(path=path)
    if not os.path.exists(path):
        os.makedirs(path)

