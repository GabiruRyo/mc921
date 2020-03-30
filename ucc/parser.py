import ply.yacc as yacc


class UCParser:
    """
     A lexer for the uC language.
    """

    # RULES

    def p_identifier(self, p):
        """ identifier : ID """
        # TODO: ID class
        p[0] = ID(p[1], lineno=p.lineno(1))

    def p_program(self, p):
        """
        program  : global_declaration_list
        """
        # TODO: Program class
        p[0] = Program(p[1])

    def p_global_declaration_list(self, p):
        """
        global_declaration_list : global_declaration
                                | global_declaration_list global_declaration
        """
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

    def p_function_definition(self, p):
        """
        <function_definition> ::= {<type_specifier>}? <declarator> {<declaration>}* <compound-statement>
        """
        # TODO: FunctionDefinition class
        p[0] = FunctionDefinition(p[1], p[2], p[3], p[4])

    def p_type_specifier(self, p):
        """
        <type_specifier> ::= void
                   | char
                   | int
                   | float
        """
        p[0] = p[1]

    def p_declarator(self, p):
        """
        <declarator> ::= <identifier>
               | ( <declarator> )
               | <declarator> [ {<constant_expression>}? ]
               | <declarator> ( <parameter_list> )
               | <declarator> ( {<identifier>}* )
        """
        #TODO
        pass

    def p_constant_expression(self, p):
        """
        <constant_expression> ::= <binary_expression>
        """
        p[0] = p[1]

    def p_binary_expression(self, p):
        """
        <binary_expression> ::= <cast_expression>
                      | <binary_expression * binary_expression
                      | binary_expression / binary_expression
                      | binary_expression % binary_expression
                      | binary_expression + binary_expression
                      | binary_expression - binary_expression
                      | binary_expression < binary_expression
                      | binary_expression <= binary_expression
                      | binary_expression > binary_expression
                      | binary_expression >= binary_expression
                      | binary_expression == binary_expression
                      | binary_expression != binary_expression
                      | binary_expression && binary_expression
                      | binary_expression || binary_expression
        """
        if len(p) == 2:
            p[0] = p[1]
        elif p[2] == '*':
            p[0] = p[1] * p[3]
        elif p[2] == '/':
            p[0] = p[1] / p[3]
        elif p[2] == '%':
            p[0] = p[1] % p[3]
        elif p[2] == '+':
            p[0] = p[1] + p[3]
        elif p[2] == '-':
            p[0] = p[1] - p[3]
        elif p[2] == '<':
            p[0] = p[1] < p[3]
        elif p[2] == '<=':
            p[0] = p[1] <= p[3]
        elif p[2] == '>':
            p[0] = p[1] > p[3]
        elif p[2] == '>=':
            p[0] = p[1] >= p[3]
        elif p[2] == '==':
            p[0] = p[1] == p[3]
        elif p[2] == '!=':
            p[0] = p[1] != p[3]
        elif p[2] == '&&':
            p[0] = p[1] and p[3]
        elif p[2] == '||':
            p[0] = p[1] or p[3]

    def cast_expression(self, p):
        """
        <cast_expression> ::= <unary_expression>
                    | ( <type_specifier> ) <cast_expression>
        """
        if len(p) == 2:
            p[0] = p[1]
        # TODO: Verify cast to void
        elif p[2] == 'void':
            p[0] = None
        elif p[2] == 'char':
            p[0] = str(p[4])
        elif p[2] == 'int':
            p[0] = int(p[4])
        elif p[2] == 'float':
            p[0] = float(p[4])

    def p_unary_expression(self, p):
        """
        <unary_expression> ::= <postfix_expression>
                     | ++ <unary_expression>
                     | -- <unary_expression>
                     | <unary_operator> <cast_expression>
        """
        pass

    def p_postfix_expression(self, p):
        """
        <postfix_expression> ::= <primary_expression>
                       | <postfix_expression> [ <expression> ]
                       | <postfix_expression> ( {<assignment_expression>}* )
                       | <postfix_expression> ++
                       | <postfix_expression> --
        """
        if len(p) == 2:
            p[0] = p[1]
        # TODO: <postfix_expression> [ <expression> ]
        elif p[2] == '[' and p[4] == ']':
            pass
        # TODO: <postfix_expression> ( {<assignment_expression>}* )
        elif p[2] == '(' and p[4] == ')':
            pass
        elif p[2] == '++':
            p[0] = p[1] + 1
        elif p[2] == '--':
            p[0] = p[1] - 1


    def p_primary_expression(self, p):
        """
        <primary-expression> ::= <identifier>
                           | <constant>
                           | <string>
                           | ( <expression> )
        """
        if len(p) == 2:
            p[0] = p[1]
        #TODO: ( <expression> )
        elif p[1] == '(' and p[3] == ')':


    def p_constant(self, p):
        """
        <constant> ::= <integer_constant>
                 | <character_constant>
                 | <floating_constant>
        """
        p[0] = p[1]

    def p_expression(self, p):
        """
        <expression> ::= <assignment_expression>
                   | <expression> , <assignment_expression>
        """
        pass

    def p_assignment_expression(self, p):
        """
        <assignment_expression> ::= <binary_expression>
                              | <unary_expression> <assignment_operator> <assignment_expression>
        """
        pass

    def p_assignment_operator(self, p):
        """
        <assignment_operator> ::= =
                            | *=
                            | /=
                            | %=
                            | +=
                            | -=
        """
        p[0] = p[1]

    def p_unary_operator(self, p):
        """
        <unary_operator> ::= &
                       | *
                       | +
                       | -
        """
        p[0] = p[1]

    def p_parameter_list(self, p):
        """
        <parameter_list> ::= <parameter_declaration>
                       | <parameter_list> , <parameter_declaration>
        """
        pass

    def p_parameter_declaration(self, p):
        """
        <parameter_declaration> ::= {<type_specifier>} <declarator>
        """
        pass

    def p_declaration(self, p):
        """
        <declaration> ::=  {<type_specifier>} {<init_declarator>}* ;
        """
        pass

    def p_init_declarator(self, p):
        """
        <init_declarator> ::= <declarator>
                        | <declarator> = <initializer>
        """
        pass

    def p_initializer(self, p):
        """
        <initializer> ::= <assignment_expression>
                    | { <initializer_list> }
                    | { <initializer_list> , }
        """
        pass

    def p_initializer_list(self, p):
        """
        <initializer_list> ::= <initializer>
                         | <initializer_list> , <initializer>
        """
        pass

    def p_compound_statement(self, p):
        """
        <compound_statement> ::= { {<declaration>}* {<statement>}* }
        """
        pass

    def p_statement(self, p):
        """
        <statement> ::= <expression_statement>
                  | <compound_statement>
                  | <selection_statement>
                  | <iteration_statement>
                  | <jump_statement>
                  | <assert_statement>
                  | <print_statement>
                  | <read_statement>
        """
        pass

    def p_expression_statement(self, p):
        """
        <expression_statement> ::= {<expression>}? ;
        """
        pass

    def p_selection_statement(self, p):
        """
        <selection_statement> ::= if ( <expression> ) <statement>
                            | if ( <expression> ) <statement> else <statement>
        """
        pass

    def p_iteration_statement(self, p):
        """
        <iteration_statement> ::= while ( <expression> ) <statement>
                            | for ( {<expression>}? ; {<expression>}? ; {<expression>}? ) <statement>
        """
        pass

    def p_jump_statement(self, p):
        """
        <jump_statement> ::= break ;
                       | return {<expression>}? ;
        """
        pass

    def p_assert_statement(self, p):
        """
        <assert_statement> ::= assert <expression> ;
        """
        pass

    def p_print_statement(self, p):
        """
        <print_statement> ::= print ( <expression>* ) ;
        """
        pass

    def p_read_statement(self, p):
        """
        <read_statement> ::= read ( <declarator>+ );
        """
        pass

    # Error rule for syntax errors
    def p_error(p):
        print("Syntax error in input!")

    # Build the parser
    parser = yacc.yacc()

    while True:
        try:
            s = raw_input('calc > ')
        except EOFError:
            break
        if not s:
            continue
        result = parser.parse(s)
        print(result)
