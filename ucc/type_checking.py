class uCType(object):
    """
    Class that represents a type in the uC language.  Types
    are declared as singleton instances of this type.
    """

    def __init__(self, name, element_type=set(), unary_ops=set(), binary_ops=set(), rel_ops=set(), assign_ops=set()):
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
                    element_type={"char"},
                    unary_ops={"+", "&"},
                    rel_ops={"==", "!="})
ArrayType = uCType("array",
                   element_type={"int", "float", "char"},
                   unary_ops={"*", "&"},
                   rel_ops={"==", "!="})
IDType = uCType("id",

)
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
    for adding and looking up nodes associated with identifiers.
    """

    def __init__(self):
        self.symtab = {}

    def lookup(self, a):
        return self.symtab.get(a)

    def add(self, a, v):
        self.symtab[a] = v

    def remove(self, a):
        del self.symtab[a]


class Visitor(NodeVisitor):
    """
    Program visitor class. This class uses the visitor pattern. You need to define methods
    of the form visit_NodeName() for each kind of AST node that you want to process.
    Note: You will need to adjust the names of the AST nodes if you picked different names.
    """

    def __init__(self):
        # Initialize the symbol table
        self.symtab = SymbolTable()

        # Add built-in type names (int, float, char) to the symbol table
        self.symtab.add("int", IntType)
        self.symtab.add("float", FloatType)
        self.symtab.add("char", CharType)
        self.symtab.add("string", StringType)

    def visit_Program(self, node):
        # 1. Visit all of the global declarations
        # 2. Record the associated symbol table
        for _decl in node.gdecls:
            self.visit(_decl)

    def visit_BinaryOp(self, node):
        # 1. Make sure left and right operands have the same type
        # 2. Make sure the operation is supported
        # 3. Assign the result type
        self.visit(node.lvalue)
        self.visit(node.rvalue)
        left, right = self.symtab.lookup(node.lvalue), self.symtab.lookup(node.rvalue)
        assert left and right, "binary operation with unknown sym"
        assert left.type == right.type, "Type mismatch in binary operation"
        node.type = node.lvalue.type
        assert node.op in type_table[node.type].binary_ops, "Operation mismatch in binary operation"

    def visit_Constant(self, node):
        self.symtab.add(node.value, type_table[node.type])

    def visit_Type(self, node):
        # TODO: implement type
        pass

    def visit_GlobalDecl(self, node):
        for _decl in node.decls:
            self.visit(_decl)

    def visit_Decl(self, node):
        self.symtab.add(node.name, type_table[node.type])
        self.visit(node.init)

    def visit_FuncDecl(self, node):
        for _arg in node.args:
            self.visit(_arg)

    def visit_VarDecl(self, node):
        pass

    def visit_Cast(self, node):
        self.visit(node.expr)
        node.type = node.expr.type

    def visit_UnaryOp(self, node):
        self.visit(node.expr)
        node.type = node.expr.type
        assert node.op in type_table[node.type].unary_ops, "Operation mismatch in unary operation"

    def visit_ExprList(self, node):
        for _expr in node.exprs:
            self.visit(_expr)

    def visit_Assignment(self, node):
        ## 1. Make sure the location of the assignment is defined
        left = self.symtab.lookup(node.lvalue)
        assert left, "Assigning to unknown sym"
        ## 2. Check that the types match
        self.visit(node.rvalue)
        assert left.name == node.rvalue.type, "Type mismatch in assignment"
        node.type = left.name
        assert node.op in type_table[node.type].assign_ops, "Operation mismatch in assignment operation"

    def visit_FuncDef(self, node):
        self.visit(node.decl)
        for _decl in node.param_decls:
            self.visit(_decl)
        self.visit(node.body)

    def visit_FuncCall(self, node):
        # TODO: Count params
        for _arg in node.args:
            self.visit(_arg)

    def visit_ID(self, node):
        pass

    def visit_ArrayDecl(self, node):
        self.visit(node.dim)

    def visit_ArrayRef(self, node):
        array = self.symtab.lookup(node.name)
        assert array, "Referencing unknown sym"
        node.type = array.name
        self.visit(node.subscript)

    def visit_Compound(self, node):
        for _block in node.block_items:
            self.visit(_block)

    def visit_If(self, node):
        self.visit(node.cond)
        self.visit(node.iftrue)
        if node.iffalse:
            self.visit(node.iffalse)

    def visit_While(self, node):
        self.visit(node.cond)
        self.visit(node.stmt)

    def visit_For(self, node):
        self.visit(node.init)
        self.visit(node.cond)
        self.visit(node.next)
        self.visit(node.stmt)

    def visit_DeclList(self, node):
        for _decl in node.decls:
            self.visit(_decl)

    def visit_EmptyStatement(self, node):
        pass

    def visit_Assert(self, node):
        self.visit(node.expr)

    def visit_Print(self, node):
        self.visit(node.expr)

    def visit_Read(self, node):
        self.visit(node.expr)

    def visit_InitList(self, node):
        for _expr in node.exprs:
            self.visit(_expr)

    def visit_ParamList(self, node):
        for _param in node.params:
            self.visit(_param)

    def visit_Break(self, node):
        pass

    def visit_Return(self, node):
        self.visit(node.expr)
