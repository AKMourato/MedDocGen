import re

def scan_timestamps(field):
    """
    Function to detect phase elements from a list of strings.
    
    Args
    ------
        field: list of strings.

    Returns
    ------
        phase (list, :str:) :  phase elements detected in each string.
    """
    phase = []
    for i in field:
        phase_scan = re.search(r'(\d+(\.\d+)?%)', i)
        if phase_scan is None:
            phase_scan = re.search(r'(\d+(\ )?%)', i)
            if phase_scan is None:
                pass
            else:
                phase.append(phase_scan[0])
        else:
            phase.append(phase_scan[0])
    return phase

def detect_convert_timestamp(field):
    """
    Function to detect phase elements from a string, and convert it to [0,1].
    
    Args:
        field (str): string to scan

    Returns:
        timestamp (float) : cardiac phase value.
    """
    timestamp = re.search(r'(\d+(\.\d+)?%)', field)
    if timestamp is None:
        timestamp = re.search(r'(\d+(\ )?%)', field)
    timestamp = timestamp[0].replace("%","")
    timestamp = float(timestamp)/100
    return timestamp


def preallocate_timestamp_info(patientdict, timestamps, nominal=False):
    """
    Function to preallocate the cardiac phase value into the predefined patientdict entry.
    If the cardiac phase comes from nominal_phase, it converts to [0,1] and removes '%' first.  

    Args
    ------
        patientdict (dict) :  patient dict 
        timestamp (list, :str:) :  cardiac phase values
        nominal (bool, optional) :  if the cardiac phase values comes from nominal_phase
        theart (bool, optional) :  if the patient is from T-Heart databulk

    """ 
    if nominal:
        nominal_phase = timestamps
        phase = []
        if any(eval(i)>100 for i in nominal_phase):
            for i in nominal_phase:
                i = round(nominal_phase.index(i)/len(nominal_phase),2)
                phase.append(i)
        else:
            for i in nominal_phase:
                i = float(i)/100
                phase.append(i)
        phase.sort()
    else:
        phase = [] 
        for i in timestamps:
            i = i.replace('%',"")
            i = float(i)/100
            phase.append(i)
        phase.sort()

    while len(patientdict['imaging']['image_files_list']) < len(phase):
        patientdict['imaging']['image_files_list'].append({
            'timestamp': "",
            'image_files': []})
    for i,j in enumerate(phase):
        patientdict['imaging']['image_files_list'][i]['timestamp'] = j

    patientdict['imaging']['n_timestamps'] = len(patientdict['imaging']['image_files_list'])
