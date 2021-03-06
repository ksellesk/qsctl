import os
import platform
import unittest
import subprocess

from qingstor.qsctl.utils import (
    yaml_load,
    load_conf,
    uni_print,
    is_windows,
    format_size,
    to_unix_path,
    pattern_match,
    encode_to_gbk,
    encode_to_utf8,
    join_local_path,
    is_pattern_match,
    get_part_numbers,
    validate_bucket_name,
    FileChunk,
)

from qingstor.qsctl.constants import PART_SIZE

config_sample = '''
qy_access_key_id: 'QINGCLOUDACCESSKEYID'
qy_secret_access_key: 'QINGCLOUDSECRETACCESSKEYEXAMPLE'
zone: 'ZONEID'
'''

bad_config_sample = '''
bad_sample: 'this is an invalid config'
'''

class TestUtils(unittest.TestCase):

    def setUp(self):
        # Write conf_file and bad_conf_file
        current_path = os.path.split(os.path.realpath(__file__))[0]

        conf_file = os.path.join(current_path, "data/config/conf_file")
        bad_conf_file = os.path.join(current_path, "data/config/bad_conf_file")

        if not os.path.exists(conf_file):
            with open(conf_file, 'w') as f:
                f.write(config_sample)

        if not os.path.exists(bad_conf_file):
            with open(bad_conf_file, 'w') as f:
                f.write(bad_config_sample)

        self.conf_file= conf_file
        self.bad_conf_file= bad_conf_file

        # Create a large file(~64MB)
        self.large_file = os.path.join(current_path, "data/large_file")
        command = ("dd if=/dev/urandom of=%s bs=%s count=2 > /dev/null 2>&1" %
                   (self.large_file, PART_SIZE))
        subprocess.check_call(command, shell=True)

        with open(self.large_file, 'w') as f:
            f.seek(2 * PART_SIZE)
            f.write("just for testing")

    def test_yaml_load(self):
        with open(self.conf_file, 'r') as f:
            self.assertIsInstance(yaml_load(f), dict)

    def test_load_conf_1(self):
        load_conf("")

    def test_load_conf_2(self):
        load_conf(self.bad_conf_file)

    def test_load_conf_3(self):
        self.assertIsInstance(load_conf(self.conf_file), dict)

    def test_is_windows(self):
        if platform.system().lower() == "windows":
            self.assertTrue(is_windows())
        else:
            self.assertFalse(is_windows())

    def test_to_unix_path(self):
        win_path = "foo\\bar"
        self.assertEqual(to_unix_path(win_path), "foo/bar")

    def test_join_local_path(self):
        if is_windows():
            path1, path2 = "foo\\", "bar/test.txt"
            self.assertEqual(join_local_path(path1, path2), "foo\\bar\\test.txt")
        else:
            path1, path2 = "foo/", "bar/test.txt"
            self.assertEqual(join_local_path(path1, path2), "foo/bar/test.txt")

    def test_encode_to_utf8(self):
        s = b'\xd6\xd0\xce\xc4' # GBK encoded
        self.assertEqual(encode_to_utf8(s), b'\xe4\xb8\xad\xe6\x96\x87')

    def test_encode_to_gbk(self):
        s = b'\xe4\xb8\xad\xe6\x96\x87' # utf8 encoded
        self.assertEqual(encode_to_gbk(s), b'\xd6\xd0\xce\xc4')

    def test_uni_print(self):
        notice = b"utf8\xe5\xb7\xb2\xe6\x94\xaf\xe6\x8c\x81"
        uni_print(notice)

    def test_format_size(self):
        size = os.path.getsize(self.large_file)
        self.assertEqual(format_size(size), "64.0 MiB")

    def test_pattern_match(self):
        self.assertTrue(pattern_match("xyz", "x?z"))
        self.assertTrue(pattern_match("xyz", "*"))
        self.assertFalse(pattern_match("xyz", "xy"))
        self.assertFalse(pattern_match("xyz", "*?x"))

    def test_is_pattern_match(self):
        self.assertTrue(is_pattern_match("xyz", None, None))
        self.assertFalse(is_pattern_match("xyz", "*", None))
        self.assertTrue(is_pattern_match("xyz", "*", "x?z"))
        self.assertTrue(is_pattern_match("xyz", "*", "*z"))

    def test_get_part_numbers(self):
        part_numbers = get_part_numbers(self.large_file)
        self.assertEqual(part_numbers, [0, 1, 2])

    def test_File_Chunk(self):
        part0 = FileChunk(self.large_file, 0)
        part1 = FileChunk(self.large_file, 1)
        part2 = FileChunk(self.large_file, 2)
        self.assertEqual(part0.__len__(), PART_SIZE)
        self.assertEqual(part1.__len__(), PART_SIZE)
        self.assertEqual(part2.__len__(), len(b"just for testing"))
        self.assertEqual(part2.read(5), b"just ")
        self.assertEqual(part2.read(), b"for testing")
        part0.close()
        part1.close()
        part2.close()

    def test_validate_bucket_name(self):
        self.assertFalse(validate_bucket_name("-abcd"))
        self.assertFalse(validate_bucket_name("abcd-"))
        self.assertFalse(validate_bucket_name("ab.cd"))
        self.assertFalse(validate_bucket_name("Abcd"))
        self.assertFalse(validate_bucket_name("Abcd"))
        self.assertFalse(validate_bucket_name("Ab!cd"))
        self.assertFalse(validate_bucket_name("Ab%cd"))
        self.assertFalse(validate_bucket_name("Ab$cd"))
        self.assertFalse(validate_bucket_name("a"*64))
        self.assertTrue(validate_bucket_name("0ab-cd"))
        self.assertTrue(validate_bucket_name("0ab-cd1"))

    def tearDown(self):
        if os.path.exists(self.large_file):
            os.remove(self.large_file)

if __name__ == "__main__":
    unittest.main(verbosity=2)
