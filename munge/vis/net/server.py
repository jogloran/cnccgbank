from selector import Selector
from munge.cptb.io import CPTBReader
from munge.trees.traverse import leaves, is_ignored
import os, cgi
from itertools import count, izip

CORPORA_PATH = os.path.join('corpora', 'cptb', 'bracketed')
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

def view_deriv(env, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    variables = env['selector.vars']
    
    doc_id, deriv_id = int(variables['doc']), int(variables['deriv'])
    filename = 'chtb_%04d.fid' % doc_id
    
    doc = CPTBReader(os.path.join(CORPORA_PATH, filename))
    if doc:
        bundle = doc[deriv_id]
    
        if bundle:
            body = '<div id="main">'
            for leaf, n in izip(leaves(bundle.derivation, lambda e: not is_ignored(e)), count()):
                body += '''<span class="word"><span id="word%(index)d" onmouseover="$('pos').show();$('pos%(index)s').show();" onmouseout="$('pos%(index)s').hide();$('pos').hide();">%(body)s</span></span>''' % {
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
        
def hello(env, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    return ["<b>Hello world!</b>"]
    
def error_document():
    return 'Error'

routes = Selector()
routes.add('/view/{doc}/{deriv}', GET=view_deriv)
routes.add('/hello', GET=hello)

from wsgiref import simple_server
srv = simple_server.WSGIServer(
    ('', 8000),
    simple_server.WSGIRequestHandler
)

srv.set_app(routes)
srv.serve_forever()