from munge.ccg.nodes import Node

# Mix-in providing the below tree transformation.
#           o               o
#          / \             / \
#        /\   o    ===>   o   /\
#       <__> / \         / \ <__>
#           ,  /\       /\  ,
#             <__>     <__>
# This transformation allows an entire left subtree to be quoted together with the absorbed comma found
# in direct quoted speech:
#   ``Foals in winter coats _,_ '' she said.

def is_non_conjunction_comma_leaf(leaf):
   # look for a conj feature in the parent's category
   return leaf.lex == "," and not leaf.parent.cat.has_feature("conj")

# Excludes commas which are part of this structure yielded by a type change:
#              (S\NP)\(S\NP)
#                   / \
#                  ,   NP
# The comma inside this apposition structure cannot be shifted because we need to preserve
# the rule.
def is_non_raised_comma_leaf(leaf):
   return leaf.lex == "," and str(leaf.parent.cat) != r'(S\NP)\(S\NP)'

def is_period_leaf(leaf):
   return leaf.lex == "." and leaf.cat == "."

def is_prequote_punctuation(leaf):
   return (is_non_raised_comma_leaf(leaf) and is_non_conjunction_comma_leaf(leaf)) or is_period_leaf(leaf)

def is_leftmost_leaf_of_right_subtree(leaf):
   # Without the following check, the following returns true:
   #       o
   #      / \
   #     /\  o
   #    /__\
   # The punctuation transformation doesn't make sense in this case, because
   # applying the shift would yield an unchanged structure.
   if (not leaf.parent) or leaf.parent.rch == leaf:
       return False

   cur = leaf
   while cur.parent.lch == cur: cur = cur.parent 

   return cur.parent and cur.parent.rch == cur

def move_punctuation_leaf_to_left_subtree(node):
   #              \
   #               o
   #              / \
   #             o   o
   #            / \
   #  punct -> ,   o <- shrunk
   punct_leaf  = node.clone()
   shrunk_leaf = node.parent.rch

   # Shrink operation: excise the comma leaf from the right subtree
   #              \
   #   node.p.p -> o__
   #          CUT! |   \    or the symmetric case
   #             o |    o
   #         CUT!  | <- new edge
   #   node -> ,   o 
   if node.parent.parent.lch == node.parent:
       node.parent.parent.lch = shrunk_leaf
   elif node.parent.parent.rch == node.parent:
       node.parent.parent.rch = shrunk_leaf

   node = shrunk_leaf
   while node.parent.lch == node:
       node = node.parent
   # Now, _node_ is the right child of its parent, so ascend once more
   node = node.parent 

   # Insert punctuation structure at this node
   kid = node.lch
   new_kid = Node(kid.cat, 0, 2, None, kid, punct_leaf)
   node.lch = new_kid

   return new_kid.rch # Return the newly inserted punctuation leaf (right child of inserted node)
   
class ShiftComma(object):
    @staticmethod
    def process_punct(node):
        if is_prequote_punctuation(node) and is_leftmost_leaf_of_right_subtree(node):
            return move_punctuation_leaf_to_left_subtree(node)
        return node
