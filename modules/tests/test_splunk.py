import os
import sys

lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(lib_path)

import splunk


class TestSplunk():
    def test_download(self):
        splunk.download('6.3.1')
        splunk.download('sustain_ember')
        splunk.download('')



