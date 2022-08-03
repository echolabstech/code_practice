from typing import Optional, List

class TreeNode:
	def __init__(self, val=0, left=None, right=None):
		self.val = val
		self.left = left
		self.right = right

class Solution:
	def preorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
		def traverse(node: Optional[TreeNode], values: List[int]) -> None:
			if node:
				values.append(node.val)
				if node.left:
					traverse(node.left, values)
				if node.right:
					traverse(node.right, values)
		values = []
		traverse(root, values)
		return values

	def inorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
		def traverse(node: Optional[TreeNode], values: List[int]) -> None:
			if node:
				if node.left:
					traverse(node.left, values)
				values.append(node.val)
				if node.right:
					traverse(node.right, values)
		values = []
		traverse(root, values)
		return values

	def postorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
		def traverse(node: Optional[TreeNode], values: List[int]) -> None:
			if node:
				if node.left:
					traverse(node.left, values)
				if node.right:
					traverse(node.right, values)
				values.append(node.val)
		values = []
		traverse(root, values)
		return values

	def levelorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
		def walk(values: List[int], queue: List[TreeNode]) -> None:
			nodes = queue.pop(0)
			level_values = []
			level_queue = []
			for node in nodes:
				if node.left:
					level_values.append(node.left.val)
					level_queue.append(node.left)
				if node.right:
					level_values.append(node.right.val)
					level_queue.append(node.right)
			if len(level_values) > 0:
				values.append(level_values)
			if len(level_queue) > 0:
				queue.append(level_queue);
			if len(queue) > 0:
				walk(values, queue) 
		values = []
		queue = []
		if root:
			values.append([root.val])
			queue.append([root])
			walk(values, queue)
		return values