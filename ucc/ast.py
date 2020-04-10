import sys


def _repr(obj):
    """
    Get the representation of an object, with dedicated pprint-like format for lists.
    """
    if isinstance(obj, list):
        return '[' + (',\n '.join((_repr(e).replace('\n', '\n ') for e in obj))) + '\n]'
    else:
        return repr(obj)


def _filter_none(*it):
    return tuple(filter(lambda t: t[1] is not None, it))


class Node:
    """
    Base class example for the AST nodes.

    By default, instances of classes have a dictionary for attribute storage.
    This wastes space for objects having very few instance variables.
    The space consumption can become acute when creating large numbers of instances.

    The default can be overridden by defining __slots__ in a class definition.
    The __slots__ declaration takes a sequence of instance variables and reserves
    just enough space in each instance to hold a value for each variable.
    Space is saved because __dict__ is not created for each instance.
    """
    __slots__ = ()

    def __repr__(self):
        """ Generates a python representation of the current node
        """
        result = self.__class__.__name__ + '('
        indent = ''
        separator = ''
        for name in self.__slots__[:-2]:
            result += separator
            result += indent
            result += name + '=' + (
                _repr(getattr(self, name)).replace('\n', '\n  ' + (' ' * (len(name) + len(self.__class__.__name__)))))
            separator = ','
            indent = ' ' * len(self.__class__.__name__)
        result += indent + ')'
        return result

    def children(self):
        """ A sequence of all children that are Nodes
        """
        pass

    def show(self, buf=sys.stdout, offset=0, attrnames=False, nodenames=False, showcoord=False, _my_node_name=None):
        """ Pretty print the Node and all its attributes and children (recursively) to a buffer.
            buf:
                Open IO buffer into which the Node is printed.
            offset:
                Initial offset (amount of leading spaces)
            attrnames:
                True if you want to see the attribute names in name=value pairs. False to only see the values.
            nodenames:
                True if you want to see the actual node names within their parents.
            showcoord:
                Do you want the coordinates of each Node to be displayed.
        """
        lead = ' ' * offset
        if nodenames and _my_node_name is not None:
            buf.write(lead + self.__class__.__name__ + ' <' + _my_node_name + '>: ')
        else:
            buf.write(lead + self.__class__.__name__ + ': ')

        if self.attr_names:
            if attrnames:
                nvlist = [(n, getattr(self, n)) for n in self.attr_names if getattr(self, n) is not None]
                attrstr = ', '.join('%s=%s' % nv for nv in nvlist)
            else:
                vlist = [getattr(self, n) for n in self.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            buf.write(attrstr)

        if showcoord:
            if self.coord:
                buf.write('%s' % self.coord)
        buf.write('\n')

        for (child_name, child) in self.children():
            child.show(buf, offset + 4, attrnames, nodenames, showcoord, child_name)


class Coord:
    """ Coordinates of a syntactic element. Consists of:
            - Line number
            - (optional) column number, for the Lexer
    """
    __slots__ = ('line', 'column')

    def __init__(self, line, column=None):
        self.line = line
        self.column = column

    def __str__(self):
        if self.line:
            coord_str = "   @ %s:%s" % (self.line, self.column)
        else:
            coord_str = ""
        return coord_str


class Program(Node):
    __slots__ = ('gdecls', 'coord')
    attr_names = tuple()

    def __init__(self, gdecls, coord=None):
        self.gdecls = gdecls
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.gdecls or []):
            nodelist.append(("gdecls[%d]" % i, child))
        return tuple(nodelist)


class BinaryOp(Node):
    __slots__ = ('op', 'lvalue', 'rvalue', 'coord')
    attr_names = ('op',)

    def __init__(self, op, left, right, coord=None):
        self.op = op
        self.lvalue = left
        self.rvalue = right
        self.coord = coord

    def children(self):
        nodelist = []
        if self.lvalue is not None: nodelist.append(("lvalue", self.lvalue))
        if self.rvalue is not None: nodelist.append(("rvalue", self.rvalue))
        return tuple(nodelist)


