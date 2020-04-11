from ply.yacc import yacc
from lexer import UCLexer
import ast


def _lex_err(msg, ln, co):
    print(f'Lexical error: {msg} at {ln}:{co}')


class ParseError(Exception):
    pass


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
        raise ParseError("{}: {}".format(coord, msg))

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

    def _token_coord(self, p, token_idx, def_column=False):
        """ Returns the coordinates for the YaccProduction objet 'p' indexed
            with 'token_idx'. The coordinate includes the 'lineno' and
            'column'. Both follow the lex semantic, starting from 1.
        """
        last_cr = p.lexer.lexer.lexdata.rfind('\n', 0, p.lexpos(token_idx))
        if last_cr < 0:
            last_cr = -1
        column = (p.lexpos(token_idx) - (last_cr))
        return ast.Coord(p.lineno(token_idx), 1 if def_column else column)

    def _build_function_definition(self, spec, decl, param_decls, body):
        """ Builds a function definition.
        """
        declaration = self._build_declarations(
            spec=spec,
            decls=[dict(decl=decl, init=None)])[0]

        return ast.FuncDef(
            decl=declaration,
            param_decls=param_decls,
            body=body,
            coord=decl.coord)

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

    def p_function_definition_1(self, p):
        """ function_definition : type_specifier declarator declaration_list_opt compound_statement
        """
        p[0] = self._build_function_definition(p[1], p[2], p[3], p[4])

    def p_function_definition_2(self, p):
        """ function_definition : declarator declaration_list_opt compound_statement
        """
        spec = dict(
            type=[ast.Type.build_void(self._token_coord(p, 1))],
            function=[])

        p[0] = self._build_function_definition(spec, p[1], p[2], p[3])

    def p_declarator(self, p):
        """ declarator : direct_declarator
        """
        p[0] = p[1]

    def p_declaration(self, p):
        """ declaration : decl_body SEMI
        """
        p[0] = p[1]

    def p_decl_body(self, p):
        """ decl_body : type_specifier init_declarator_list
                      | type_specifier empty
        """
        type_spec = p[1]
        decls = self._build_declarations(type_spec, p[2])\
            if p[2] is not None else None
        p[0] = decls

    def p_init_declarator(self, p):
        """ init_declarator : declarator
                            | declarator ASSIGN initializer
        """
        p[0] = dict(decl=p[1], init=(p[3] if len(p) > 2 else None))

    def p_init_declarator_list(self, p):
        """ init_declarator_list : init_declarator
                                 | init_declarator_list COMMA init_declarator
        """
        p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]

    def p_initializer_1(self, p):
        """ initializer : assignment_expression
        """
        p[0] = p[1]

    def p_initializer_2(self, p):
        """ initializer : LBRACE initializer_list RBRACE
                        | LBRACE initializer_list COMMA RBRACE
        """
        p[0] = ast.InitList([], self._token_coord(p, 1)) \
            if p[2] is None else p[2]

    def p_initializer_list(self, p):
        """ initializer_list : initializer
                             | initializer_list COMMA initializer
        """
        if len(p) == 2:
            p[0] = ast.InitList([p[1]], p[1].coord)
        else:
            p[1].exprs.append(p[3])
            p[0] = p[1]

    def p_declaration_list(self, p):
        """ declaration_list : declaration
                             | declaration_list declaration
        """
        p[0] = p[1] + p[2] if len(p) == 3 else p[1]

    def p_declaration_list_opt(self, p):
        """ declaration_list_opt : declaration_list
                                 | empty
        """
        p[0] = p[1]

    def p_direct_declarator_1(self, p):
        """ direct_declarator : identifier
        """
        p[0] = p[1]

    def p_direct_declarator_2(self, p):
        """ direct_declarator : LPAREN declarator RPAREN
        """
        p[0] = p[2]

    def p_direct_declarator_3(self, p):
        """ direct_declarator : direct_declarator LBRACKET constant_expression RBRACKET
                              | direct_declarator LBRACKET empty RBRACKET
        """
        array = ast.ArrayDecl(None, p[3], p[1].coord)
        p[0] = self._type_modify_decl(p[1], array)

    def p_direct_declarator_4(self, p):
        """ direct_declarator : direct_declarator LPAREN parameter_list RPAREN
                              | direct_declarator LPAREN identifier_list RPAREN
                              | direct_declarator LPAREN empty RPAREN
        """
        func = ast.FuncDecl(p[3], None, p[1].coord)
        p[0] = self._type_modify_decl(p[1], func)

    def p_constant_expression(self, p):
        """ constant_expression : binary_expression
        """
        p[0] = p[1]

    def p_block_item(self, p):
        """ block_item  : declaration
                        | statement
        """
        p[0] = p[1] if isinstance(p[1], list) else [p[1]]

    def p_block_item_list(self, p):
        """ block_item_list : block_item
                            | block_item_list block_item
        """
        p[0] = list(filter(
            lambda x: x is not None,
            p[1] if len(p) == 2 else p[1] + p[2]))

    def p_compound_statement(self, p):
        """ compound_statement   : LBRACE block_item_list RBRACE
        """
        p[0] = ast.Compound(block_items=p[2], coord=self._token_coord(p, 1, def_column=True))

    def p_selection_statement(self, p):
        """ selection_statement : IF LPAREN expression RPAREN statement
                                | IF LPAREN expression RPAREN statement ELSE statement
        """
        p[0] = ast.If(p[3], p[5], p[7] if len(p) > 7 else None, self._token_coord(p, 1))

    def p_iteration_statement_1(self, p):
        """ iteration_statement : WHILE LPAREN expression RPAREN statement
        """
        p[0] = ast.While(p[3], p[5], self._token_coord(p, 1))

    def p_iteration_statement_2(self, p):
        """ iteration_statement : FOR LPAREN expression_opt SEMI expression_opt SEMI expression_opt RPAREN statement
        """
        p[0] = ast.For(p[3], p[5], p[7], p[9], self._token_coord(p, 1))

    def p_iteration_statement_3(self, p):
        """ iteration_statement : FOR LPAREN declaration expression_opt SEMI expression_opt RPAREN statement
        """
        p[0] = ast.For(ast.DeclList(p[3], self._token_coord(p, 1)), p[4], p[6], p[8], self._token_coord(p, 1))

    def p_expression_statement(self, p):
        """ expression_statement : expression SEMI
                                 | empty SEMI
        """
        if p[1] is not None:
            p[0] = p[1]
        else:
            p[0] = ast.EmptyStatement(self._token_coord(p, 2))

    def p_assert_statement(self, p):
        """ assert_statement : ASSERT expression SEMI
        """
        p[0] = ast.Assert(p[2], self._token_coord(p, 1))

    def p_print_statement(self, p):
        """ print_statement : PRINT LPAREN expression RPAREN SEMI
                            | PRINT LPAREN empty RPAREN SEMI
        """
        p[0] = ast.Print(p[3], self._token_coord(p, 1))

    def p_read_statement(self, p):
        """ read_statement : READ LPAREN argument_expression RPAREN SEMI
        """
        p[0] = ast.Read(p[3], self._token_coord(p, 1))

    def p_statement(self, p):
        """ statement   : expression_statement
                        | selection_statement
                        | compound_statement
                        | iteration_statement
                        | jump_statement
                        | assert_statement
                        | print_statement
                        | read_statement
        """
        p[0] = p[1]

    def p_empty(self, p):
        """ empty :
        """
        p[0] = None

    def p_type_specifier(self, p):
        """ type_specifier : VOID
                           | CHAR
                           | INT
                           | FLOAT
        """
        p[0] = ast.Type([p[1]], self._token_coord(p, 1))

    def p_binary_expression(self, p):
        """ binary_expression   : cast_expression
                                | binary_expression TIMES binary_expression
                                | binary_expression DIVIDE binary_expression
                                | binary_expression MOD binary_expression
                                | binary_expression PLUS binary_expression
                                | binary_expression MINUS binary_expression
                                | binary_expression LT binary_expression
                                | binary_expression LTE binary_expression
                                | binary_expression GT binary_expression
                                | binary_expression GTE binary_expression
                                | binary_expression EQUALS binary_expression
                                | binary_expression NE binary_expression
                                | binary_expression AND binary_expression
                                | binary_expression OR binary_expression
        """
        p[0] = p[1] if len(p) == 2 else ast.BinaryOp(p[2], p[1], p[3], p[1].coord)

    def p_cast_expression_1(self, p):
        """ cast_expression : unary_expression
        """
        p[0] = p[1]

    def p_cast_expression_2(self, p):
        """ cast_expression : LPAREN type_specifier RPAREN cast_expression
        """
        p[0] = ast.Cast(p[2], p[4], self._token_coord(p, 1))

    def p_unary_expression_1(self, p):
        """ unary_expression : postfix_expression
        """
        p[0] = p[1]

    def p_unary_expression_2(self, p):
        """ unary_expression : PLUSPLUS unary_expression
                             | MINUSMINUS unary_expression
                             | unary_operator cast_expression
        """
        return ast.UnaryOp(p[1], p[2], p[2].coord)

    def p_unary_operator(self, p):
        """ unary_operator : ADDRESS
                           | TIMES
                           | PLUS
                           | MINUS
                           | NOT
        """
        p[0] = p[1]

    def p_postfix_expression_1(self, p):
        """ postfix_expression : primary_expression
        """
        p[0] = p[1]

    def p_postfix_expression_2(self, p):
        """ postfix_expression : postfix_expression LBRACKET expression RBRACKET
        """
        p[0] = ast.ArrayRef(p[1], p[3], p[1].coord)

    def p_postfix_expression_3(self, p):
        """ postfix_expression : postfix_expression LPAREN argument_expression RPAREN
                               | LPAREN RPAREN
        """
        p[0] = ast.FuncCall(p[1], p[3] if len(p) > 4 else None, p[1].coord)

    def p_postfix_expression_4(self, p):
        """ postfix_expression : postfix_expression PLUSPLUS
                               | postfix_expression MINUSMINUS
        """
        p[0] = ast.UnaryOp('p' + p[2], p[1], p[1].coord)

    def p_constant_1(self, p):
        """ constant : INT_CONST
        """
        p[0] = ast.Constant('int', p[1], self._token_coord(p, 1))

    def p_constant_2(self, p):
        """ constant : FLOAT_CONST
        """
        p[0] = ast.Constant('float', p[1], self._token_coord(p, 1))

    def p_constant_3(self, p):
        """ constant : CHAR_CONST
        """
        p[0] = ast.Constant('char', p[1], self._token_coord(p, 1))

    def p_constant_4(self, p):
        """ constant : STRING_CONST
        """
        p[0] = ast.Constant('string', p[1], self._token_coord(p, 1))

    def p_expression(self, p):
        """ expression : assignment_expression
                       | expression COMMA assignment_expression
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ast.ExprList.concat_exprs(p[1], p[3])

    def p_expression_opt(self, p):
        """ expression_opt : expression
                           | empty
        """
        p[0] = p[1]

    def p_argument_expression(self, p):
        """ argument_expression : assignment_expression
                                | argument_expression COMMA assignment_expression
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ast.ExprList.concat_exprs(p[1], p[3])

    def p_assignment_expression(self, p):
        """ assignment_expression : binary_expression
                                  | unary_expression assignment_operator assignment_expression
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ast.Assignment(p[2], p[1], p[3], self._token_coord(p[1], 1))

    def p_assignment_operator(self, p):
        """ assignment_operator : ASSIGN
                                | TIMESASSIGN
                                | DIVIDEASSIGN
                                | MODASSIGN
                                | PLUSASSIGN
                                | MINUSASSIGN
        """
        p[0] = p[1]

    def p_primary_expression_1(self, p):
        """ primary_expression : identifier
                               | constant
        """
        p[0] = p[1]

    def p_primary_expression_2(self, p):
        """ primary_expression : LPAREN expression RPAREN
        """
        p[0] = p[2]

    def p_identifier(self, p):
        """ identifier : ID
        """
        p[0] = ast.ID(p[1], self._token_coord(p, 1))

