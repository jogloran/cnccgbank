#include "Python.h"
#include <iostream>
#include <deque>
#include <set>
#include <string>
#include <stdio.h>

static PyObject* _parse_docs(PyObject* self, PyObject* args);
static PyObject* _parse_doc(std::deque<std::string>& toks);
static std::deque<std::string> augparse_split(PyObject* self, PyObject* args);
static void shift_and_check(std::string must_match, std::deque<std::string>& toks);
static PyObject* augparse_augpenn_parse(PyObject* self, PyObject* args);
static PyObject* _parse(std::deque<std::string>& toks, PyObject* parent=NULL);

static PyObject* parse_category_f = NULL;
static PyObject* Leaf_f = NULL;
static PyObject* Node_f = NULL;

static void shift_and_check(std::string must_match, std::deque<std::string>& toks) {
    std::string next = toks.front(); toks.pop_front();
    if (next != must_match) {
        std::string msg = "Expected " + must_match + ", got " + toks.front();
        PyErr_SetString(PyExc_RuntimeError, msg.c_str());
    }
}

static PyObject* augparse_augpenn_parse(PyObject* self, PyObject* args) {
    return _parse_docs(self, args);
}

static PyObject* _parse_docs(PyObject* self, PyObject* args) {
    std::deque<std::string> toks = augparse_split(self, args);
    
    PyObject* result = PyList_New((Py_ssize_t)0);
    while (toks.size() > 0 && toks.front() == "(") {
        PyObject* doc = _parse_doc(toks);
        PyList_Append( result, doc );
        Py_XDECREF(doc);
    }
    return result;
}

static PyObject* _parse_doc(std::deque<std::string>& toks) {
    shift_and_check("(", toks);
    PyObject* result = _parse(toks);
    shift_and_check(")", toks);
    return result;
}

static PyObject* _parse(std::deque<std::string>& toks, PyObject* parent) {
    if (parent == NULL) {
        parent = Py_None; Py_XINCREF(Py_None);
    }
    
    shift_and_check("(", toks);
    // tag = toks.next()
    std::string tag = toks.front(); toks.pop_front();
    //     head_index = None
    //     if toks.peek() == '<':
    int head_index = -1;
    if (toks.front() == "<") {
        //         toks.next()
        toks.pop_front();
        //         head_index = int(toks.next())
        head_index = atoi(toks.front().c_str()); toks.pop_front();
        //         shift_and_check( '>', toks )
        shift_and_check(">", toks);
    }
        
    //     category = None
    PyObject* category = NULL;
    
//     if toks.peek() == '{':        
    if (toks.front() == "{") {
//         toks.next()
        toks.pop_front();
//         category = parse_category(toks.next())
        PyObject* cat = PyString_FromString(toks.front().c_str()); toks.pop_front();
        PyObject* args = Py_BuildValue("(O)", cat);
        category = PyObject_CallObject(parse_category_f, args);
//         shift_and_check( '}', toks )
        shift_and_check("}", toks);
    }
    
    if (category == NULL) {
        category = Py_None; Py_XINCREF(Py_None);
    }

//     kids = []
    PyObject* kids = PyList_New((Py_ssize_t)0);
// 
//     lex = None
    std::string lex;
//     while toks.peek() != ')':
    while (toks.front() != ")") {
//         if toks.peek() == '(':
        if (toks.front() == "(") {
//             kids.append( self.read_deriv(toks) )
            PyObject* node = _parse(toks);
            PyList_Append( kids, node );
            Py_XDECREF(node);
//         else:
        } else {
//             lex = toks.next()
            lex = toks.front(); toks.pop_front();
        }
    }
    
//     if (not kids) and lex:
    if (PyList_Size(kids) == 0 && lex.length() != 0) {
//         return A.Leaf(tag, lex, category, parent)
        PyObject* args = Py_BuildValue("(ssOO)", tag.c_str(), lex.c_str(), category, parent);
        PyObject* result = PyObject_CallObject(Leaf_f, args);
        Py_XDECREF(args);
                    
        shift_and_check(")", toks);
        
        Py_XDECREF(kids);
        Py_XDECREF(category);
        return result;
//     else:
    } else {
//         ret = A.Node(tag, kids, category, parent, head_index)
        PyObject* args = Py_BuildValue("(sOOOi)", tag.c_str(), kids, category, parent, head_index);
        PyObject* result = PyObject_CallObject(Node_f, args);
        if (result == NULL) {
            Py_RETURN_NONE;
        }
        Py_XDECREF(args);
        
//         for kid in ret: kid.parent = ret
        PyObject* kids = PySequence_Fast(result, "result not iterable");
        Py_ssize_t nitems = PySequence_Fast_GET_SIZE(kids);
        PyObject** kidp = PySequence_Fast_ITEMS(kids);
        while (nitems-- > 0) {
            PyObject_SetAttrString(*kidp, "parent", result);
            ++kidp;
        }

        // TODO:
        shift_and_check(")", toks);
        
        Py_XDECREF(kids);
        Py_XDECREF(category);
        return result;
    }
    
    Py_RETURN_NONE;
}

