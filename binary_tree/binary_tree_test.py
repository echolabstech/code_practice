import unittest
from binary_tree import Solution, TreeNode
import time
from memory_profiler import profile

class TestPreorderTraversal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.st = int(round(time.time() * 1000))

    @classmethod
    def tearDownClass(cls):
        et = int(round(time.time() * 1000))
        print('runtime is {} ms'.format(et - cls.st))

    @profile
    def setUp(self):
        self.solution = Solution()

    def tearDown(self):
        self.solution = None

    def test_missing_root(self):
        root = None
        tree = self.solution.preorderTraversal(root)
        self.assertEqual(tree, [])

    def test_missing_left_missing_right(self):
        three = TreeNode(val=3, left=None, right=None)
        two = TreeNode(val=2, left=three, right=None)
        root = TreeNode(val=1, left=None, right=two)
        tree = self.solution.preorderTraversal(root)
        self.assertEqual(tree, [1,2,3])

    def test_one_left_one_right(self):
        one = TreeNode(val=1, left=None, right=None)
        two = TreeNode(val=2, left=None, right=None)
        root = TreeNode(val=3, left=one, right=two)
        tree = self.solution.preorderTraversal(root)
        self.assertEqual(tree, [3,1,2])

    def test_left_left_right(self):
        three = TreeNode(val=3, left=None, right=None)
        one = TreeNode(val=1, left=None, right=None)
        two = TreeNode(val=2, left=one, right=three)
        root = TreeNode(val=4, left=two, right=None)
        tree = self.solution.preorderTraversal(root)
        self.assertEqual(tree, [4,2,1,3])

class TestInorderTraversal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.st = int(round(time.time() * 1000))

    @classmethod
    def tearDownClass(cls):
        et = int(round(time.time() * 1000))
        print('runtime is {} ms'.format(et - cls.st))

    @profile
    def setUp(self):
        self.solution = Solution()

    def tearDown(self):
        self.solution = None

    def test_missing_root(self):
        root = None
        tree = self.solution.inorderTraversal(root)
        self.assertEqual(tree, [])

    def test_missing_left_missing_right(self):
        three = TreeNode(val=3, left=None, right=None)
        two = TreeNode(val=2, left=three, right=None)
        root = TreeNode(val=1, left=None, right=two)
        tree = self.solution.inorderTraversal(root)
        self.assertEqual(tree, [1,3,2])

    def test_one_left_one_right(self):
        one = TreeNode(val=1, left=None, right=None)
        two = TreeNode(val=2, left=None, right=None)
        root = TreeNode(val=3, left=one, right=two)
        tree = self.solution.inorderTraversal(root)
        self.assertEqual(tree, [1,3,2])

    def test_left_left_right(self):
        three = TreeNode(val=3, left=None, right=None)
        one = TreeNode(val=1, left=None, right=None)
        two = TreeNode(val=2, left=one, right=three)
        root = TreeNode(val=4, left=two, right=None)
        tree = self.solution.inorderTraversal(root)
        self.assertEqual(tree, [1,2,3,4])

class TestPostOrderTraversal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.st = int(round(time.time() * 1000))

    @classmethod
    def tearDownClass(cls):
        et = int(round(time.time() * 1000))
        print('runtime is {} ms'.format(et - cls.st))

    @profile
    def setUp(self):
        self.solution = Solution()

    def tearDown(self):
        self.solution = None

    def test_missing_root(self):
        root = None
        tree = self.solution.postorderTraversal(root)
        self.assertEqual(tree, [])

    def test_missing_left_missing_right(self):
        three = TreeNode(val=3, left=None, right=None)
        two = TreeNode(val=2, left=three, right=None)
        root = TreeNode(val=1, left=None, right=two)
        tree = self.solution.postorderTraversal(root)
        self.assertEqual(tree, [3,2,1])

    def test_one_left_one_right(self):
        one = TreeNode(val=1, left=None, right=None)
        two = TreeNode(val=2, left=None, right=None)
        root = TreeNode(val=3, left=one, right=two)
        tree = self.solution.postorderTraversal(root)
        self.assertEqual(tree, [1,2,3])

    def test_left_left_right(self):
        three = TreeNode(val=3, left=None, right=None)
        one = TreeNode(val=1, left=None, right=None)
        two = TreeNode(val=2, left=one, right=three)
        root = TreeNode(val=4, left=two, right=None)
        tree = self.solution.postorderTraversal(root)
        self.assertEqual(tree, [1,3,2,4])

class TestLevelOrderTraversal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.st = int(round(time.time() * 1000))

    @classmethod
    def tearDownClass(cls):
        et = int(round(time.time() * 1000))
        print('runtime is {} ms'.format(et - cls.st))

    @profile
    def setUp(self):
        self.solution = Solution()

    def tearDown(self):
        self.solution = None

    def test_missing_root(self):
        root = None
        tree = self.solution.levelorderTraversal(root)
        self.assertEqual(tree, [])

    def test_only_root(self):
        root = TreeNode(val=1, left=None, right=None)
        tree = self.solution.levelorderTraversal(root)
        self.assertEqual(tree, [[1]])

    def test_short_traversal(self):
        seven = TreeNode(val=7, left=None, right=None)
        fifteen = TreeNode(val=15, left=None, right=None)
        twenty = TreeNode(val=20, left=fifteen, right=seven)
        nine = TreeNode(val=9, left=None, right=None)
        root = TreeNode(val=3, left=nine, right=twenty)
        tree = self.solution.levelorderTraversal(root)
        self.assertEqual(tree, [[3],[9,20],[15,7]])

    def test_long_traversal(self):
        five = TreeNode(val=5, left=None, right=None)
        eight = TreeNode(val=8, left=None, right=None)
        one = TreeNode(val=1, left=eight, right=five)
        nine = TreeNode(val=9, left=None, right=None)
        two = TreeNode(val=2, left=nine, right=None)
        six = TreeNode(val=6, left=None, right=None)
        seven = TreeNode(val=7, left=six, right=one)
        four = TreeNode(val=4, left=None, right=two)
        root = TreeNode(val=3, left=seven, right=four)
        tree = self.solution.levelorderTraversal(root)
        self.assertEqual(tree, [[3],[7,4],[6,1,2],[8,5,9]])

if __name__ == '__main__':
    unittest.main()
