def patient_dict(now, URI_p, n_slices):
    """
    Function to initialize the patient dict. It contains all the defined database elements for
    patient, imaging, and patient reid collection.

    Args
    ------
        now (:obj:) :  JSONGen process starting time
        URI_p (str) :  storage URI + human-patient info
        n_slices (int) :  number of dicoms inside patient folder

    Returns
        patientdict (dict) :  patient dict

    """

    patientdict = {
            'datetime_creation': now,
            'versioning': {'version': 1,
                            'base_patient_id': None,
                            'edited_fields': [None, None]},
            'study_date': '',
            'institution_id': '',
            'institution_name': '',
            'internal_info':{'internal_id':'','series':''},
            'age': '',
            'height': None,
            'weight': '',
            'bsa': None,
            'bmi': None,
            'gender': '',
            'body_rois': [{'catalog_tag': None,
                            'extra_tag': None}],
            'es_timestamp': None,
            'ed_timestamp': None,
            'pathology': None,
            'origin_location': None,
            'origin_ethnicity': None,
            'additional_hist': '',
            'imaging_data': None,
            'models': None,
            'imaging':{
                'datetime_creation': now,
                'URI': URI_p,
                'image_files_list': [{
                    'timestamp': None,
                    'image_files': []
                }],
                'n_instances' : n_slices,
                'n_timestamps': '',
                'acquisition_date': '',
                'additional_info': '',
                'body_part_examined': '',
                'modality': '',
                'manufacturer': '',
                'manuf_model': '',
                'bolus_agent': '',
                'slice_thickness': '',
                'pixel_spacing' : '',
                'spacing_btwn_slices': '',
                'image_orientation' : '',
                'image_position_patient' : '',
                'rows': '',
                'columns': ''
        }}

    return patientdict

def human_dict(human):

    human_coll_dict = {'internal_id': int(human),
                        'studies': []}
                        
    human_reid_coll_dict = {'human_id':None,
                            'institution_id':None,
                            'institution_name':None}

    return human_coll_dict, human_reid_coll_dict

