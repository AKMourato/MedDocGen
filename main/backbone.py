import os
import json
import random
from pydicom import dcmread
import pymongo
from parse import search
from pathlib import Path
import datetime
from dateutil.relativedelta import relativedelta
import sys
import glob
import sys
from main.utils import csv_databulk_loaders, helpers, timestamp_helpers, patient_defaultdict

class JSONGeneration:
    """
    Class containing the building blocks of the JSON generation pipeline.
    
    Attributes
    ------
        now (:obj:) :  JSONGen process starting time
        managed0, theart, canada_china, toulouse, challengedata, realheart (list : :str:) : Human IDs respective to each databulk    

    Methods
    ------
        init
        dataloader
        serialize
        cine_normal_classification
        normal_init
        cine_init
        elements_extraction_and_storing
        elements_correction
        collections_creation
        database_upload

    Returns
    ------

    """
    def __init__(self):
        self.now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        #datadrive databulk bulks
        self.managed0 = [f"{int(i):05}" for i in ([str(i) for i in range(0,642)]+['770','771'])]
        self.theart = [f"{int(i):05}" for i in ([str(i) for i in range(642,708)])]
        self.canada_china = [f"{int(i):05}" for i in ([str(i) for i in range(708,720)]+['767'])]
        self.toulouse = [f"{int(i):05}" for i in ([str(i) for i in range(720,747)])]
        self.challengedata = [f"{int(i):05}" for i in ([str(i) for i in range(747,767)])]
        self.kiba = [f"{int(i):05}" for i in ([str(i) for i in (list(range(772,794))+list(range(859,887)))])]
        self.realheart = [f"{int(i):05}" for i in ([str(i) for i in range(794,837)])]
        self.hannover = [f"{int(i):05}" for i in ([str(i) for i in (list(range(837,859))+list(range(887,894)))])] +['940']
        self.animal = [f"{int(i):05}" for i in ([str(i) for i in range(894,940)])]
        self.fontan = [f"{int(i):05}" for i in ([str(i) for i in range(941,942)])]

    def dataloader(self,**kwargs):
        """
        Function to store the humans IDs that the user wants to create the JSONs for.
        Depending on the user input received in kwargs, the function initialize the ID list to JSONGen iterate further,
        creating as well the directory for the JSONs.

        Kwargs
        ------
            jsondir (str) : JSON destination directory
            databulk (str) : Type of data (bulk)
            URI (str) : URI of the vpatients azure storage
            datadir (str) :  Data directory
            hlist (list) :  Human list for the JSONGen creation
            file (str) :  File path for the JSONGen creation
            models (bool) :  To create models' JSONs

        Raises
        ------
            - exit if databulk is not supported 
            
        Returns
        ------
            humans (list) :  list of human IDs
        """
        self.default_datadir = kwargs.get('default_datadir')
        self.URI = kwargs.get('URI')
        self.jsondir = kwargs.get('jsondir')
        self.csvdir = kwargs.get('csvdir')

        if kwargs.get('databulk') == 'general':
            humans = list(filter(lambda f: f.isnumeric(), [str(f) for f in os.listdir(kwargs.get('datadir'))]))
        elif kwargs.get('databulk') == 'managed0':
            humans = list(filter(lambda f: f in os.listdir(self.default_datadir), self.managed0))
        elif kwargs.get('databulk') == 'theart':
            humans = list(filter(lambda f: f in os.listdir(self.default_datadir), self.theart))
        elif kwargs.get('databulk') == 'canadachn':
            humans = list(filter(lambda f: f in os.listdir(self.default_datadir), self.canada_china))
        elif kwargs.get('databulk') == 'toulouse': 
            humans = list(filter(lambda f: f in os.listdir(self.default_datadir), self.toulouse))
        elif kwargs.get('databulk') == 'challengedata': 
            humans = list(filter(lambda f: f in os.listdir(self.default_datadir), self.challengedata))
        elif kwargs.get('databulk') == 'realheart': 
            humans = list(filter(lambda f: f in os.listdir(self.default_datadir), self.realheart))
        elif kwargs.get('databulk') == 'kiba': 
            humans = list(filter(lambda f: f in os.listdir(self.default_datadir), self.kiba))
        elif kwargs.get('databulk') == 'hannover': 
            humans = list(filter(lambda f: f in os.listdir(self.default_datadir), self.hannover))
        elif kwargs.get('databulk') == 'animal': 
            humans = list(filter(lambda f: f in os.listdir(self.default_datadir), self.animal))
        elif kwargs.get('databulk') == 'fontan': 
            humans = list(filter(lambda f: f in os.listdir(self.default_datadir), self.fontan))

        else:
            sys.exit('Data bulk class not supported.')

        if kwargs.get('file') != None:
            humans = []
            with open(kwargs.get('file')) as fp:
                pat = fp.readlines()
                for line in pat:
                    humans.append(line.rstrip())
            humans.sort()

        if kwargs.get('hlist') != None:
            humans = eval(kwargs.get('hlist'))
            humans = [f"{int(i):05}" for i in humans]

        return humans

    def serialize(self,datadir,humans):
        """
        Function to initialize the serialization of JSONGen. It iterates through the human ID list
        given by the dataloader extracting the elements of each patient folder used for cine-normal classification, 
        calling the subsequent function of the backbone for each patient passage.

        Args
        ------
            datadir (str) :  Data directory
            humans (list) :  list of human IDs

        """

        print('*** Process initialized ***')
        for human in sorted(os.listdir(datadir),key=int):
            if human in humans:
                print(human)
                self.collections_creation(human, human_and_reid=True)
                for pdir in sorted(os.listdir(os.path.join(datadir,human))):
                    if pdir.startswith('STD'):
                        for subdir in sorted(os.listdir(os.path.join(datadir,human,pdir))):
                            if len(glob.glob(os.path.join(datadir,human,pdir,subdir,'*.dcm'))) >= 20:
                                nominal_phase = []
                                image_comments = []
                                series_desc = []
                                #only iterates for patients folder with more than 20 dicoms, although this condition should already be handled in VirtoLoader
                                for image in sorted(os.listdir(os.path.join(datadir,human,pdir,subdir))):
                                    metadata = dcmread(os.path.join(datadir,human,pdir,subdir,image), force=True)
                                    try:
                                        elem = metadata['NominalPercentageOfCardiacPhase'].value
                                        if str(elem) not in nominal_phase:
                                            nominal_phase.append(str(elem))
                                    except KeyError:
                                        pass
                                    try:
                                        elem2 = metadata['ImageComments'].value
                                        if elem2 not in image_comments:
                                            image_comments.append(elem2)
                                    except KeyError:
                                        pass
                                    try:
                                        elem3 = metadata['SeriesDescription'].value
                                        if elem3 not in series_desc:
                                            series_desc.append(elem3)
                                    except KeyError:
                                        pass

                                self.cine_normal_classification(datadir, human, pdir, subdir, nominal_phase, image_comments, series_desc)

    def cine_normal_classification(self,datadir,human,pdir,subdir,nominal_phase,image_comments,series_desc):
        """
        Function to classify each patient of cine or normal ct, calling the respective subsequent function accordingly.
        Essentially, if more than one phase value is detected in one of the elements, hierarchically analysed, a patient is classified as cite ct. Otherwise, as normal ct.

        Args
        ------
            datadir (str) :  Data directory
            human (str) :  human ID
            pdir (str) :  patient parent directory
            subdir (str) :  patient directory (i.e. series folder name)
            nominal_phase (list) :  nominal phase elements present in the patient metadata
            image_comments (list) :  image comments elements present in the patient metadata
            series_desc (list) :  series description elements present in the patient metadata

        """
        path = os.path.join(datadir,human,pdir,subdir)
        if len(nominal_phase) > 1:
            for i,p in enumerate(nominal_phase):
                if nominal_phase[i] == '':
                    del nominal_phase[i]
            #condition to neglect anomalies in phase variation. Theoretically, no more than 14 (detected) timestamps should exist. 
            if len(nominal_phase) > 1 and len(nominal_phase) < 15:
                self.cine_init(human,subdir,path,nominal_phase=set(nominal_phase))
            else:
                #condition to neglect anomalies in phase variation. If more than 14 timestamps are detected, the patient will be classified as normal ct and the cardiac phase info ignored.
                if len(nominal_phase) >= 15:
                    nominal_phase = []
                self.normal_init(human,subdir,path, phase=(nominal_phase))

        elif nominal_phase != [] and len(nominal_phase) <= 1:
            self.normal_init(human,subdir,path, phase=nominal_phase)

        elif image_comments != []:
            phase = timestamp_helpers.scan_timestamps(image_comments)
            if not phase:
                phase = ['']
            if len(set(phase))>1:
                #condition to neglect anomalies in phase variation. If more than 14 timestamps are detected, the patient will be classified as normal ct and the cardiac phase info ignored.
                if len(set(phase)) >= 15:
                    phase = timestamp_helpers.scan_timestamps(series_desc)
                    if not phase:
                        phase = ['']
                    if len(set(phase))>1:
                        #condition to neglect anomalies in phase variation. If more than 14 timestamps are detected, the patient will be classified as normal ct and the cardiac phase info ignored.
                        if len(set(phase)) >= 15:
                            phase = []
                            self.normal_init(human,subdir,path, phase=phase)
                        self.cine_init(human,subdir,path,phase_s=set(phase))
                    else:
                        self.normal_init(human,subdir,path,phase=set(phase))
                else:
                    self.cine_init(human,subdir,path,phase_c=set(phase))
            else:
                if phase == ['']:
                    phase = timestamp_helpers.scan_timestamps(series_desc)
                    if not phase:
                        phase = ['']
                    if len(set(phase))>1:
                        #condition to neglect anomalies in phase variation. If more than 14 timestamps are detected, the patient will be classified as normal ct and the cardiac phase info ignored.
                        if len(set(phase)) >= 15:
                            phase = []
                            self.normal_init(human,subdir,path, phase=phase)
                        else:
                            self.cine_init(human,subdir,path,phase_s=set(phase))
                        
                    else:
                        self.normal_init(human,subdir,path, phase=set(phase))
                else:
                    self.normal_init(human,subdir,path, phase=set(phase))
        
        else:
            phase = timestamp_helpers.scan_timestamps(series_desc)
            if not phase:
                phase = ['']
            if len(set(phase))>1:
                #condition to neglect anomalies in phase variation. If more than 14 timestamps are detected, the patient will be classified as normal ct and the cardiac phase info ignored.
                if len(set(phase)) >= 15:
                    phase = []
                    self.normal_init(human,subdir,path, phase=phase)
                self.cine_init(human,subdir,path,phase_s=set(phase))
            else:
                self.normal_init(human,subdir,path,phase=set(phase))


    def normal_init(self,human,subdir,path,phase=0):
        """
        Function to initialize the procedure for normal ct patients, calling the subsequent functions of the backbone.

        Args
        ------
            human (str) :  human ID
            subdir (str) :  patient directory (i.e. series folder name)
            path (str) :  patient dir absolute path
            phase (list) : detected cardiac phase 

        """
        n_slices = len(os.listdir(path))
        #storage URI + human-patient info
        URI_p = self.URI + 'v-patients/' + human 
        patientdict = patient_defaultdict.patient_dict(self.now, URI_p, n_slices)

        #allocate the timestamp (if exists) in patientdict, removing '%' and converting to [0,1]
        if phase not in (0, {''}):
            for i in phase:
                if '%' in i:
                    i = i.replace("%","")
                    phase = float(i)/100
                else:
                    i = i.replace("[","")
                    i = i.replace("]","")
                    phase = float(i)/100
            patientdict['imaging']['image_files_list'][0]['timestamp'] = phase
        
        for image in sorted(os.listdir(path)):
            if image.endswith("dcm"):
                #adding the images filenames to the timestamp
                patientdict['imaging']['image_files_list'][0]['image_files'].append(image)
                metadata = dcmread(os.path.join(path,image),force=True)
                patientdict = self.elements_extraction_and_storing(metadata, patientdict)
        

        patientdict = self.elements_correction(human,patientdict,path)
        self.collections_creation(human,patientdict=patientdict,subdir=subdir)

    def cine_init(self,human,subdir,path,nominal_phase=0,phase_c=0, phase_s=0):
        """
        Function to initialize the procedure for cine ct patients, calling the subsequent functions of the backbone.

        Args
        ------
            human (str) :  human ID
            subdir (str) :  patient directory (i.e. series folder name)
            path (str) :  patient dir absolute path
            nominal_phase (list) :  cardiac phase elements present in nominal phase of the cardiac cycle metadata field
            phase_c (list) :  cardiac phase detected elements present in the image comments metadata field
            phase_s (list) :  cardiac phase detected elements present in the series description metadata field

        """
        URI_p = self.URI + 'v-patients/' + human
        n_slices = len(os.listdir(path))
        patientdict = patient_defaultdict.patient_dict(self.now, URI_p, n_slices)

        #since the size of the image_files_list depends on the number of timestamps, the lenght of this element is settled according to each patient
        #this procedure is only applied to one of the following three branches depending on where the cardiac phase info is.
        #thus, the timestamps are first allocated in the patientdict, and when the final loop through the patient dicoms starts (to info extraction and consequently storing in patientdict), 
        #the images are appended to the corresponding cardiac phase element
        
        #----------------------------------------------------------------#
        if nominal_phase != 0:
            nominal_phase = sorted(list(nominal_phase),key=float)
            timestamp_helpers.preallocate_timestamp_info(patientdict, nominal_phase, nominal=True)
        #----------------------------------------------------------------#
        if phase_c != 0:
            phase_c = list(phase_c)
            timestamp_helpers.preallocate_timestamp_info(patientdict,phase_c)
        #----------------------------------------------------------------#
        if phase_s != 0:
            phase_s = list(phase_s)
            timestamp_helpers.preallocate_timestamp_info(patientdict,phase_s)
        #----------------------------------------------------------------#
        #start of the "final loop" mentioned above
        for image in os.listdir(path):
            if image.endswith("dcm"):
                metadata = dcmread(os.path.join(path,image),force=True)
                #add the images filename to the respective cardiac phase element
                #----------------------------------------------------------------#
                if nominal_phase != 0:
                    for i,j in enumerate(patientdict['imaging']['image_files_list']):
                        if any(eval(x)>100 for x in nominal_phase):
                            if round(nominal_phase.index(str((metadata['NominalPercentageOfCardiacPhase'].value)))/len(nominal_phase),2) == patientdict['imaging']['image_files_list'][i]['timestamp']:
                                patientdict['imaging']['image_files_list'][i]['image_files'].append(image)
                                patientdict['imaging']['image_files_list'][i]['image_files'].sort()
                        else:
                            if float(metadata['NominalPercentageOfCardiacPhase'].value)/100 == patientdict['imaging']['image_files_list'][i]['timestamp']:
                                patientdict['imaging']['image_files_list'][i]['image_files'].append(image)
                                patientdict['imaging']['image_files_list'][i]['image_files'].sort()
                #----------------------------------------------------------------#
                if phase_c != 0:
                    field = str(metadata['ImageComments'].value)
                    timestamp = timestamp_helpers.detect_convert_timestamp(field)
                    for i,j in enumerate(patientdict['imaging']['image_files_list']):
                        if timestamp == patientdict['imaging']['image_files_list'][i]['timestamp']:
                            patientdict['imaging']['image_files_list'][i]['image_files'].append(image)
                            patientdict['imaging']['image_files_list'][i]['image_files'].sort()
                #----------------------------------------------------------------#
                if phase_s != 0:
                    field = str(metadata['SeriesDescription'].value)
                    timestamp = timestamp_helpers.detect_convert_timestamp(field)
                    for i,j in enumerate(patientdict['imaging']['image_files_list']):
                        if timestamp == patientdict['imaging']['image_files_list'][i]['timestamp']:
                            patientdict['imaging']['image_files_list'][i]['image_files'].append(image)
                            patientdict['imaging']['image_files_list'][i]['image_files'].sort()
                #----------------------------------------------------------------#

                patientdict = self.elements_extraction_and_storing(metadata, patientdict)

        patientdict = self.elements_correction(human,patientdict,path,nominal_phase=nominal_phase)
        self.collections_creation(human,patientdict=patientdict,subdir=subdir)

    def elements_extraction_and_storing(self, metadata, patientdict):
        """
        Function to extract the desired fields from the patients metadata, and store into patientdict.

        Args
        ------
            metadata (dict) :  patient metadata
            patientdict (dict) :  patient dict 

        Return
        ------
            patientdict (dict) :  patient dict
        """

        #the value size conditions in the several following fields extraction are just to ensure that the maximum information present in each field, amongst all dicoms in a patient, are stored.  
        #---------------------------------------------------------------------#
        try:
            age_elem = str(metadata['PatientAge'].value)
            if len(age_elem) > len(patientdict['age']):
                patientdict['age'] = age_elem
        except KeyError:
            pass
        # the age should also be determinable via birthday and acquisition date. 
        try:
            # if age is already filled in, skip this part
            if patientdict['age'] == '':
                birthday = str(metadata['PatientBirthDate'].value)
                if birthday != '19000101':
                    acquisition_date = str(metadata['AcquisitionDate'].value)
                    # bring the date to correct format
                    birthday = datetime.datetime.strptime(birthday, '%Y%m%d')
                    acquisition_date = datetime.datetime.strptime(acquisition_date, '%Y%m%d')
                    diff = relativedelta(acquisition_date, birthday)
                    # one more check, if age is in a conceivable range
                    if diff.years > 5 and diff.years < 110:
                        patientdict['age'] = str(diff.years)
        except:
            pass
        #---------------------------------------------------------------------#
        try:
            weight_elem = str(metadata['PatientWeight'].value)
            if len(weight_elem) > len(patientdict['weight']):
                patientdict['weight'] = weight_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            add_datahist_elem = str(metadata['AdditionalPatientHistory'].value)
            if len(add_datahist_elem) > len(patientdict['additional_hist']):
                patientdict['additional_hist'] = add_datahist_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            gender_elem = str(metadata['PatientSex'].value)
            if len(gender_elem) > len(patientdict['gender']):
                patientdict['gender'] = gender_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            studydate_elem = str(metadata['StudyDate'].value)
            if len(studydate_elem) > len(patientdict['study_date']):
                patientdict['study_date'] = studydate_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            acquisitiondate_elem = str(metadata['AcquisitionDate'].value)
            if len(acquisitiondate_elem) > len(patientdict['imaging']['acquisition_date']):
                patientdict['imaging']['acquisition_date'] = acquisitiondate_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            bolus_agent_elem = str(metadata['ContrastBolusAgent'].value)
            if len(str(bolus_agent_elem)) > len(patientdict['imaging']['bolus_agent']):
                patientdict['imaging']['bolus_agent'] = bolus_agent_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            slicethicknss_elem = str(metadata['SliceThickness'].value)
            if len(slicethicknss_elem) > len(patientdict['imaging']['slice_thickness']):
                patientdict['imaging']['slice_thickness'] = slicethicknss_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            spacingbtwnslices_elem = str(metadata['SpacingBetweenSlices'].value)
            if len(spacingbtwnslices_elem) > len(patientdict['imaging']['spacing_btwn_slices']):
                patientdict['imaging']['spacing_btwn_slices'] = spacingbtwnslices_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            imageorientation_elem = str(metadata['ImageOrientationPatient'].value)
            if len(imageorientation_elem) > len(patientdict['imaging']['image_orientation']):
                patientdict['imaging']['image_orientation'] = imageorientation_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            imgposition_pat = str(metadata['ImagePositionPatient'].value)
            if len(imgposition_pat) > len(patientdict['imaging']['image_position_patient']):
                patientdict['imaging']['image_position_patient'] = imgposition_pat
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            body_part_examined_elem = str(metadata['BodyPartExamined'].value)
            if len(body_part_examined_elem) > len(patientdict['imaging']['body_part_examined']):
                patientdict['imaging']['body_part_examined'] = body_part_examined_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            rows_elem = str(metadata['Rows'].value)
            if len(rows_elem) > len(patientdict['imaging']['rows']):
                patientdict['imaging']['rows'] = rows_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            columns_elem = str(metadata['Columns'].value)
            if len(columns_elem) > len(patientdict['imaging']['columns']):
                patientdict['imaging']['columns'] = columns_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            pixel_spacing_elem = str(metadata['PixelSpacing'].value)
            if len(pixel_spacing_elem) > len(patientdict['imaging']['pixel_spacing']):
                patientdict['imaging']['pixel_spacing'] = pixel_spacing_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            institution_id_elem = str(metadata['PatientName'].value)
            if len(institution_id_elem) > len(patientdict['institution_id']):
                patientdict['institution_id'] = institution_id_elem
        except KeyError:
            pass
        if patientdict['institution_id'] == '':
            try:
                institution_id_elem = str(metadata['PatientID'].value)
                if len(institution_id_elem) > len(patientdict['institution_id']):
                    patientdict['institution_id'] = institution_id_elem
            except KeyError:
                pass
        #---------------------------------------------------------------------#
        try:
            institution_name_elem = str(metadata['InstitutionName'].value)
            if len(institution_name_elem) > len(patientdict['institution_name']):
                patientdict['institution_name'] = institution_name_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            manufacturer_elem = str(metadata['Manufacturer'].value)
            if len(manufacturer_elem) > len(patientdict['imaging']['manufacturer']):
                patientdict['imaging']['manufacturer'] = manufacturer_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            manuf_model_elem = str(metadata['ManufacturerModelName'].value)
            if len(manuf_model_elem) > len(patientdict['imaging']['manuf_model']):
                patientdict['imaging']['manuf_model'] = manufacturer_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            modality_elem = str(metadata['Modality'].value)
            if len(modality_elem) > len(patientdict['imaging']['modality']):
                patientdict['imaging']['modality'] = modality_elem
        except KeyError:
            pass
        #---------------------------------------------------------------------#
        try:
            add_info_elem = str(metadata['ImageComments'].value)
            if len(add_info_elem) > len(patientdict['imaging']['additional_info']):
                patientdict['imaging']['additional_info'] = add_info_elem
        except KeyError:
            pass

        return patientdict


    def elements_correction(self, human, patientdict, path, nominal_phase=None):
        """
        Function to correct the extracted fields from the patients metadata, according to our needs.
        Also, the patient information present in CSVs and PDFs are inserted here.

        Args
        ------
            human (str) :  human ID
            path (str) :  patient dir absolute path
            patientdict (dict) :  patient dict 
            nominal_phase (list, optional) :  cardiac phase elements present in nominal phase of the cardiac cycle metadata field

        Return
        ------
            patientdict (dict) :  patient dict
        """

        gender_exclude = ['','Anonymous','0','O']
        weight_exclude = ['','Anonymous','None','0','0.0']
        slice_thck_exclude = ['','None']   
        #---------------------------------------------------------------------#
        if patientdict['age'].strip() in ['','001D']:
            patientdict['age'] = None

        if patientdict['age'] is not None:
            try:
                patientdict['age'] = int(patientdict['age'].replace('Y',''))
            except ValueError as e:
                print(e)
                pass
        #---------------------------------------------------------------------#
        if patientdict['height'] is None:
            #to extract height info from "additional_info" field
            height = search('{:d}cm', patientdict['imaging']['additional_info'])
            try:
                patientdict['height'] = float(height[0])
            except TypeError:
                patientdict['height'] = None
        #---------------------------------------------------------------------#        
        if patientdict['weight'].strip() in weight_exclude:
            patientdict['weight'] = None
        
        if patientdict['weight'] is None:
            #to extract weight info from "additional_info" field
            weight = search('{:d}kg', patientdict['imaging']['additional_info'])
            try:
                patientdict['weight'] = float(weight[0])
            except TypeError:
                patientdict['weight'] = None
        else:
            patientdict['weight'] = float(patientdict['weight'])
        #---------------------------------------------------------------------#
        
        if patientdict['gender'].strip() == 'W':
            patientdict['gender'] = 'female'

        if patientdict['gender'].strip() == 'M':
            patientdict['gender'] = 'male'
        
        if patientdict['gender'].strip() == 'F':
            patientdict['gender'] = 'female'
        
        if patientdict['gender'].strip() in gender_exclude:
            patientdict['gender'] = None
        #---------------------------------------------------------------------#
        if patientdict['imaging']['rows'] != '':
            try:
                patientdict['imaging']['rows'] = int(patientdict['imaging']['rows'])
            except KeyError:
                pass   
        if patientdict['imaging']['columns'] != '':
            try:
                patientdict['imaging']['columns'] = int(patientdict['imaging']['columns'])
            except KeyError:
                pass
        #---------------------------------------------------------------------#
        if patientdict['imaging']['slice_thickness'] in slice_thck_exclude:
            patientdict['imaging']['slice_thickness'] = None
        if patientdict['imaging']['slice_thickness'] != None:
            try:
                patientdict['imaging']['slice_thickness'] = float(patientdict['imaging']['slice_thickness'])
            except KeyError:
                pass
        #---------------------------------------------------------------------#
        if patientdict['imaging']['spacing_btwn_slices'] != '':
            try:
                patientdict['imaging']['spacing_btwn_slices'] = float(patientdict['imaging']['spacing_btwn_slices'])
            except KeyError:
                pass
        #---------------------------------------------------------------------#
        if patientdict['imaging']['image_files_list'][0]['timestamp'] == '':
            patientdict['imaging']['image_files_list'][0]['timestamp'] = None
        #---------------------------------------------------------------------#
        if patientdict['imaging']['pixel_spacing'] == '':
            patientdict['imaging']['pixel_spacing'] = None

        if patientdict['imaging']['pixel_spacing'] is not None:
            patientdict['imaging']['pixel_spacing'] = eval(patientdict['imaging']['pixel_spacing'])
        #---------------------------------------------------------------------#
        if patientdict['imaging']['image_orientation'] == '':
            patientdict['imaging']['image_orientation'] = None
            
        if patientdict['imaging']['image_orientation'] is not None:
            patientdict['imaging']['image_orientation'] = eval(patientdict['imaging']['image_orientation'])
        #---------------------------------------------------------------------#
        if patientdict['imaging']['image_position_patient'] == '':
            patientdict['imaging']['image_position_patient'] = None
                                                            
        if patientdict['imaging']['image_position_patient'] is not None:
            patientdict['imaging']['image_position_patient'] = eval(patientdict['imaging']['image_position_patient'])
        #---------------------------------------------------------------------#
        if patientdict['imaging']['n_timestamps'] == '':
            patientdict['imaging']['n_timestamps'] = 1
        #---------------------------------------------------------------------#
        if patientdict['imaging']['bolus_agent'] == '':
            patientdict['imaging']['bolus_agent'] = None
        #---------------------------------------------------------------------#
        if patientdict['imaging']['body_part_examined'] == '':
            patientdict['imaging']['body_part_examined'] = None
        else:
            #body_rois standardization
            heart_and_thorax = ['HEART','CHEST','KORPERSTAMM', 'chest','AORTA','CT Aorta ganz KM','Aorta','CT ANGIO','TORAX','ANGIO','CT ANGIO TOTALE AORTA + IV CONTR','CORONARIO','SAPIEN','TX']
            abdominal = ['ABDOMEN']
            head_to_pelvis = ['J BRZUSZNA','TX AB PE','CORE VALVE','SPECIAL','aorta tho/abd','CTA Thorax/Ab...']
            head = ['HEAD']
            
            if patientdict['imaging']['body_part_examined'].strip() in heart_and_thorax:
                patientdict['body_rois'][0]['catalog_tag'] = 'heart_and_thorax'
            elif patientdict['imaging']['body_part_examined'].strip() in abdominal:
                patientdict['body_rois'][0]['catalog_tag'] = 'abdominal'
            elif patientdict['imaging']['body_part_examined'].strip() in head:
                patientdict['body_rois'][0]['catalog_tag'] = 'head_and_neck'
            elif patientdict['imaging']['body_part_examined'].strip() in head_to_pelvis:
                patientdict['body_rois'][0]['catalog_tag'] = 'head_to_pelvis'
        #---------------------------------------------------------------------#
        #replace the spacing between slices by the difference between consecutive slices locations whenever
        #spacing between slice element is not filled
        if patientdict['imaging']['spacing_btwn_slices'] == '':
            images = sorted(os.listdir(path))
            consecutive_images_pairs = list(zip(images, images[1:]))
            random_pair = random.choice(consecutive_images_pairs)
            slice_loc1 = 0
            slice_loc2 = 0
            ds1 = dcmread(os.path.join(path,random_pair[0]),force=True)
            try:
                slice_loc1 = float(ds1['SliceLocation'].value)
            except KeyError:
                pass

            ds2 = dcmread(os.path.join(path,random_pair[1]),force=True)
            try:
                slice_loc2 = float(ds2['SliceLocation'].value)
            except KeyError:
                pass
            
            spacingbtwnslices_elem = round(abs(slice_loc1-slice_loc2),1)
            patientdict['imaging']['spacing_btwn_slices'] = spacingbtwnslices_elem
        #---------------------------------------------------------------------# 
        #CSV loader
        patientdict = csv_databulk_loaders.additionalinfo_csv_parse(human,patientdict,self.csvdir)

        if human in self.theart:
            patientdict = csv_databulk_loaders.theart_csv_parse(human,nominal_phase,patientdict,self.csvdir)
        
        if human in self.toulouse:
            patientdict = csv_databulk_loaders.toulouse_csv_parse(human,patientdict,path,self.csvdir)

        if human in self.canada_china:
            patientdict = csv_databulk_loaders.canada_china_csv_parse(human,patientdict,path,self.csvdir)
        #---------------------------------------------------------------------#
        #bsa and bmi calculation
        patientdict['bsa'] = helpers.calculate_mosteller_bsa(patientdict)
        patientdict['bmi'] = helpers.calculate_bmi(patientdict)
        #---------------------------------------------------------------------#
        # additional info insertion
        patientdict['internal_info']['internal_id'] = int(human)
        patientdict['internal_info']['series'] = Path(path).stem
        #---------------------------------------------------------------------# 
        
        return patientdict

    def collections_creation(self,human,patientdict=None,subdir=None,human_and_reid=False):
        """
        Function to create each collection from the patient and model dicts.

        Args
        ------
            human (str) :  human ID
            path (str) :  patient dir absolute path
            patientdict (dict) :  patient dict

        """
        if human_and_reid:
            human_coll_dict, human_reid_coll_dict = patient_defaultdict.human_dict(human)
            
            with open(os.path.join(self.jsondir,human,'human_collection.json') , 'w') as f:
                json.dump(human_coll_dict, f)
            
            with open(os.path.join(self.jsondir,human,'human_reid_collection.json') , 'w') as f:
                json.dump(human_reid_coll_dict, f)
        else:
            patient_collection_dict = {}
            imaging_collection_dict = {}
            reidentification = ['institution_id', 'institution_name']

            for i,j in patientdict['imaging'].items():
                imaging_collection_dict[i] = j

            for i,j in patientdict.items():
                if i != 'imaging' and i not in reidentification:
                    patient_collection_dict[i] = j

            del patient_collection_dict['study_date']
            #create patient and imaging collection jsons
            with open(os.path.join(self.jsondir,human,subdir,'patient_collection.json') , 'w') as f:
                json.dump(patient_collection_dict, f)

            with open(os.path.join(self.jsondir,human,subdir,'imaging_collection.json') , 'w') as f:
                json.dump(imaging_collection_dict, f)

            #fill in human and human_reid collections jsons
            with open(os.path.join(self.jsondir,human,'human_collection.json') , 'r') as f:
                human_coll_dict = json.load(f)
            
            if human_coll_dict['studies'] == []:
                human_coll_dict['studies'].append({'study_date': patientdict['study_date'],
                                            'patients_ids': [subdir]})
            
            else:
                studydates = []
                for i in human_coll_dict["studies"]:
                    studydates.append(i["study_date"])
                if patientdict['study_date'] not in studydates:
                    human_coll_dict['studies'].append({'study_date': patientdict['study_date'],
                                            'patients_ids': [subdir]})
                else:
                    for e,_ in enumerate(human_coll_dict['studies']):
                        if human_coll_dict['studies'][e]['study_date'] == patientdict['study_date']:
                            human_coll_dict['studies'][e]['patients_ids'].append(subdir)
            
            with open(os.path.join(self.jsondir,human,'human_collection.json') , 'w') as f:
                json.dump(human_coll_dict, f)
            
            with open(os.path.join(self.jsondir,human,'human_reid_collection.json') , 'r+') as f:
                human_reid_coll_dict = json.load(f)
            for i in reidentification:
                if human_reid_coll_dict[i] == None:
                    human_reid_coll_dict[i] = patientdict[i]
                else:
                    if human_reid_coll_dict[i] == patientdict[i]:
                        pass
                    else:
                        if len(human_reid_coll_dict[i].rstrip()) > 1:
                            print(i,'don\'t match. Verify it.')
                        else:
                            human_reid_coll_dict[i] == patientdict[i]

            with open(os.path.join(self.jsondir,human,'human_reid_collection.json') , 'w') as f:
                json.dump(human_reid_coll_dict, f)
   
#             _____
#           .'  |  `.
#          /    |    \
#         |-----|-----|
#          \    |    /
#           '.__|__.'
#              \|/
#               |