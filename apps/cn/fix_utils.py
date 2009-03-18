def replace_kid(node, old, new):
    # make sure you go through Node#__setitem__, not by modifying Node.kids directly,
    # otherwise parent pointers won't get updated 
    node[node.kids.index(old)] = new