static std::deque<std::string> augparse_split(PyObject* self, PyObject* args) {
    const char* str;
    const char* split_chars;
    const char* skip_chars;
    const char* suppressors;
    if (!PyArg_ParseTuple(args, "ssss", &str, &split_chars, &skip_chars, &suppressors)) {
        PyErr_SetString(PyExc_RuntimeError, "split: error parsing arguments");
    }
    
    std::deque<std::string> result;
    int use_suppressors = strlen(suppressors) == 2;
    int in_node = 0;
    
    const char* p = str;
    char c;
    
    char cur[5000] = { 0 };
    char* curp = cur;
    
    static char single_char[2] = { 0 };
    
    while (c = *p++) {
        if ((!in_node && strchr(split_chars, c) != NULL) ||
            (strchr(skip_chars, c) != NULL) ||
            (strchr(suppressors, c) != NULL)) {
            
            if (cur[0] != '\0') {
                *curp++ = '\0';
                result.push_back(std::string(cur));
                
                cur[0] = '\0';
                curp = cur;
            }
            
            if (use_suppressors) {
                if (c == suppressors[0]) in_node = 1;
                else if (c == suppressors[1]) in_node = 0;
            }
            
            if (strchr(split_chars, c) != NULL ||
                strchr(suppressors, c) != NULL) {
                    
                single_char[0] = c; single_char[1] = '\0';
                result.push_back(std::string(single_char));
                single_char[0] = '\0';
            }
        } else {
            *curp++ = c;
        }
    }
    
    if (cur[0] != '\0') {
        *curp++ = '\0';
        result.push_back(cur);
    }

    return result;
}

static PyMethodDef augparse_methods[] = {
    /* name    ptr to function               flags         doc */
    { "augpenn_parse", (PyCFunction)augparse_augpenn_parse, METH_VARARGS, "" },
    { NULL, NULL, 0, NULL }
};

extern "C" void initaugparse(void) {
    PyObject* module = PyImport_ImportModule("munge.cats.headed.parse");
        if (module == NULL) {
            PyErr_SetString(PyExc_ImportError, "Could not load munge.cats.headed.parse");
            return;
        }
        
        PyObject* module_dict = PyModule_GetDict(module);
            parse_category_f = PyDict_GetItemString(module_dict, "parse_category");
            Py_XINCREF(parse_category_f);
        Py_XDECREF(module_dict);
    Py_XDECREF(module);
    
    module = PyImport_ImportModule("munge.penn.aug_nodes");
        if (module == NULL) {
            PyErr_SetString(PyExc_ImportError, "Could not load munge.penn.aug_nodes");
            return;
        }
        module_dict = PyModule_GetDict(module);
            Leaf_f = PyDict_GetItemString(module_dict, "Leaf");
            Py_XINCREF(Leaf_f);
            Node_f = PyDict_GetItemString(module_dict, "Node");
            Py_XINCREF(Node_f);
        Py_XDECREF(module_dict);
    Py_XDECREF(module);
    
    Py_InitModule("augparse", augparse_methods);
}
