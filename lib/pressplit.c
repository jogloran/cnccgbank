#include "Python.h"

static PyObject* pressplit_base_tag(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* tag;
    PyObject* strip_cptb_tag = Py_True;
    PyObject* strip_tag = Py_True;
    
    static char* kwarg_names[] = { "tag", "strip_cptb_tag", "strip_tag", NULL };
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|OO", kwarg_names, &tag, &strip_cptb_tag, &strip_tag)) {
        return NULL;
    }
    
    printf("here (%s, %x, %x)\n", tag, PyObject_IsTrue(strip_cptb_tag), PyObject_IsTrue(strip_tag));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject* pressplit_split(PyObject* self, PyObject* args) {
    const char* str;
    const char* split_chars;
    const char* skip_chars;
    const char* suppressors;
    if (!PyArg_ParseTuple(args, "ssss", &str, &split_chars, &skip_chars, &suppressors)) {
        return NULL;
    }
    
    PyObject* result;
    int use_suppressors = strlen(suppressors) == 2;
    int in_node = 0;
    
    const char* p = str;
    char c;
    
    char cur[1024] = { 0 };
    char* curp = cur;
    
    static char single_char[2] = { 0 };
    
    result = PyList_New((Py_ssize_t)0);
    
    while (c = *p++) {
        if ((!in_node && strchr(split_chars, c) != NULL) ||
            (strchr(skip_chars, c) != NULL) ||
            (strchr(suppressors, c) != NULL)) {
            
            if (cur[0] != '\0') {
                *curp++ = '\0';
                PyObject* new_string = PyString_FromString(cur);
                if (!new_string) {
                    return NULL;
                }
                
                if (PyList_Append(result, new_string) != 0) {
                    return NULL;
                }
                
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
                PyObject* new_string = PyString_FromString(single_char);
                if (!new_string) return NULL;
                single_char[0] = '\0';
                
                if (PyList_Append(result, new_string) != 0) {
                    return NULL;
                }
            }
        } else {
            *curp++ = c;
        }
    }
    
    if (cur[0] != '\0') {
        *curp++ = '\0';
        PyObject* new_string = PyString_FromString(cur);
        if (!new_string) {
            return NULL;
        }
        
        if (PyList_Append(result, new_string) != 0) {
            return NULL;
        }
    }
    
    return result;
    // Py_INCREF(Py_None);
    // return Py_None;
}

static PyMethodDef pressplit_methods[] = {
    /* name    ptr to function               flags         doc */
    { "split", (PyCFunction)pressplit_split, METH_VARARGS, "" },
    { "base_tag", (PyCFunctionWithKeywords)pressplit_base_tag, METH_VARARGS | METH_KEYWORDS, "" },
    { NULL, NULL, 0, NULL }
};

void initpressplit(void) {
    Py_InitModule("pressplit", pressplit_methods);
}


