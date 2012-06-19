#include "Python.h"

#include <iostream>
#include <deque>
#include <string>
#include <stdio.h>

static PyObject* _parse_docs(PyObject* self, PyObject* args);
static PyObject* _parse_doc(std::deque<std::string>& toks);
static std::deque<std::string> pressplit2_split(PyObject* self, PyObject* args);
static void shift_and_check(std::string must_match, std::deque<std::string>& toks);
static PyObject* pressplit2_augpenn_parse(PyObject* self, PyObject* args);
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

static PyObject* pressplit2_augpenn_parse(PyObject* self, PyObject* args) {
    return _parse_docs(self, args);
}

static PyObject* _parse_docs(PyObject* self, PyObject* args) {
    std::deque<std::string> toks = pressplit2_split(self, args);
    // std::cout << "ntoks: " << toks.size() << std::endl;
    for (std::deque<std::string>::const_iterator it = toks.begin();
        it != toks.end(); ++it) {
        // std::cout << *it << std::endl;
    }
    
    
    PyObject* result = PyList_New((Py_ssize_t)0);
    while (toks.size() > 0 && toks.front() == "(") {
        // std::cout << "Reading doc" << std::endl;
        PyObject* doc = _parse_doc(toks);
        // std::cout << "Read doc" << doc << std::endl;
        PyList_Append( result, doc );
        // std::cout << "Appended doc" << result << std::endl;
    }
    // std::cout << "done parsing docs" << std::endl;
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
        parent = Py_None; Py_INCREF(Py_None);
    }
    
    // std::cout << "-1" << toks.front() << std::endl;
    shift_and_check("(", toks);
    // std::cout << "-1" << toks.front() << std::endl;    
    // tag = toks.next()
    std::string tag = toks.front(); toks.pop_front();
    // std::cout << "-1a" << toks.front() << std::endl;    
    //     head_index = None
    //     if toks.peek() == '<':
    int head_index = -1;
    if (toks.front() == "<") {
        // std::cout << "-2" << std::endl;
        //         toks.next()
        toks.pop_front();
        //         head_index = int(toks.next())
        // std::cout << "atoi " << atoi(toks.front().c_str()) << std::endl;
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
        category = PyObject_CallObject(parse_category_f, cat);
        // std::cout << "category " << category << std::endl;
//         shift_and_check( '}', toks )
        shift_and_check("}", toks);
    }
    
    if (category == NULL) {
        category = Py_None; Py_INCREF(Py_None);
    }
// 
//     kids = []
    // std::cout << "-M" << std::endl;
    PyObject* kids = PyList_New((Py_ssize_t)0);
// 
//     lex = None
    std::string lex;
//     while toks.peek() != ')':
    while (toks.front() != ")") {
//         if toks.peek() == '(':
        if (toks.front() == "(") {
//             kids.append( self.read_deriv(toks) )
            PyList_Append( kids, _parse(toks) );
//         else:
        } else {
//             lex = toks.next()
            // std::cout << "lex " << toks.front() << std::endl;
            lex = toks.front(); toks.pop_front();
        }
    }
    
    // std::cout << "-P" << toks.front() << std::endl;
// 
//     if (not kids) and lex:
    if (PyList_Size(kids) == 0 && lex.length() != 0) {
//         return A.Leaf(tag, lex, category, parent)
        PyObject* args = Py_BuildValue("(ssOO)", tag.c_str(), lex.c_str(), category, parent);
        // std::cout << "-2 " << tag.c_str() << " " << lex.c_str() << " " << category << " " << parent << std::endl;        
        // std::cout << "-1 args: " << args << std::endl;
        PyObject* result = PyObject_CallObject(Leaf_f, args);
        // std::cout << "-RR1" << std::endl;
        // Py_DECREF(args); causes crash
        // std::cout << "-R1" << std::endl;
                    
        shift_and_check(")", toks);
        
        return result;
//     else:
    } else {
//         ret = A.Node(tag, kids, category, parent, head_index)
        PyObject* args = Py_BuildValue("(sOOOi)", tag.c_str(), kids, category, parent, head_index);
        // std::cout << "-2 " << tag.c_str() << " " << kids << " " << category << " " << parent << " " <<  head_index << std::endl;
        // std::cout << "-2 args: " << args << std::endl;
        PyObject* result = PyObject_CallObject(Node_f, args);
        // Py_DECREF(args); causes crash
        // std::cout << "-R2" << toks.front() << std::endl;
//         for kid in ret: kid.parent = ret
        PyObject *iterator = PyObject_GetIter(result);
        PyObject *kid;
        // if (iterator == NULL) {}
        while (kid = PyIter_Next(iterator)) {
            PyObject_SetAttrString(kid, "parent", result);
        }
        
        // TODO:
        shift_and_check(")", toks);
        
        return result;
    }
    
    Py_RETURN_NONE;
}

// static PyObject* pressplit2_split(PyObject* self, PyObject* args) {
static std::deque<std::string> pressplit2_split(PyObject* self, PyObject* args) {
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

    // for (std::deque<std::string>::const_iterator it = result.begin();
    //     it != result.end(); ++it) {
    //     // std::cout << *it << std::endl;
    // }
    
    return result;
    // Py_RETURN_NONE;
}

static PyMethodDef pressplit2_methods[] = {
    /* name    ptr to function               flags         doc */
    { "augpenn_parse", (PyCFunction)pressplit2_augpenn_parse, METH_VARARGS, "" },
    { NULL, NULL, 0, NULL }
};

extern "C" void initpressplit2(void) {
    // std::cout << "initpressplit2" << std::endl;
    PyObject* module = PyImport_ImportModule("munge.cats.headed.parse");
        if (module == NULL) {
            PyErr_SetString(PyExc_ImportError, "Could not load munge.cats.headed.parse");
            return;
        }
        // // std::cout << "here " << module << std::endl;
        PyObject* module_dict = PyModule_GetDict(module);
        // // std::cout << "here" << std::endl;
        parse_category_f = PyDict_GetItemString(module_dict, "parse_category");
        Py_INCREF(parse_category_f);
        // // std::cout << "Loaded parse_category: " << parse_category_f << std::endl;    
    Py_DECREF(module);
    
    module = PyImport_ImportModule("munge.penn.aug_nodes");
    if (module == NULL) {
        PyErr_SetString(PyExc_ImportError, "Could not load munge.penn.aug_nodes");
        return;
    }
    module_dict = PyModule_GetDict(module);
        Leaf_f = PyDict_GetItemString(module_dict, "Leaf");
        Py_INCREF(Leaf_f);
        Node_f = PyDict_GetItemString(module_dict, "Node");
        Py_INCREF(Node_f);
    Py_DECREF(module_dict);
    
    Py_InitModule("pressplit2", pressplit2_methods);
}
