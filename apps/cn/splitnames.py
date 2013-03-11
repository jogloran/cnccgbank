# coding: utf-8
from munge.proc.filter import Filter
from apps.cn.output import OutputPTBDerivation

from munge.penn.aug_nodes import Leaf, Node
from munge.trees.traverse import nodes, leaves
from munge.proc.tgrep.tgrep import find_all

from apps.cn.fix_utils import replace_kid

baixing = u'王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤'
expr = r'/NP-PN/ [ #<1 | #<2 ] < { ^/...?$/u=N [ > { * #<1 } | $ ^/先生|女士|博士|总统|教授|小姐|总经理|夫人/u ] }'
class SplitNames(Filter, OutputPTBDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputPTBDerivation.__init__(self, outdir)
        
    def accept_derivation(self, bundle):
        for node, ctx in find_all(bundle.derivation, expr, with_context=True):
            u = ctx.n.lex.decode('u8')
            if u[0] in baixing:
                leaf = ctx.n
                kids = [ Leaf(leaf.tag, u[0].encode('u8'), None), Leaf(leaf.tag, u[1:].encode('u8'), None) ]
                replace_kid(ctx.n.parent, ctx.n, Node('NR', kids))
                #node.kids = kids
                
        self.write_derivation(bundle)