class Constant(Node):
    __slots__ = ('type', 'value', 'coord')
    attr_names = ('type', 'value',)

    def __init__(self, type, value, coord=None):
        self.type = type
        self.value = value
        self.coord = coord

    def children(self):
        return tuple()


class Type(Node):
    __slots__ = ('types', 'coord')
    attr_names = ('types',)

    def __init__(self, types, coord=None):
        self.types = types
        self.coord = coord

    def children(self):
        return tuple()

    @classmethod
    def build_void(cls, coord=None):
        return Type(['void'], coord)


class GlobalDecl(Node):
    __slots__ = ('decls', 'coord')
    attr_names = tuple()

    def __init__(self, decls, coord=None):
        self.decls = decls if decls is not None else []
        self.coord = coord

    def children(self):
        return tuple(map(lambda decl: ('decl', decl), self.decls))


class Decl(Node):
    __slots__ = ('name', 'type', 'init', 'coord')
    attr_names = ('name',)

    def __init__(self, name, type, init, coord):
        self.name = name
        self.type = type
        self.init = init
        self.coord = coord

    def children(self):
        return _filter_none(('name', self.name), ('type', self.type))


class FuncDecl(Node):
    __slots__ = ('args', 'type', 'coord')
    attr_names = tuple()

    def __init__(self, args, type, coord=None):
        self.args = args
        self.type = type
        self.coord = coord

    def children(self):
        return _filter_none(('args', self.args), ('type', self.type))


class VarDecl(Node):
    __slots__ = ('name', 'type', 'coord')
    attr_names = tuple()

    def __init__(self, name, type, coord=None):
        self.name = name
        self.type = type
        self.coord = coord

    def children(self):
        return _filter_none(('type', self.type))


class Cast(Node):
    __slots__ = ('type', 'expr', 'coord')
    attr_names = tuple()

    def __init__(self, type, expr, coord=None):
        self.type = type
        self.expr = expr
        self.coord = coord

    def children(self):
        return _filter_none(('type', self.type), ('expr', self.expr))


class UnaryOp(Node):
    __slots__ = ('op', 'expr', 'coord')
    attr_names = ('op',)

    def __init__(self, op, expr, coord=None):
        self.op = op
        self.expr = expr
        self.coord = coord

    def children(self):
        return _filter_none(('expr', self.expr))


class ExprList(Node):
    __slots__ = ('exprs', 'coord')
    attr_names = tuple()

    def __init__(self, exprs, coord=None):
        self.exprs = exprs if exprs else []
        self.coord = coord

    def children(self):
        return tuple(map(lambda expr: ('expr', expr), self.exprs))

    @classmethod
    def concat_exprs(cls, expr_base, expr):
        if not isinstance(expr_base, cls):
            expr_base = ExprList([expr_base], expr_base.coord)
        expr_base.exprs.append(expr)


class Assignment(Node):
    __slots__ = ('op', 'lvalue', 'rvalue', 'coord')
    attr_names = ('op',)

    def __init__(self, op, lvalue, rvalue, coord=None):
        self.op = op
        self.lvalue = lvalue
        self.rvalue = rvalue
        self.coord = coord

    def children(self):
        return _filter_none(('lvalue', self.lvalue), ('rvalue', self.rvalue))


class FuncDef(Node):
    __slots__ = ('decl', 'param_decls', 'body', 'coord')
    attr_names = tuple()

    def __init__(self, decl, param_decls, body, coord=None):
        self.decl = decl
        self.param_decls = param_decls if param_decls else []
        self.body = body
        self.coord = coord

    def children(self):
        nodelist = [('decl', self.decl), ('body', self.body)]
        for i, child in enumerate(self.param_decls):
            nodelist.append(("param_decls[%d]" % i, child))
        return tuple(nodelist)


