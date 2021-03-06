import os
import shutil
import unittest

from qingstor.qsctl.commands.cp import CpCommand
from qingstor.qsctl.utils import load_conf

from mock import MockOptions

class TestCpCommand(unittest.TestCase):
    Cp = CpCommand

    def setUp(self):
        # Set the http connection
        conf = load_conf("~/.qingcloud/config.yaml")
        options = MockOptions()
        self.Cp.conn = self.Cp.get_connection(conf, options)

        # We need some buckets and keys for testing.
        valid_bucket = "validbucket"
        resp = self.Cp.conn.make_request("PUT", valid_bucket)
        resp = self.Cp.conn.make_request("HEAD", valid_bucket)
        if resp.status != 200:
            self.fail("setUp failed: please use another bucket name")
        resp.close()

        # Temp directory for testing
        if not os.path.exists("tmp/"):
            os.mkdir("tmp/")

        self.valid_bucket = valid_bucket

    def test_upload_files(self):
        # Create some local files for testing.
        for i in range(1, 10):
            with open("tmp/file" + str(i), 'w') as f:
                f.write("just for testing")
        options = MockOptions(
            source_path="tmp/",
            dest_path="qs://validbucket",
            exclude="*",
            include="*",
            force=True
        )
        print(options.exclude)
        self.Cp.upload_files(options)

    def test_upload_file(self):
        # Create a large file(~8MB)
        with open("tmp/large_file", 'w') as f:
            f.seek(8*1024*1024)
            f.write("just for testing")
        options = MockOptions(
            source_path="tmp/large_file",
            dest_path="qs://validbucket",
            exclude=None,
            include=None,
            force=True
        )
        self.Cp.upload_file(options)

    def test_download_files(self):
        for i in range(0, 10):
            key = "test" + str(i)
            resp = self.Cp.conn.make_request("PUT", self.valid_bucket, key)
        resp.close()
        options = MockOptions(
            source_path="qs://validbucket",
            dest_path="tmp/",
            exclude=None,
            include=None,
            force=True
            )
        self.Cp.download_files(options)

    def test_download_file(self):
        resp = self.Cp.conn.make_request("PUT", self.valid_bucket, "test_file")
        resp.close()
        options = MockOptions(
            source_path="qs://validbucket/test_file",
            dest_path="tmp/",
            exclude=None,
            include=None,
            force=True
        )
        self.Cp.download_file(options)
        self.assertTrue((os.path.exists("tmp/test_file")))

    def tearDown(self):
        options = MockOptions(exclude=None, include=None)
        self.Cp.remove_multiple_keys(self.valid_bucket, options=options)
        resp = self.Cp.conn.make_request("DELETE", self.valid_bucket)
        resp.close()
        shutil.rmtree("tmp/")

if __name__ == "__main__":
    unittest.main(verbosity=2)
