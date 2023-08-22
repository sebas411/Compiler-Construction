import sys
from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener
from antlr.YAPLLexer import YAPLLexer
from antlr.YAPLParser import YAPLParser
from antlr.YAPLListener import YAPLListener
from graphviz import Digraph
from antlr4.tree.Trees import Trees
from antlr.YAPLVisitor import YAPLVisitor
from lib import *

class TypeCheckingVisitor(YAPLVisitor):
    def __init__(self):
        self.current_class = None
        self.current_method = None
        self.classes = {}
        self.inheritance_info = {}
        self.active_lets = []
        self.last_let = 0

    def visitClass_prod(self, ctx:YAPLParser.Class_prodContext):
        self.current_class = ctx.TYPE_ID(0).getText()
        self.classes[self.current_class] = ClassObj(self.current_class)
        #self.symbol_table.append(ClassObj(self.current_class))  # crea un nuevo ámbito para la clase

        if ctx.INHERITS():
            inherited_class = ctx.TYPE_ID(1).getText()
            if inherited_class in self.classes:
                self.classes[self.current_class].inherit(self.classes[inherited_class])
                self.inheritance_info[self.current_class] = inherited_class
            else:
                print(f"La clase {inherited_class} no ha sido definida (línea {ctx.start.line})")
                self.inheritance_info[self.current_class] = None


        self.visitChildren(ctx)
        self.current_class = None


    def visitFeature(self, ctx:YAPLParser.FeatureContext):

        if ctx.getChild(1).getText() == "(": # method
            method_name = ctx.id_().getText()
            method_type = ctx.TYPE_ID().getText()
            self.current_method = method_name
            params = {}
            for param in ctx.formal():
                param_type = param.TYPE_ID().getText()
                param_name = param.id_().getText()
                params[param_name] = param_type
            self.classes[self.current_class].methods[method_name] = Method(method_type, params)
            return_type = self.get_expr_type(ctx.expr())
            print(return_type)
            self.current_method = None

        else: # attribute
            attribute_name = ctx.id_().getText()
            attribute_type = ctx.TYPE_ID().getText()
            self.classes[self.current_class].attributes[attribute_name] = attribute_type
            if ctx.expr():
                self.get_expr_type(ctx.expr())


    def visitChildren(self, node):
        result = []
        for child in node.getChildren():
            if isinstance(child, YAPLParser.ExprContext):
                childResult = self.visitExpr(child)
                if childResult is not None:
                    result.append(childResult)
            else:
                childResult = child.accept(self)
                if childResult is not None:
                    result.append(childResult)
        return result

    def get_expr_type(self, expr: YAPLParser.ExprContext):
        if expr.getChild(0).getText() == "{": #code block
            code_block_type = None
            for child in expr.expr():
                code_block_type = self.get_expr_type(child)
            return code_block_type
        elif expr.getChildCount() == 7 and expr.getChild(0).getSymbol().type == YAPLParser.IF: # If
            conditional_type = self.get_expr_type(expr.getChild(1))
            if conditional_type not in ["Bool", "Int"]:
                print(f"Se esperaba tipo Bool pero se obtuvo tipo {conditional_type} (línea {expr.start.line})")
                return "Error"
            then_type = self.get_expr_type(expr.getChild(3))
            else_type = self.get_expr_type(expr.getChild(5))

            # calculando el supertipo
            if then_type == else_type:
                return then_type
            elif then_type in self.inheritance_info and else_type in self.inheritance_info:
                if self.inheritance_info[then_type] == self.inheritance_info[else_type]:
                    return self.inheritance_info[then_type]
            elif then_type in self.inheritance_info:
                if self.inheritance_info[then_type] == else_type:
                    return else_type
            elif else_type in self.inheritance_info:
                if then_type == self.inheritance_info[else_type]:
                    return then_type
            print(f"Los tipos de las ramas then y else difieren: {then_type}, {else_type} (línea {expr.start.line})")
            return "Error"
        elif expr.getChildCount() >= 6 and expr.getChild(0).getText() == "let": # let
            self.last_let += 1
            let_name = f"let{self.last_let}"
            num_of_params = len(expr.id_())
            params = {}
            for i in range(num_of_params):
                if expr.id_(i).getText() not in params:
                    params[expr.id_(i).getText()] = expr.TYPE_ID(i).getText()
                else:
                    print(f"Variable local '{expr.id_(i).getText()}' definida múltiples veces (línea {expr.start.line})")
                    return "Error"

            for param in params.keys():
                if self.classes[self.current_class].has_attribute(self.current_method, self.active_lets, param):
                    print(f"Variable local '{param}' definida previamente (línea {expr.start.line})")
                    return "Error"
            for i in range(len(expr.expr())-1):
                self.get_expr_type(expr.expr(i))
            self.classes[self.current_class].lets[let_name] = params
            self.active_lets.append(let_name)
            let_type = self.get_expr_type(expr.expr()[-1])
            self.active_lets.pop()
            return let_type
        elif expr.getChildCount() >= 5 and (expr.getChild(1).getText() == "." or expr.getChild(3).getText() == "."): # class.method call
            class_type = self.get_expr_type(expr.getChild(0))
            if class_type not in self.classes:
                print(f"La clase {class_type} no ha sido declarada. (línea {expr.start.line})")
                return "Error"
            if expr.getChild(1).getText() == "@":
                parent_class = expr.getChild(2).getText()
                if class_type not in self.inheritance_info or self.inheritance_info[class_type] != parent_class:
                    print(f"La clase {class_type} no hereda de {parent_class}. (línea {expr.start.line})")
                    return "Error"
                method_name = expr.getChild(4).getText()
                called_class = parent_class
            else:
                method_name = expr.getChild(2).getText()
                called_class = class_type
            if method_name not in self.classes[called_class].methods:
                print(f"El método {method_name} no ha sido declarado en la clase {called_class}. (línea {expr.start.line})")
                return "Error"
            print(called_class, self.classes[called_class].methods)
            param_types = [self.get_expr_type(param) for param in expr.expr()[1:]]
            method_params = self.classes[called_class].methods[method_name].params
            method_param_num = len(method_params)
            param_num = len(param_types)
            if param_num != method_param_num:
                print(f"En la llamada del método {method_name} se esperaban {method_param_num} parámetros pero se obtuvieron {param_num}. (línea {expr.start.line})")
                return "Error"
            foundError = False
            for i in range(param_num):
                if not self.check_casting(list(method_params.values())[i], param_types[i]):
                    foundError = True
                    print(f"Error de tipo para el parámetro '{list(method_params.keys())[i]}'. Se esperaba el tipo '{list(method_params.values())[i]}' pero se obtuvo '{param_types[i]}'. (línea {expr.start.line})")
            if foundError: return "Error"
            return self.classes[called_class].methods[method_name].return_type
        elif expr.getChildCount() == 5 and expr.getChild(0).getSymbol().type == YAPLParser.WHILE: # While
            conditional_type = self.get_expr_type(expr.getChild(1))
            if conditional_type not in ["Bool", "Int"]:
                print(f"Se esperaba tipo Bool pero se obtuvo tipo {conditional_type} (línea {expr.start.line})")
                return "Error"
            if self.get_expr_type(expr.getChild(3)) == "Error":
                return "Error"
            return "Object"
        elif expr.getChildCount() >= 3 and expr.getChild(1).getText() == "(": # method call
            method_name = expr.getChild(0).getText()
            if method_name not in self.classes[self.current_class].methods:
                print(f"El método {method_name} no ha sido declarado. (línea {expr.start.line})")
                return "Error"
            param_types = [self.get_expr_type(param) for param in expr.expr()]
            method_params = self.classes[self.current_class].methods[method_name].params
            method_param_num = len(method_params)
            param_num = len(param_types)
            if param_num != method_param_num:
                print(f"En la llamada del método {method_name} se esperaban {method_param_num} parámetros pero se obtuvieron {param_num}. (línea {expr.start.line})")
                return "Error"
            foundError = False
            for i in range(param_num):
                if not self.check_casting(list(method_params.values())[i], param_types[i]):
                    foundError = True
                    print(f"Error de tipo para el parámetro '{list(method_params.keys())[i]}'. Se esperaba el tipo '{list(method_params.values())[i]}' pero se obtuvo '{param_types[i]}'. (línea {expr.start.line})")
            if foundError: return "Error"
            return self.classes[self.current_class].methods[method_name].return_type
        elif expr.getChildCount() == 3 and expr.getChild(1).getText() == "<-": # assign
            return self.visitAssign(expr)
        elif expr.getChildCount() == 3 and expr.getChild(0).getText() == "(": # parentheses
            return self.get_expr_type(expr.getChild(1))
        elif expr.getChildCount() == 3 and expr.getChild(1).getText() in ['+', '-', '*', '/']: # arith operations
            left_type = self.get_expr_type(expr.getChild(0))
            right_type = self.get_expr_type(expr.getChild(2))
            if left_type == 'Int' and right_type == 'Int':
                return 'Int'
            print(f'Error de tipos de operandos para {expr.getChild(1).getText()}: "{left_type}" y "{right_type}" (línea {expr.start.line})')
            return "Error"
        elif expr.getChildCount() == 3 and expr.getChild(1).getText() in ['<', '<=', '=']: # comparisons
            left_type = self.get_expr_type(expr.getChild(0))
            right_type = self.get_expr_type(expr.getChild(2))
            if (left_type == 'Int' and right_type == 'Int') or \
               (left_type == 'Bool' and right_type == 'Bool') or \
               (left_type == 'String' and right_type == 'String'):
                return 'Bool'
            print(f'Error de tipos de operandos para {expr.getChild(1).getText()}: "{left_type}" y "{right_type}" (línea {expr.start.line})')
            return "Error"
        elif expr.getChildCount() == 2 and expr.getChild(0).getText() in ['~', '-', 'not']: # unary operators
            expr_type = self.get_expr_type(expr.getChild(1))
            if expr_type == 'Int' and expr.getChild(0).getText() != 'not':
                return 'Int'
            elif expr_type == 'Bool' and expr.getChild(0).getText() in ['~', 'not']:
                return 'Bool'
            print(f'Error de tipo de operando para {expr.getChild(0).getText()}: "{expr_type}" (línea {expr.start.line})')
            return "Error"
        elif expr.getChildCount() == 2 and expr.getChild(0).getSymbol().type == YAPLParser.NEW: # new
            class_name = expr.getChild(1).getText()
            if class_name not in self.classes:
                print(f"La clase {class_name} no ha sido declarada. (línea {expr.start.line})")
                return "Error"
            return class_name
        elif expr.getChildCount() == 2 and expr.getChild(0).getSymbol().type == YAPLParser.ISVOID: # isvoid
            if self.get_expr_type(expr.getChild(1)) == "Error":
                return "Error"
            return "Bool"
        elif expr.getChildCount() == 1: # single child
            if isinstance(expr.getChild(0), YAPLParser.IdContext): # id
                if self.classes[self.current_class].has_attribute(self.current_method, self.active_lets, expr.getText()):
                    return self.classes[self.current_class].get_attribute_type(self.current_method, self.active_lets, expr.getText())
                print(f'El símbolo {expr.getText()} no ha sido definido (línea {expr.start.line})')
                return 'Error'
            elif expr.getChild(0).getSymbol().type == YAPLParser.INTEGER: # int
                return 'Int'
            elif expr.getChild(0).getSymbol().type == YAPLParser.STRING: # str
                return 'String'
            elif expr.getChild(0).getSymbol().type in [YAPLParser.TRUE, YAPLParser.FALSE]: #bool
                return 'Bool'
            elif expr.getText() == "self": # self
                return self.current_class
            return "Error"
        return 'Error'

    def visitAssign(self, ctx):
        id_name = ctx.id_()[0].getText()
        if not self.classes[self.current_class].has_attribute(self.current_method, self.active_lets, id_name):
            print(f'El símbolo {id_name} no ha sido definido (línea {ctx.start.line})')
            return 'Error'
        id_type = self.classes[self.current_class].get_attribute_type(self.current_method, self.active_lets, id_name)
        expr_type = self.get_expr_type(ctx.expr(0))

        if id_type != expr_type:
            print(f"Error de tipo se esperaba '{id_type}' pero se obtuvo '{expr_type}' (linea {ctx.start.line})")
            return "Error"
        return id_type

    def visitExprWithTwoChildren(self, ctx):
        left_type = self.visit(ctx.expr(0))  # visita el hijo izquierdo
        right_type = self.visit(ctx.expr(1))  # visita el hijo derecho
        if left_type != right_type or left_type != 'Int':
            print(f"Error de tipo: se esperaba 'Int' pero se obtuvo '{left_type}' y '{right_type}'")
        return 'Int'  # asume que la operación fue exitosa y devuelve 'Int'


    def visitExprWithNot(self, ctx):
        expr_type = self.get_expr_type(ctx.expr(0))
        if expr_type != 'Bool':
            print(f"Error de tipo: se esperaba 'Bool' pero se obtuvo '{expr_type}'")

    def visitExprWithAdd(self, ctx):
        left_type = self.get_expr_type(ctx.expr(0))
        right_type = self.get_expr_type(ctx.expr(1))
        if left_type == 'Int' and right_type == 'Int':
            return 'Int'
        else:
            print(f"Error de tipo: no se puede sumar '{left_type}' y '{right_type}'")
            return None



    def visitExprInFunction(self, ctx):
        function_name = ctx.id_().getText()
        function_type = self.classes[self.current_class].methods[function_name].return_type
        if function_type is None:
            print(f"Error: función '{function_name}' no definida")
            return
        if len(ctx.expr()) != len(function_type) - 1:
            print(f"Error: número incorrecto de argumentos para la función '{function_name}'")
        else:
            for expected_arg_type, actual_arg_expr in zip(function_type[1:], ctx.expr()):
                actual_arg_type = self.get_expr_type(actual_arg_expr)
                if expected_arg_type != actual_arg_type:
                    print(f"Error de tipo: se esperaba '{expected_arg_type}' pero se obtuvo '{actual_arg_type}' para el argumento de la función '{function_name}'")


    def visitExpr(self, ctx):
        if ctx.id_() and ctx.expr():
           self.visitAssign(ctx)
        elif ctx.expr() and len(ctx.expr()) == 2:
            self.visitExprWithTwoChildren(ctx)
        elif ctx.NOT():
            self.visitExprWithNot(ctx)
        elif ctx.getChild(0).getText() == '{':
            for expre in ctx.expr():
                self.visitExpr(expre)
        else:
            # Llama a la visita de los hijos directamente sin visitChildren
            result = []
            for child in ctx.getChildren():
                if isinstance(child, YAPLParser.ExprContext):
                    childResult = self.visitExpr(child)
                    if childResult is not None:
                        result.append(childResult)
            return result




    def verify_main_class(self):
        # Verificar que existe una clase llamada 'Main'
        if 'Main' not in self.classes:
            print("Error: La clase 'Main' no está definida.")
            return

        # Verificar que la clase 'Main' tiene un método llamado 'main'
        main_class_methods = self.classes['Main'].methods
        if 'main' not in main_class_methods:
            print("Error: La clase 'Main' no tiene un método 'main'.")
            return

        # Verificar que el tipo de retorno del método 'main' es 'Int'
        main_method_type = main_class_methods['main'].return_type
        if main_method_type != 'Int':
            print(f"Error: El método 'main' en la clase 'Main' tiene un tipo de retorno incorrecto: '{main_method_type}'. Se esperaba 'Int'.")
            return

        print("La clase 'Main' es válida.")


    def verify_inheritance_rules(self):
        def check_recursive_inheritance(start_class):
            visited = set()
            current_class = start_class
            while current_class in self.inheritance_info:
                if current_class in visited:
                    print(f"Error: Herencia recursiva detectada con la clase '{current_class}'.")
                    return True
                visited.add(current_class)
                current_class = self.inheritance_info[current_class]
            return False

        #print(f"Reglas de herencia: {self.inheritance_info}")
        #print(f"Tabla de clases: {self.classes}")

        # Verificar que la clase Main no hereda de ninguna otra clase.
        if self.inheritance_info.get('Main'):
            print("Error: La clase 'Main' no puede heredar de ninguna otra clase.")
            return

        # Verificar que las clases de tipos básicos no son superclases.
        basic_types = ['Int', 'String', 'Bool']
        for basic_type in basic_types:
            if basic_type in self.inheritance_info.values():
                print(f"Error: La clase '{basic_type}' no puede ser una superclase.")
                return

        # Verificar herencia recursiva.
        for cls in self.inheritance_info:
            if check_recursive_inheritance(cls):
                return

        print("Las reglas de herencia son válidas.")

    def check_default_values(self, variable_name, variable_type):
        default_values = {
            'Int': 0,
            'String': "",
            'Bool': 'false'
        }

        # Si la variable no ha sido inicializada, asignarle su valor por defecto
        if variable_name not in self.symbol_table[-1]:
            default_value = default_values.get(variable_type)
            if default_value is not None:
                self.symbol_table[-1][variable_name] = default_value
                print(f"'{variable_name}' ha sido inicializada con valor por defecto: {default_value}")
            else:
                print(f"Tipo desconocido '{variable_type}' para la variable '{variable_name}'. No se pudo inicializar con un valor por defecto.")


    def check_casting(self, expr_type, expected_type):
        if expr_type == expected_type:
            return True

        if expr_type == 'Int' and expected_type == 'Bool':
            # Int a Bool: 0 es False, cualquier valor positivo es True.
            return True
        
        if expr_type == 'Bool' and expected_type == 'Int':
            # Bool a Int: False es 0, True es 1.
            return True

        return False



