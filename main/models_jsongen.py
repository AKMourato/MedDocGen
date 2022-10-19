import os
import sys
from main.utils.helpers import structure_matching, correct_phase_info, sharepoint_download
import json
import pandas as pd
import numpy as np
import datetime


def generate_modelsjsons(models_jsons_dir, humans, model_dir, jsons_dir, excel_file, credentials, URI):
    """
    Function that generates models' JSONs.

    Args
    ------
        humans (list) :  list of human IDs
        models_jsons_dir (str) :  directory where the JSONs will be stored
    """
    df = sharepoint_download(credentials, excel_file)
    df = pd.read_excel(excel_file)
    df = df.replace(np.nan, 'None')
    now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    for human in sorted(os.listdir(model_dir)):
        if human in humans:
            print(human)
            for folder in os.listdir(os.path.join(model_dir,human)):
                if folder == 'dec_models':
                    #get the existing series from all the stls files, excluding ser_merged
                    existing_series = list(set([int((i.split('-')[1]).replace('ser','')) for i in os.listdir(os.path.join(model_dir,human,folder)) if 'ser_merged' not in i]))
                    #check if a ser_merged exists
                    if any('ser_merged' in stls for stls in os.listdir(os.path.join(model_dir,human,folder))):
                        existing_series.append('ser_merged')
                    for series in sorted(existing_series):
                        modeldict = {'datetime_creation': now,
                                            'URI': URI,
                                            'models': []}
                        #procedure init for non-ser_merged
                        if series != 'ser_merged':
                            ser = 'SER'+f"{int(series):05}"
                            #opening of patient's imaging_collection document and pre-allocation of the detected timestamps from backbone
                            f = open(os.path.join(jsons_dir,human,ser,'imaging_collection.json'))
                            imagingdict = json.load(f)
                            dicom_timestamps = [j['timestamp'] for j in imagingdict['image_files_list']]
                            for i in dicom_timestamps:
                                submodeldict = {'timestamp': i,'sub_models':[],'landmarks':[]}
                                modeldict['models'].append(submodeldict)

                            #this block iterates through the folder stls, extracts the timestamps present, do the interval conversion if needed
                            #and do the organ structure matching between the stls' suffix nomenclature and the standard model_names
                            for stl in sorted(os.listdir(os.path.join(model_dir,human,folder))):
                                submodel_info = {'blob': '', 'name': ''}
                                if 'merged' not in stl and int((stl.split('-')[1]).replace('ser','')) == series:
                                    if 'frame' in stl:
                                        #existing_frames = list(set([(float(int(j.split('-')[2].replace('frame','')))/100) for j in list(filter(lambda f: int((f.split('-')[1]).replace('ser','')) == series, os.listdir(os.path.join(model_dir,human,folder))))])) 
                                        frames = sorted(list(df[(df['PatientID']== int(human)) & (df['Series']== int(series))]['Timestamp']),key=int)
                                        if len(frames) != len(dicom_timestamps):
                                            sys.exit('Mismatch between detected dicom\'s timestamps and database-dl for patient {}-{}.'.format(human,ser))
                                        if any(frame > 100 for frame in frames):
                                            #converted_frame = round(sorted(existing_frames,key=float).index(float(int(stl.split('-')[2].replace('frame','')))/100)/len(existing_frames),2)
                                            converted_frame = round(frames.index(int(stl.split('-')[2].replace('frame','')))/len(frames),2)                                          
                                            submodel_info = structure_matching(human,folder,stl,submodel_info)
                                            for e,i in enumerate(modeldict['models']):
                                                if i['timestamp'] == converted_frame:
                                                    modeldict['models'][e]['sub_models'].append(submodel_info)
                                        else:
                                            converted_frame = float(int(stl.split('-')[2].replace('frame','')))/100
                                            submodel_info = structure_matching(human,folder,stl,submodel_info)
                                            for e,i in enumerate(modeldict['models']):
                                                if i['timestamp'] == converted_frame:
                                                    modeldict['models'][e]['sub_models'].append(submodel_info)
                                    else:
                                        submodel_info = structure_matching(human,folder,stl,submodel_info)
                                        modeldict['models'][0]['sub_models'].append(submodel_info)
                            modeldict = correct_phase_info(excel_file,modeldict,human,series,jsons_dir,ser,df)
                            for i in modeldict['models']:
                                if i['timestamp'] == None:
                                    print('Unexpected behaviour on {}-{} patient.'.format(human,ser))

                            os.makedirs(os.path.join(models_jsons_dir,human,ser), exist_ok=True)               
                            with open(os.path.join(models_jsons_dir,human,ser,'model_collection.json') , 'w') as f:
                                json.dump(modeldict, f)
                        else:
                            #procedure init for ser_merged
                            ser = 'SER_MERGED'
                            #opening of patient's imaging_collection document and pre-allocation of the detected timestamps from backbone
                            f = open(os.path.join(jsons_dir,human,ser,'imaging_collection.json'))
                            imagingdict = json.load(f)
                            dicom_timestamps = [j['timestamp'] for j in imagingdict['image_files_list']]
                            for i in dicom_timestamps:
                                submodeldict = {'timestamp': i,'sub_models':[],'landmarks':[]}
                                modeldict['models'].append(submodeldict)
                            #this block iterates through the folder stls, extracts the timestamps present, do the interval conversion if needed
                            #and do the organ structure matching between the stls' suffix nomenclature and the standard model_names
                            for stl in sorted(os.listdir(os.path.join(model_dir,human,folder))):
                                submodel_info = {'blob': '', 'name': ''}
                                if 'merged' in stl:                      
                                    if 'frame' in stl:
                                        #existing_frames = list(set([(float(int(j.split('-')[2].replace('frame','')))/100) for j in list(filter(lambda f: int((f.split('-')[1]).replace('ser','')) == series, os.listdir(os.path.join(model_dir,human,folder))))])) 
                                        frames = sorted(list(df[(df['PatientID']== int(human)) & (df['Series']== series)]['Timestamp']),key=int)
                                        if len(frames) != len(dicom_timestamps):
                                            sys.exit('Mismatch between detected dicom\'s timestamps and database-dl for patient {}-{}.'.format(human,ser))
                                        if any(frame > 100 for frame in frames):
                                            #converted_frame = round(sorted(existing_frames,key=float).index(float(int(stl.split('-')[2].replace('frame','')))/100)/len(existing_frames),2)
                                            converted_frame = round(frames.index(int(stl.split('-')[2].replace('frame','')))/len(frames),2)                                          
                                            submodel_info = structure_matching(human,folder,stl,submodel_info)
                                            for e,i in enumerate(modeldict['models']):
                                                if i['timestamp'] == converted_frame:
                                                    modeldict['models'][e]['sub_models'].append(submodel_info)
                                        else:
                                            converted_frame = float(int(stl.split('-')[2].replace('frame','')))/100
                                            submodel_info = structure_matching(human,folder,stl,submodel_info)
                                            for e,i in enumerate(modeldict['models']):
                                                if i['timestamp'] == converted_frame:
                                                    modeldict['models'][e]['sub_models'].append(submodel_info)
                                    else:
                                        submodel_info = structure_matching(human,folder,stl,submodel_info)
                                        modeldict['models'][0]['sub_models'].append(submodel_info)
                            modeldict = correct_phase_info(excel_file,modeldict,human,series,jsons_dir,ser)
                            for i in modeldict['models']:
                                if i['timestamp'] == None:
                                    print('Unexpected behaviour on {}-{} patient.'.format(human,ser))

                            os.makedirs(os.path.join(models_jsons_dir,human,ser), exist_ok=True)               
                            with open(os.path.join(models_jsons_dir,human,ser,'model_collection.json') , 'w') as f:
                                json.dump(modeldict, f)

#             _____
#           .'  |  `.
#          /    |    \
#         |-----|-----|
#          \    |    /
#           '.__|__.'
#              \|/
#               |