from ast import *


class uCType(object):
    """
    Class that represents a type in the uC language.  Types
    are declared as singleton instances of this type.
    """

    def __init__(self, name, unary_ops=set(), binary_ops=set(), rel_ops=set(), assign_ops=set()):
        self.typename = name
        self.unary_ops = unary_ops
        self.binary_ops = binary_ops
        self.rel_ops = rel_ops
        self.assign_ops = assign_ops


# Create specific instances of types. You will need to add
# appropriate arguments depending on your definition of uCType
VoidType = uCType("void")
IntType = uCType("int",
                 unary_ops={"-", "+", "--", "++", "p--", "p++", "*", "&"},
                 binary_ops={"+", "-", "*", "/", "%"},
                 rel_ops={"==", "!=", "<", ">", "<=", ">="},
                 assign_ops={"=", "+=", "-=", "*=", "/=", "%="})

FloatType = uCType("float",
                   unary_ops={"-", "+", "--", "++", "p--", "p++", "*", "&"},
                   binary_ops={"+", "-", "*", "/", "%"},
                   rel_ops={"==", "!=", "<", ">", "<=", ">="},
                   assign_ops={"=", "+=", "-=", "*=", "/=", "%="})
CharType = uCType("char",
                  unary_ops={"-", "+", "--", "++", "p--", "p++", "*", "&"},
                  binary_ops={"+", "-", "*", "/", "%"},
                  rel_ops={"==", "!=", "<", ">", "<=", ">="},
                  assign_ops={"=", "+=", "-=", "*=", "/=", "%="})
StringType = uCType("string",
                    unary_ops={"+", "&"},
                    rel_ops={"==", "!="})
ArrayType = uCType("array",
                   unary_ops={"*", "&"},
                   rel_ops={"==", "!="})
# TODO: Complete uCTypes

type_table = {
    'void': VoidType,
    'int': IntType,
    'float': FloatType,
    'char': CharType,
    'string': StringType,
    'array': ArrayType
}


class NodeVisitor(object):
    """ A base NodeVisitor class for visiting uc_ast nodes.
        Subclass it and define your own visit_XXX methods, where
        XXX is the class name you want to visit with these
        methods.

        For example:

        class ConstantVisitor(NodeVisitor):
            def __init__(self):
                self.values = []

            def visit_Constant(self, node):
                self.values.append(node.value)

        Creates a list of values of all the constant nodes
        encountered below the given node. To use it:

        cv = ConstantVisitor()
        cv.visit(node)

        Notes:

        *   generic_visit() will be called for AST nodes for which
            no visit_XXX method was defined.
        *   The children of nodes for which a visit_XXX was
            defined will not be visited - if you need this, call
            generic_visit() on the node.
            You can use:
                NodeVisitor.generic_visit(self, node)
        *   Modeled after Python's own AST visiting facilities
            (the ast module of Python 3.0)
    """

    _method_cache = None

    def visit(self, node):
        """ Visit a node.
        """
        print(">", node)

        if self._method_cache is None:
            self._method_cache = {}

        visitor = self._method_cache.get(node.__class__.__name__, None)
        if visitor is None:
            method = 'visit_' + node.__class__.__name__
            visitor = getattr(self, method, self.generic_visit)
            self._method_cache[node.__class__.__name__] = visitor

        return visitor(node)

    def generic_visit(self, node):
        """ Called if no explicit visitor function exists for a
            node. Implements preorder visiting of the node.
        """
        for c in node:
            self.visit(c)


class SymbolTable(object):
    """
    Class representing a symbol table.  It should provide functionality
    for adding and looking up nodes associated with identifiers by their scopes.
    """

    def __init__(self):
        self.scope = -1
        self.symtabs = []

    def lookup(self, a):
        for i in range(self.scope, -1, -1):
            if a in self.symtabs[i]:
                return self.symtabs[i].get(a)
        return None

    def put(self, a, v):
        self.symtabs[self.scope][a] = v

    def begin_scope(self):
        self.scope += 1
        self.symtabs.append({})

    def end_scope(self):
        self.symtabs.pop()
        self.scope -= 1


