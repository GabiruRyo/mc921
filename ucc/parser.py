from ply.yacc import yacc
from lexer import UCLexer
import ast


def _lex_err(msg, ln, co):
    print(f'Lexical error: {msg} at {ln}:{co}')


class UCParser:
    tokens = UCLexer.tokens
    precedence = (
        ('left', 'OR'),
        ('left', 'AND'),
        ('left', 'EQUALS', 'NE'),
        ('left', 'GT', 'GTE', 'LT', 'LTE'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE', 'MOD')
    )

    def __init__(self):
        self._lexer = UCLexer(_lex_err)
        self._lexer.build()
        self._parser = yacc(module=self)

    def parse(self, code, debug=False):
        return self._parser.parse(
            input=code,
            lexer=self._lexer,
            debug=debug)

    def _parse_error(self, msg, coord):
        raise Exception("{}: {}".format(coord, msg))

    def _fix_decl_name_type(self, decl, typename):
        """ Fixes a declaration. Modifies decl.
        """
        # Reach the underlying basic type
        type = decl
        while not isinstance(type, ast.VarDecl):
            type = type.type

        decl.name = type.declname

        # The typename is a list of types. If any type in this
        # list isn't an Type, it must be the only
        # type in the list.
        # If all the types are basic, they're collected in the
        # Type holder.
        for tn in typename:
            if not isinstance(tn, ast.Type):
                if len(typename) > 1:
                    self._parse_error(
                        "Invalid multiple types specified", tn.coord)
                else:
                    type.type = tn
                    return decl

        if not typename:
            # Functions default to returning int
            if not isinstance(decl.type, ast.FuncDecl):
                self._parse_error("Missing type in declaration", decl.coord)
            type.type = ast.Type(['int'], coord=decl.coord)
        else:
            # At this point, we know that typename is a list of Type
            # nodes. Concatenate all the names into a single list.
            type.type = ast.Type(
                [typename.names[0]],
                coord=typename.coord)
        return decl

    def _build_declarations(self, spec, decls):
        """ Builds a list of declarations all sharing the given specifiers.
        """
        declarations = []

        for decl in decls:
            assert decl['decl'] is not None
            declaration = ast.Decl(
                name=None,
                type=decl['decl'],
                init=decl.get('init'),
                coord=decl['decl'].coord)

            fixed_decl = self._fix_decl_name_type(declaration, spec)
            declarations.append(fixed_decl)

        return declarations

    def _type_modify_decl(self, decl, modifier):
        """ Tacks a type modifier on a declarator, and returns
            the modified declarator.
            Note: the declarator and modifier may be modified
        """
        modifier_head = modifier
        modifier_tail = modifier

        # The modifier may be a nested list. Reach its tail.
        while modifier_tail.type:
            modifier_tail = modifier_tail.type

        # If the decl is a basic type, just tack the modifier onto it
        if isinstance(decl, ast.VarDecl):
            modifier_tail.type = decl
            return modifier
        else:
            # Otherwise, the decl is a list of modifiers. Reach
            # its tail and splice the modifier onto the tail,
            # pointing to the underlying basic type.
            decl_tail = decl

            while not isinstance(decl_tail.type, ast.VarDecl):
                decl_tail = decl_tail.type

            modifier_tail.type = decl_tail.type
            decl_tail.type = modifier_head
            return decl

    def p_program(self, p):
        """ program  : global_declaration_list
        """
        p[0] = ast.Program(p[1])

    def p_global_declaration_list(self, p):
        """ global_declaration_list : global_declaration
                                    | global_declaration_list global_declaration
        """
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

    def p_global_declaration_1(self, p):
        """ global_declaration : declaration
        """
        p[0] = ast.GlobalDecl(p[1])

    def p_global_declaration_2(self, p):
        """ global_declaration : function_definition
        """
        p[0] = p[1]

    def p_declaration(self, p):
        """ declaration : decl_body SEMI
        """
        p[0] = p[1]

    def p_declaration_list(self, p):
        """ declaration_list : declaration
                             | declaration_list declaration
        """
        p[0] = p[1] + p[2] if len(p) == 3 else p[1]