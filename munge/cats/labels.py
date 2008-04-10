def label_result(cur, prev, app, flipped):
    '''This labels the slashes of the results of combinatory rule applications in a way that 
    preserves the indices attached to the slashes of its arguments.
    For example, (X\1)/0Y Y/0Z -> (X\1)/0Z.
    _flipped_ is true when prev was the right child of its parent.'''

    if app == "fwd_appl":
        if (not flipped) and prev.left.label # _X/Y_ Y -> X
            cur.labelled(prev.left.label)
    elif app == "bwd_appl":
        if flipped and prev.left.label # Y _X\Y_ -> X
            cur.labelled(prev.left.label)
    elif app in ("fwd_comp", "fwd_xcomp"):
        if flipped: # X/Y _Y/Z_ -> X/Z 
            if prev.right.label: cur.right.labelled(prev.right.label)
        else: # _X/Y_ Y/Z -> X/Z
            if prev.left.label: cur.left.labelled(prev.left.label)
    elif app in ("bwd_comp", "bwd_xcomp"):
        if flipped: # Y\Z _X\Y_ -> X\Z
            if prev.left.label: cur.left.labelled(prev.left.label)
        else: # _Y\Z_ X\Y -> X\Z
            if prev.right.label: cur.right.labelled(prev.right.label)
    elif app in ("fwd_raise", "bwd_raise"): # X -> T|(T|X)
        if prev.label: cur.right.right.labelled(prev.label)
    elif app in ("fwd_subst", "fwd_xsubst"):
        if flipped: # (X/Y)/Z _Y/Z_ -> X/Z
            if prev.right.label: cur.right.labelled(prev.right.label)
        else: # _(X/Y)/Z_ Y/Z -> X/Z
            if prev.left.left.label: cur.left.labelled(prev.left.left.label)
            if prev.right.label: cur.right.labelled(prev.right.label)
    elif app in ("bwd_subst", "bwd_xsubst"):
        if flipped: # Y/Z _(X\Y)/Z_ -> X/Z
            if prev.left.left.label: cur.left.labelled(prev.left.left.label)
            if prev.right.label: cur.right.labelled(prev.right.label)
        else: # _Y/Z_ (X\Y)/Z -> X/Z
            if prev.right.label: cur.right.labelled(prev.right.label)

