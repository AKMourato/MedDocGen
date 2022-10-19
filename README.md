## JSONGen v1.0.1

Brief description: (ToBe completed)


The main script **json_generation.py** works as a user input parser followed by the backbone calling accordingly to user needs.

Required positional arguments:
1) JSON directory
2) Dataclass (i.e. general,managed0,toulouse,etc..)

Optional arguments:
- Data directory (default: */home/database/datadrive*)
- Human list
- File
- Only models (T/F) (default: False)


### Usage
*requires (env) activated*

For general usage and info type

```
python json_generation.py -h
```

&nbsp;

*To test the complete package, define a test directory for jsons and delete the folder after you finish if possible.*

&nbsp;

To a quick overview, let's see some use cases:

- Generate JSONs for all data (accordingly to the exceptions in each databulk) in datadrive into /test-jsons dir
```
python json_generation.py ./test-jsons general
```

*Currently, for testing, the database defined is database_v0_prototype in the development database account. So you can upload and delete documents there freely.*


&nbsp;

- Generate JSONs for specific humans, regardless dataclass. (e.g: human 122 (managed0), human 669 (theart), human 733 (toulouse))
```
python json_generation.py ./test-jsons general --hlist [122,669,733]
```
Note that the JSONs will be created accordingly with the databulk that these humans belong (since some processes differ relative to that, e.g. CSV parsing), so we don't need to worry about specifying anything additionally.

&nbsp;

In the case that you have data outside datadrive (thus not verified data), you can still create regardless its databulk. The **only** and **required** assumption the scripts have, is that the data should be in the following structure:

```
/nevermind/datadir/example
    ├── 00222
    │   └── STD00001
    │       ├── SER000001
    │       │   └── image1.dcm
    |       |   └── (......)
    │       ├── SER000002
    │       └── SER000003
    └── 00223
```
so if you want to generate the jsons for all the patients in that directory, you'll just:
```
python json_generation.py ./test-jsons general --datadir /nevermind/datadir/example
```

### Generate Models' JSONs

- To generate the jsons for the models, the procedure is similar. Setting --only_models to True, the package will generate the models' jsons without iterating through the dicom data, therefore not creating patient and imaging collection. The dataloader is the same for both processes, so the above examples for specifying databulks or specific humans works in the same way. Similarly, jsondir and dataclass must be specified.

So for example, if you want to create the models' jsons just for existing realheart patients:

```
python json_generation.py /home/database/test-jsons realheart --only_models True
```

One aspect should be noted though. The models' json generation requires the imaging collection document of each patient model since it needs to extract the heart cycle phase information detected from the dicoms. Currently, the default directory to look for this documents is set to /home/database/jsons, therefore they must exist there. To change it, check models_jsongen.py.

### Generate Measurements' JSONs

- To create measurement JSONs you have to run the script json_generation_measurements.py. The arguments are similar to the main script. In particular, however, the measurement must also be specified. Type and Categories are optional, they could be already in database. But this will be checked again during upload. 

### Merge acquisitions

- To merge acquisitions into one (combination of series) according to what was defined:

```
python utils/merge_acquisitions.py 222 -s SER00003 SER00006
```

So a new series with the merging between series 3 and 6 will be created in the current default directory (/home/dev/jsons).

If you want to have different base directory and destination directory:

```
python utils/merge_acquisitions.py 222 -s SER00003 SER00006 -b /home/dev/test-jsons -d /home/dev/end-test-jsons
```

In this case the jsons that lie in *dev/test-jsons/222* will be used to create a new series in *dev/end-test-jsons/222*.

### Test

To run the test battery, patients data should be downloaded first from the azure datastorage.
For that, go to *virtonomyplatformdev* storage account and download all the existing blobs inside *jsongen-test-data*.
The 'csvs' and 'models' folder should be inserted in the package root folder, and 'test_data' inside 'tests' folder and each patient folder unzipped.

The final structure should look like this:
```
/JSONGeneration/
    ├── main
    ├── csvs
    ├── (...)
    ├── tests/test_data/  
        ├── 00122
        │   └── STD00001
        │       ├── SER0000011
        │       │   └── <image1>.dcm
        |       |   └── (......)
        └── 00169
        │   └── STD00001
        │       ├── SER00003
        │       │   └── <image1>.dcm
        |       |   └── (......)
```

After completion, run ```pytest``` in the root folder.
