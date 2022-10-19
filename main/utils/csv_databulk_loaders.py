import pandas as pd
import numpy as np
from pathlib import Path
import os


#this file contains the functions used to parse information of the patients of each bulk from CSVs


def theart_csv_parse(human,nominal_phase,patientdict,csvdir):
    """
    Function to parse CSV data from T-Heart patients.

    Args
    ------
        human (str) :  human ID
        nominal_phase (list) :  cardiac phase elements present in nominal phase of the cardiac cycle metadata field
        patientdict (dict) :  patient dict

    Return
    ------
        patientdict (dict) :  patient dict
        
    """
    correspondence = {}
    #making the correspondence between raw theart ID and our internal ID
    for i,j in zip(range(0,66),range(642,708)):
        correspondence[str(j)] = i
    
    theart_df = pd.read_csv(os.path.join(csvdir,'ES_ED-theart.csv'))
    theart_df = theart_df.replace({'-':None})
    theart_df = theart_df.where(pd.notnull(theart_df), None)
    idx = correspondence[str(int(human))]
    
    #neglect human 658 due to data incongruities
    if human != '00658':
        nominal_phase.sort()
        if any(eval(i)>100 for i in nominal_phase):
            patientdict['es_timestamp'] = round(nominal_phase.index(str(round(theart_df['ES'][idx]*100,2)))/len(nominal_phase),2)
            patientdict['ed_timestamp'] = round(nominal_phase.index(str(round(theart_df['ED'][idx]*100,2)))/len(nominal_phase),2)
        else:
            patientdict['es_timestamp'] = theart_df['ES'][idx]
            patientdict['ed_timestamp'] = theart_df['ED'][idx]

    if theart_df['Age'][idx]:
        patientdict['age'] = int(theart_df['Age'][idx])
    if theart_df['Gender'][idx]:
        patientdict['gender'] = theart_df['Gender'][idx]
    if theart_df['Weight'][idx]:            
        patientdict['weight'] = float(theart_df['Weight'][idx])
    if theart_df['Height'][idx]:
        patientdict['height'] = float(theart_df['Height'][idx])

    return patientdict

def toulouse_csv_parse(human,patientdict,path,csvdir):
    """
    Function to parse CSV data from Toulouse databulk.

    Args
    ------
        human (str) :  human ID
        patientdict (dict) :  patient dict
        path (str) :  patient dir absolute path 
    
    Return
    ------
        patientdict (dict) :  patient dict
    """

    df = pd.read_csv(os.path.join(csvdir,'toulouse_info.csv'), delimiter=';')
    df = df.astype(object).replace(np.nan, 'None')
    pat_ser = Path(path).stem

    for i in ['es_timestamp','ed_timestamp']:
        patientdict[i] = df[(df['human']== int(human)) & (df['series']== pat_ser)][i].to_numpy()[0]
        if patientdict[i] == 'None':
            patientdict[i] = None

    patientdict['body_rois'][0]['catalog_tag'] = df[(df['human']== int(human)) & (df['series']== pat_ser)]['body_rois'].to_numpy()[0]

    return patientdict

def canada_china_csv_parse(human,patientdict,path,csvdir):
    """
    Function to parse CSV data from Canada and China databulks.

    Args
    ------
        human (str) :  human ID
        patientdict (dict) :  patient dict
        path (str) :  patient dir absolute path 
    
    Return
    ------
        patientdict (dict) :  patient dict
    """

    df = pd.read_csv(os.path.join(csvdir,'canada_china_info.csv'))
    df = df.astype(object).replace(np.nan, 'None')
    pat_ser = Path(path).stem
    
    # temporary- additional info from human 767 should be added to the csv
    if int(human) != 767:
        for i in ['gender','age','height','weight','origin_location','origin_ethnicity']:
            patientdict[i] = df[(df['human']== int(human)) & (df['series']== pat_ser)][i].to_numpy()[0]
            if patientdict[i] == 'None':
                patientdict[i] = None

        if patientdict['imaging']['body_part_examined'] in ['',' ',None]:
            patientdict['imaging']['body_part_examined'] = df[(df['human']== int(human)) & (df['series']== pat_ser)]['body_part'].to_numpy()[0]
            if patientdict['imaging']['body_part_examined'] == 'None':
                patientdict['imaging']['body_part_examined'] = None

        patientdict['body_rois'][0]['catalog_tag'] = df[(df['human']== int(human)) & (df['series']== pat_ser)]['body_part'].to_numpy()[0]
        if patientdict['body_rois'][0]['catalog_tag'] == 'None':
            patientdict['body_rois'][0]['catalog_tag'] = None

    return patientdict


def additionalinfo_csv_parse(human,patientdict,csvdir):

    df = pd.read_csv(os.path.join(csvdir,'human_additionalinfo.csv'))
    df = df.replace(np.nan, 'None')
    try:
        for i in ['age','gender','height', 'weight','origin_location','pathology','origin_ethnicity']:
            if df[df['human_id']==int(human)].iloc[0][i] != 'None':
                if i == 'pathology':
                    patientdict[i] = eval(df[df['human_id']==int(human)].iloc[0][i])
                else:
                    patientdict[i] = df[df['human_id']==int(human)].iloc[0][i]
    except:
        pass
    return patientdict