class Visitor(NodeVisitor):
    """
    Program visitor class. This class uses the visitor pattern. You need to define methods
    of the form visit_NodeName() for each kind of AST node that you want to process.
    Note: You will need to adjust the names of the AST nodes if you picked different names.
    """

    def __init__(self):
        # Initialize the symbol table
        self.check_array = 0
        self.fmap = {}
        self.amap = {}
        self.symtab = SymbolTable()

    def type_from_id_or_const(self, look, error):
        if isinstance(look, ID):
            look_type = self.symtab.lookup(look.name)
            assert look_type, error
        elif isinstance(look, Constant):
            look_type = look.type
        elif isinstance(look, BinaryOp) or isinstance(look, FuncCall):
            look_type = self.visit(look)
        else:
            look_type = self.visit(look)
        return look_type

    def visit_Program(self, node):
        # 1. Visit all of the global declarations
        print('lets go')
        self.symtab.begin_scope()
        if node.gdecls is not None:
            for _decl in node.gdecls:
                self.visit(_decl)
        self.symtab.end_scope()

    def visit_BinaryOp(self, node):
        # Verifies if left and right element are ID or Constant
        left = self.type_from_id_or_const(node.lvalue, 'BinaryOp error: Left element not defined')
        right = self.type_from_id_or_const(node.rvalue, 'BinaryOp error: Right element not defined')

        assert left == right, "BinaryOp error: Elements type mismatch"
        assert node.op in type_table[left].binary_ops or node.op in type_table[left].rel_ops, \
            "BinaryOp error: Operator mismatch"
        return left

    def visit_Constant(self, node):
        return node.type

    def visit_Type(self, node):
        real_type = None
        if node.types is not None:
            return node.types[0]
        return real_type

    def visit_GlobalDecl(self, node):
        for _decl in node.decls:
            self.visit(_decl)

    def visit_Decl(self, node):
        if node.type is not None:
            if isinstance(node.type, ArrayDecl):
                node_type = self.amap[self.visit(node.type)][0]
            elif isinstance(node.type, FuncDecl):
                node_type = self.visit(node.type)
            elif isinstance(node.type, VarDecl):
                node_type = self.visit(node.type)
            if node.init is not None:
                init = self.visit(node.init)
                assert node_type == init, 'Declaration error: Init type differs from declared type'
        # assert cond, "Type mismatch in declaration operation"

    def visit_FuncDecl(self, node):
        # VERIFICA SE JA TEM O NOME SENA BOTA
        if node.type is not None and isinstance(node.type, VarDecl):
            node_type = self.visit(node.type)
            if node.args is not None and isinstance(node.args, ParamList):
                self.fmap[node.type.name.name] = self.visit(node.args)
        self.symtab.begin_scope()
        return node_type

    def visit_VarDecl(self, node):
        name = self.visit(node.name)
        var_type = self.visit(node.type)
        self.symtab.put(name, var_type)

        return var_type

    def visit_Cast(self, node):
        self.visit(node.expr)
        node.type = node.expr.type

    def visit_UnaryOp(self, node):
        name = self.visit(node.expr)
        var_type = self.symtab.lookup(name)
        assert node.op in type_table[var_type].unary_ops, "Unary operation: operator mismatch"

    def visit_ExprList(self, node):
        for _expr in node.exprs:
            self.visit(_expr)

    def visit_Assignment(self, node):
        left = self.symtab.lookup(self.visit(node.lvalue))
        assert left, "Assignment error: undefined element"
        # If right value is variable, searchs symbol table
        if isinstance(node.rvalue, ID) or isinstance(node.rvalue, ArrayRef):
            right = self.symtab.lookup(self.visit(node.rvalue))
        else:
            right = self.visit(node.rvalue)
        assert left == right, "Assignment error: Type mismatch"
        assert node.op in type_table[left].assign_ops, "Assignment error: operation mismatch"

    def visit_FuncDef(self, node):
        if node.decl is not None:
            self.visit(node.decl)
        for _decl in node.param_decls:
            self.visit(_decl)
        self.visit(node.body)

        # Begin scope after function declaration to make function global
        self.symtab.end_scope()

    def visit_FuncCall(self, node):
        # TODO: Count params
        assert self.visit(node.name) in self.fmap, 'Function Call error: function not declared'
        if isinstance(node.args, ID):
            self.visit(node.args)
        else:
            print("OH NO args in FuncCall is not ID")
        return self.symtab.lookup(self.visit(node.name))

    def visit_ID(self, node):
        return node.name

    def visit_ArrayDecl(self, node):
        name = None
        if isinstance(node.type, VarDecl):
            array_type = self.visit(node.type)
            if array_type == 'char':
                array_type = 'string'
            else:
                array_type = 'array'
            name = node.type.name
            self.symtab.put(self.visit(name), array_type)
            self.amap[self.visit(name)] = (
                array_type,
                [node.dim.value if node.dim is not None and isinstance(node.dim, Constant) else None]
            )
        if isinstance(node.type, ArrayDecl):
            name = self.visit(node.type)
            array_type = self.amap[self.visit(name)][0]
            if array_type == 'string':
                self.symtab.put(self.visit(name), 'array')
            self.amap[self.visit(name)][1].append(
                node.dim.value if node.dim is not None and isinstance(node.dim, Constant) else None
            )
        return name

    def visit_ArrayRef(self, node):
        array = self.symtab.lookup(self.visit(node.name))
        assert array, "Array Refence error: Array not declared"
        # FAZER O REF PARA STRIN G E ARRAY
        if array == 'string':
            return 'char'
        if array == 'array':
            pass
        if isinstance(node.subscript, ArrayRef):
            cmp_type = self.visit(node.subscript)
            assert cmp_type == 'int', "Array Refence error: Index not integer"
        elif isinstance(node.subscript, ID):
            cmp_type = self.symtab.lookup(self.visit(node.subscript))
            assert cmp_type == 'int', "Array Refence error: Index not integer"
        elif isinstance(node.subscript, Constant):
            cmp_type = self.visit(node.subscript)
            assert cmp_type == 'int', "Array Refence error: Index not integer"
        return self.visit(node.name)

    def visit_Compound(self, node):
        for _block in node.block_items:
            self.visit(_block)

    def visit_If(self, node):
        self.visit(node.cond)
        self.visit(node.iftrue)
        if node.iffalse is not None:
            self.visit(node.iffalse)

    def visit_While(self, node):
        self.visit(node.cond)
        self.visit(node.stmt)

    def visit_For(self, node):
        self.symtab.begin_scope()
        self.visit(node.init)
        self.visit(node.cond)
        self.visit(node.next)
        self.visit(node.stmt)
        self.symtab.end_scope()

    def visit_DeclList(self, node):
        for _decl in node.decls:
            self.visit(_decl)

    def visit_EmptyStatement(self, node):
        pass

    def visit_Assert(self, node):
        self.visit(node.expr)

    def visit_Print(self, node):
        if node.expr is not None:
            self.visit(node.expr)

    def visit_Read(self, node):
        if node.expr is not None:
            self.visit(node.expr)

    def visit_InitList(self, node):
        if node.exprs is not None:
            consistency = self.type_from_id_or_const(node.exprs[0], 'InitList error: Element not defined')
            for _expr in node.exprs:
                verify = self.type_from_id_or_const(_expr, 'InitList error: Element not defined')
                assert consistency == verify, 'InitList error: Type consistency'
        else:
            consistency = None
        return consistency

    def visit_ParamList(self, node):
        for _param in node.params:
            self.visit(_param)
        return node.params

    def visit_Break(self, node):
        pass

    def visit_Return(self, node):
        if node.expr is not None:
            self.visit(node.expr)
        print(self.symtab.symtabs, self.fmap)
