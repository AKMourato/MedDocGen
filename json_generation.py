import os
import sys
import argparse
import yaml
from main.backbone import JSONGeneration
from main.utils import helpers
from main.models_jsongen import generate_modelsjsons 


def jsongen_parser():
    """
    Argparser function for the JSON generation process.
    
    Args
    ----------
        jsondir (str) : JSON destination directory
        databulk (str) : Type of data (bulk)
        datadir (str, optional) :  Data directory
        hlist (list, optional) :  Human list
        file (str, optional) :  File path
        models (bool, optional) :  Create models JSONs
    
    Return
    -------
        parser (:obj: Namespace)
    
    """

    parser = argparse.ArgumentParser(prog='json_generation',
                                            usage='%(prog)s [options]',
                                            description='Generate patient JSON files')

    parser.add_argument('jsondir', metavar = 'JSON destination directory', 
                                help='the path to the directory where the JSONs will be created')

    parser.add_argument('databulk',  metavar='Type of data', choices=['general','managed0','theart','toulouse','canadachn','challengedata','realheart','kiba','hannover','animal','fontan'], 
                                help= 'Data bulk or general type')

    parser.add_argument('--datadir', metavar = 'Data directory', default='/home/dev/datadrive/', 
                                help='the absolute path to the patients DICOM directory')
    
    parser.add_argument('--csvdir', metavar = 'CSV root directory', default='/home/database/csvs/', 
                                help='the absolute path to the patients CSV directory')

    parser.add_argument('--basejsondir', metavar = 'Base JSON directory', default='/home/dev/jsons', 
                                help='the absolute path to the JSON directory that the model json generation will look into.')

    parser.add_argument('--hlist', metavar='Human list', default=None,
                                help='list containing the humans to be generated')

    parser.add_argument('--file', metavar='File path', default=None,
                                help='path to the .txt file where the humans are defined')

    parser.add_argument('--only_models', default=False,
                                metavar='Create models\' JSONs', help='Create models\' JSONs')

    return parser


def backbone_caller(args):
    """
    Function to call the backbone of JSONGen package.
    
    Args:
        args (:obj: Namespace)               
    
    Print:
        - When the dataloader process is completed
        - When JSONGen process (before an eventual db upload) is finished
    Raises:
        - exit if data directory given do not exist.
        - exit if file and human list are defined in parallel.
        - exit if file path given is not a file.
        - exit if hlist is not a list
        - if boolean values are not given for models and dbupload
    """

    if not os.path.exists(args.datadir):
        sys.exit('Data directory given do not exist.')

    if (args.file and args.hlist) != None:
        sys.exit('File and human list cannot be initialized in parallel.')

    if args.file != None:
        if not os.path.isfile(args.file):
            sys.exit('Path given is not a file.')

    if args.hlist != None:
        try:
            if not isinstance(eval(args.hlist),list):
                sys.exit('Human list must be a list of integers')
        except:
            sys.exit('Human list must be a list of integers')
        
        #needs further items check (e.g. only int(int) items)

    def str2bool(arg):
        if isinstance(arg, bool):
            return arg
        if arg.lower() in ('yes', 'true', '1'):
            return True
        elif arg.lower() in ('no', 'false', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')

    args.only_models = str2bool(args.only_models)

    with open("./config.yaml", "r") as yml:
        cfg = yaml.full_load(yml)

    if args.only_models == False:
        jsongen = JSONGeneration()
        humans = jsongen.dataloader(datadir=args.datadir,
                                    csvdir=args.csvdir,
                                    jsondir=args.jsondir,
                                    databulk=args.databulk,
                                    default_datadir=cfg['default-server-paths']['datadir'],
                                    file=args.file,
                                    hlist=args.hlist,
                                    URI = cfg['azure-storage']['URI'])
        helpers.create_jsondirs(args.datadir, args.jsondir, humans)
        jsongen.serialize(args.datadir,humans)
        print('JSONs created.')
    else:
        jsongen = JSONGeneration()
        humans = jsongen.dataloader(datadir=args.datadir,
                            databulk=args.databulk,
                            file=args.file,
                            hlist=args.hlist)
        generate_modelsjsons(args.jsondir,humans,cfg['default-server-paths']['modelsdir'],
                            args.basejsondir,cfg['default-server-paths']['database-dl'],cfg['sharepoint-download-credentials'],cfg['azure-storage']['URI'])
        print('Models\' JSONs created.')

if __name__ == "__main__":
    args = jsongen_parser().parse_args()
    print("Command Line Interface Args:", args)
    backbone_caller(args)

#             _____
#           .'  |  `.
#          /    |    \
#         |-----|-----|
#          \    |    /
#           '.__|__.'
#              \|/
#               |