class MyListener(YAPLListener, ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        print(f"Error de sintaxis en la línea {line}, columna {column}: {msg}")

    def visitErrorNode(self, node):
        print(f"Error: nodo no reconocido '{node.getText()}'")

def visualize_tree(node, dot):
    if isinstance(node, TerminalNode):
        dot.node(str(id(node)), str(node.getSymbol().text))
    else:
        rule_name = YAPLParser.ruleNames[node.getRuleContext().getRuleIndex()]
        dot.node(str(id(node)), rule_name)
        for i in range(node.getChildCount()):
            child = node.getChild(i)
            visualize_tree(child, dot)
            dot.edge(str(id(node)), str(id(child)))

def main(argv):
    if len(argv) < 2:
        print("Ingrese el programa yapl.")
        return
    input_stream = FileStream(argv[1], encoding='utf-8')
    lexer = YAPLLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = YAPLParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(MyListener())

    tree = parser.source()

    visitor = TypeCheckingVisitor()
    visitor.visit(tree)
    visitor.verify_main_class()
    visitor.verify_inheritance_rules()

    if parser.getNumberOfSyntaxErrors() == 0:
        # Generar representación gráfica
        dot = Digraph(comment='Abstract Syntax Tree')
        visualize_tree(tree, dot)
        #dot.render('tree', format='png', view=True)

        # Generar representación textual
        textual_representation = Trees.toStringTree(tree, None, parser)
        #print(textual_representation)
        print("Code compiled successfully")
    else:
        print("Se encontraron errores durante el análisis. No se generará ningún árbol.")

if __name__ == '__main__':
    main(sys.argv)

