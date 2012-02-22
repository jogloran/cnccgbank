# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from selector import Selector
from munge.cptb.io import CPTBReader
from munge.trees.traverse import leaves, is_ignored
from munge.trees.pprint import pprint
import os, cgi
from itertools import count, izip
from munge.io.guess import GuessReader

#CORPORA_PATH = os.path.join('corpora', 'cptb', 'bracketed')
CORPORA_PATH = 'binarised'
cache = {}

Template = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html>
    <head>
        <script src='http://www.themissingyard.net/js/prototype.js'></script>
		<title>%s</title>
		<style type='text/css'>
			#main {
				margin: 0px auto;
				border: 1px solid black;
				padding: 10px;
				
				width: 60%%;
				font-size: 16pt;
				
				line-height: 140%%;
			}
			
			.word {
			    border: 1px solid #ddd;
			    margin: 1px;
			}
			
			.word:hover {
			    border: 1px solid gray;
			}
			
			#pos {
                margin: 0px auto;
                width: 60%%;
                padding: 10px;
                
                font-size: 18pt;
			}
			
			#tree {
			    font-family: monospace;
			    float: left;
			    
			    font-size: 10pt;
			}
			
			.highlighted {
			    color: #c33;
			    font-weight: bold;
			}
		</style>
		
		<body>
			<div id="content">
				%s
			</div>
		</body>
	</head>
'''
DefaultTitle = "Viewer"

def layout(body, title=None):
    return Template % (cgi.escape(title) if title else DefaultTitle, body)
    
def link_to(body, url):
    return '<a href="%s">%s</a>' % (cgi.escape(url), cgi.escape(body))
    
def prev_next_links(doc, doc_no, deriv_no):
    ret = []
    if doc[deriv_no-1]:
        ret += link_to('<', '/view/%s/%s' % (doc_no, deriv_no-1))
    if doc[deriv_no+1]:
        ret += link_to('>', '/view/%s/%s' % (doc_no, deriv_no+1))
    return ''.join(ret)
    
node_index = 0
def html_node_repr(node):
    global node_index # TODO: What's the proper way to do this in Python?
    if is_ignored(node): span_id = "trace"
    else: 
        span_id = "tree%d" % node_index
        node_index += 1
        
    return '(<span id="%s">%s %s</span>)' % (span_id, node.tag, node.lex)

def view_deriv(env, start_response):
    global node_index
    node_index = 0
    
    start_response('200 OK', [('Content-type', 'text/html')])
    variables = env['selector.vars']
    
    doc_id, deriv_id = int(variables['doc']), int(variables['deriv'])
    filename = 'chtb_%04d.fid' % doc_id
    
    doc = GuessReader(os.path.join(CORPORA_PATH, filename))
    if doc:
        bundle = doc[deriv_id]
    
        body = ''
        if bundle:
            body += '<div id="tree">'
            body += pprint(bundle.derivation, sep='&nbsp;', newline='<br/>', node_repr=html_node_repr)
            body += '</div>'
            
            body += '<div id="main">'
            for leaf, n in izip(leaves(bundle.derivation, lambda e: not is_ignored(e)), count()):
                body += '''<span class="word"><span id="word%(index)d" onmouseover="$('pos').show();$('pos%(index)s').show();$('tree%(index)s').addClassName('highlighted');" onmouseout="$('tree%(index)s').removeClassName('highlighted');$('pos%(index)s').hide();$('pos').hide();">%(body)s</span></span>''' % {
                    'index': n, 'body': leaf.lex
                }
                
            body += prev_next_links(doc, doc_id, deriv_id)
            body += '</div>'
            
            body += '<div id="pos">'
            body += '<span id="pos_display">'
            for leaf, n in izip(leaves(bundle.derivation, lambda e: not is_ignored(e)), count()):
                body += '<span id="pos%d" style="display:none">%s</span>' % (n, leaf.tag)
            body += '</span>'
            body += '</div>'
            
            yield layout(body)
        else:
            yield error_document()
        
    else:
        yield error_document()
    
def error_document():
    return 'Error'

routes = Selector()
routes.add('/view/{doc}/{deriv}', GET=view_deriv)

from wsgiref import simple_server
srv = simple_server.WSGIServer(
    ('', 8000),
    simple_server.WSGIRequestHandler
)

srv.set_app(routes)
srv.serve_forever()