class FuncCall(Node):
    __slots__ = ('name', 'args', 'coord')
    attr_names = ()

    def __init__(self, name, args, coord=None):
        self.name = name
        self.args = args
        self.coord = coord

    def children(self):
        return _filter_none(('name', self.name), ('args', self.args))


class ID(Node):
    __slots__ = ('name', 'coord')
    attr_names = ('name',)

    def __init__(self, name, coord=None):
        self.name = name
        self.coord = coord

    def children(self):
        return tuple()


class ArrayDecl(Node):
    __slots__ = ('type', 'dim', 'coord')
    attr_names = tuple()

    def __init__(self, type, dim, coord=None):
        self.type = type
        self.dim = dim
        self.coord = coord

    def children(self):
        return _filter_none(('type', self.type), ('dim', self.dim))


class ArrayRef(Node):
    __slots__ = ('name', 'subscript', 'coord')
    attr_names = tuple()

    def __init__(self, name, subscript, coord=None):
        self.name = name
        self.subscript = subscript
        self.coord = coord

    def children(self):
        return _filter_none(('name', self.name), ('subscript', self.subscript))


class Compound(Node):
    __slots__ = ('block_items', 'coord')
    attr_names = tuple()

    def __init__(self, block_items, coord=None):
        self.block_items = block_items if block_items else []
        self.coord = coord

    def children(self):
        return tuple(map(lambda bi: ('block_items', bi), self.block_items))


class If(Node):
    __slots__ = ('cond', 'iftrue', 'iffalse', 'coord')
    attr_names = tuple()

    def __init__(self, cond, iftrue, iffalse, coord=None):
        self.cond = cond
        self.iftrue = iftrue
        self.iffalse = iffalse
        self.coord = coord

    def children(self):
        return _filter_none(('cond', self.cond), ('iftrue', self.iftrue), ('iffalse', self.iffalse))


class While(Node):
    __slots__ = ('cond', 'stmt', 'coord')
    attr_names = tuple()

    def __init__(self, cond, stmt, coord=None):
        self.cond = cond
        self.stmt = stmt
        self.coord = coord

    def children(self):
        return _filter_none(('cond', self.cond), ('stmt', self.stmt))


class For(Node):
    __slots__ = ('init', 'cond', 'next', 'stmt', 'coord')
    attr_names = tuple()

    def __init__(self, init, cond, next, stmt, coord=None):
        self.init = init
        self.cond = cond
        self.next = next
        self.stmt = stmt
        self.coord = coord

    def children(self):
        return _filter_none(
            ('init', self.init), ('cond', self.cond),
            ('next', self.next), ('stmt', self.stmt))


class DeclList(Node):
    __slots__ = ('decls', 'coord', '__weakref__')
    attr_names = tuple()

    def __init__(self, decls, coord=None):
        self.decls = decls if decls else []
        self.coord = coord

    def children(self):
        return tuple(map(lambda decl: ('decl', decl), self.decls))


class EmptyStatement(Node):
    __slots__ = ('coord', '__weakref__')
    attr_names = tuple()

    def __init__(self, coord=None):
        self.coord = coord

    def children(self):
        return tuple()


class Assert(Node):
    __slots__ = ('expr', 'coord')
    attr_names = ()

    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        return _filter_none(('assert', self.expr))


class Print(Node):
    __slots__ = ('expr', 'coord')
    attr_names = ()

    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        return _filter_none(('print', self.expr))


class Read(Node):
    __slots__ = ('expr', 'coord')
    attr_names = ()

    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        return _filter_none(('read', self.expr))


class InitList(Node):
    __slots__ = ('exprs', 'coord')
    attr_names = tuple()

    def __init__(self, exprs, coord=None):
        self.exprs = exprs
        self.coord = coord

    def children(self):
        return tuple(map(lambda expr: ('expr', expr), self.exprs))
