import os
import filecmp
from main.utils.timestamp_helpers import *



def test_scan_timestamps():
    test1 = ['1203 33% text']
    test2 = ['randomtext 22 %']
    test3 = ['22 %  randomtext']
    test4 = ['22.2% randomtext']
    tests = [test1,test2,test3,test4]
    to_verify = [['33%'],['22 %'], ['22 %'], ['22.2%']]
    for w,z in zip(tests,to_verify):
        assert scan_timestamps(w) == z

def test_detect_convert_timestamp():
    test1 = '33%'
    test2 = '33.3%'
    test3 = '22 %'
    tests = [test1,test2,test3]
    to_verify = ['0.33','0.333','0.22']
    for w,z in zip(tests,to_verify):
        assert round(detect_convert_timestamp(w),3) == float(z)


class dircmp(filecmp.dircmp):
    """
    Compare the content of dir1 and dir2. In contrast with filecmp.dircmp, this
    subclass compares the content of files with the same path.
    """
    def phase3(self):
        """
        Find out differences between common files.
        Ensure we are using content comparison with shallow=False.
        """
        fcomp = filecmp.cmpfiles(self.left, self.right, self.common_files,
                                 shallow=False)
        self.same_files, self.diff_files, self.funny_files = fcomp

    
def is_same(dir1, dir2):
    """
    Compare two directory trees content.
    Return False if they differ, True is they are the same.
    """
    compared = dircmp(dir1, dir2)
    if (compared.left_only or compared.right_only or compared.diff_files 
        or compared.funny_files):
        return False
    for subdir in compared.common_dirs:
        if not is_same(os.path.join(dir1, subdir), os.path.join(dir2, subdir)):
            return False
    return True