#include "Python.h"
#include <iostream>
#include <deque>
#include <set>

static PyObject* cleaves_leaves(PyObject* self, PyObject* args) {
    PyObject* deriv;
    // PyObject* pred;
    if (!PyArg_ParseTuple(args, "O", &deriv)) {
        PyErr_SetString(PyExc_RuntimeError, "leaves: error parsing arguments");
    }
    
    PyObject* result = PyList_New((Py_ssize_t)0);
    
    PyObject* is_leaf_boolean = PyObject_CallMethod(deriv, "is_leaf", NULL);
    bool is_leaf = PyBool_Check(is_leaf_boolean) && is_leaf_boolean == Py_True;
    Py_XDECREF(is_leaf_boolean);
    if (is_leaf) {
        PyList_Append(result, deriv);
        Py_XDECREF(deriv);
    } else {
        PyObject* kids = PySequence_Fast(deriv, "deriv not iterable");
        
        Py_ssize_t nitems = PySequence_Fast_GET_SIZE(kids);
        PyObject** kidp = PySequence_Fast_ITEMS(kids);
        while (nitems-- > 0) {
            PyObject* args = Py_BuildValue("(O)", *kidp);
            PyObject* sub_leaves = cleaves_leaves(NULL, args); 
            Py_XDECREF(args);
            
            PySequence_InPlaceConcat(result, sub_leaves);      
            Py_XDECREF(sub_leaves);
            
            ++kidp;
        }
    }
    
    return result;
}

static PyObject* cleaves_nonrecursive_leaves(PyObject* self, PyObject* args) {
    PyObject* deriv;
    // PyObject* pred;
    if (!PyArg_ParseTuple(args, "O", &deriv)) {
        PyErr_SetString(PyExc_RuntimeError, "nonrecursive_leaves: error parsing arguments");
    }
    
    std::set<PyObject*> visited;
    PyObject* cur = deriv;
    Py_XINCREF(cur);
    PyObject* result = PyList_New((Py_ssize_t)0);

    bool found;
    while (true) {
        if (cur == Py_None) break;
        
        found = false;
        PyObject* is_leaf_boolean = PyObject_CallMethod(cur, "is_leaf", NULL);
        bool is_leaf = PyBool_Check(is_leaf_boolean) && is_leaf_boolean == Py_True;
        Py_XDECREF(is_leaf_boolean);
        if (!is_leaf) {
            PyObject *iterator = PyObject_GetIter(cur);
            if (iterator != NULL) { // iterator is NULL when cur is leaf
                PyObject *kid;
                while (kid = PyIter_Next(iterator)) {
                    if (kid != Py_None) {
                        if (visited.find(kid) == visited.end()) {
                            cur = kid;
                        
                            found = true;
                            break;
                        }
                    }
                    Py_XDECREF(kid);
                }
                Py_XDECREF(iterator);
            }
        }
            
        if (!found) {
            if (visited.find(cur) == visited.end()) {
                // if not cur.is_leaf() and ...
                // std::cout << "=cur " << cur << std::endl;
                PyObject* is_leaf_boolean = PyObject_CallMethod(cur, "is_leaf", NULL);
                bool is_leaf = PyBool_Check(is_leaf_boolean) && is_leaf_boolean == Py_True;
                Py_XDECREF(is_leaf_boolean);
                if (is_leaf) {
                    PyList_Append(result, cur);
                    Py_XDECREF(cur);
                }
            
                visited.insert(cur);
            } else {
                cur = PyObject_GetAttrString(cur, "parent");
            }
        }
        
        found: ;
    }
    
    return result;
}

static PyMethodDef cleaves_methods[] = {
    /* name    ptr to function               flags         doc */
    { "leaves", (PyCFunction)cleaves_leaves, METH_VARARGS, "" },
    { "nonrecursive_leaves", (PyCFunction)cleaves_nonrecursive_leaves, METH_VARARGS, "" },
    { NULL, NULL, 0, NULL }
};

extern "C" void initcleaves(void) {    
    Py_InitModule("cleaves", cleaves_methods);
}