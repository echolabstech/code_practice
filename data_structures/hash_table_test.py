import unittest
import time
from memory_profiler import profile
from hash_table import HashTable

class TestHashTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.st = int(round(time.time() * 1000))

    @classmethod
    def tearDownClass(cls):
        et = int(round(time.time() * 1000))
        print('runtime is {} ms'.format(et - cls.st))

    @profile
    def setUp(self):
        self.hash_table = HashTable(50)

    def tearDown(self):
        self.hash_table = None

    def test_idempotent_hash_function(self):
        key = 'gfg@example.com'
        hashed_key = self.hash_table.hashed_key(key)
        for _ in range(50):
            self.assertEqual(self.hash_table.hashed_key(key), hashed_key)

    @unittest.skip('WIP')
    def test_set_some_value(self):
        key = 'gfg@example.com'
        value = 'some value'
        self.hash_table.set_val(key, value)
        print(self.hash_table)
        # expected = "[][][][][][][][][][][][][][][][][][][][][][][][][('gfg@example.com', 'some value')][][][][][][][][][][][][][][][][][][][][][][][][][]"
        # self.assertTrue(str(self.hash_table).__contains__('[]'))

if __name__ == '__main__':
    unittest.main()
