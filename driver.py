import sys
from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener
from YAPLLexer import YAPLLexer
from YAPLParser import YAPLParser
from YAPLListener import YAPLListener
from graphviz import Digraph
from antlr4.tree.Trees import Trees
from YAPLVisitor import YAPLVisitor

class TypeCheckingVisitor(YAPLVisitor):
    def __init__(self):
        self.symbol_table = [{}]  # Una lista de diccionarios para manejar los ámbitos
        self.current_class = None
        self.classes = {}

    def visitClass_prod(self, ctx:YAPLParser.Class_prodContext):
        self.current_class = ctx.TYPE_ID(0).getText()
        self.classes[self.current_class] = {}  
        self.symbol_table.append({})  # crea un nuevo ámbito para la clase
        self.visitChildren(ctx)
        self.current_class = None
        self.symbol_table.pop()  # sale del ámbito de la clase al finalizar
        # print(f"Tabla de símbolos después de visitar la clase: {self.symbol_table}")
        # print(f"Tabla de clases después de visitar la clase: {self.classes}")

    def visitFeature(self, ctx:YAPLParser.FeatureContext):
        if ctx.id_() and ctx.TYPE_ID():
            id_name = ctx.id_().getText()
            id_type = ctx.TYPE_ID().getText()
            if ctx.formal():
                formal_types = [formal.TYPE_ID().getText() for formal in ctx.formal()]
                id_type = (id_type, *formal_types)
            self.symbol_table[-1][id_name] = id_type
            self.visitChildren(ctx)
            if self.current_class:
                self.classes[self.current_class][id_name] = id_type
            # print(f"Tabla de símbolos después de visitar la característica: {self.symbol_table}")
            # print(f"Tabla de clases después de visitar la característica: {self.classes}")


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
        
    # def visitExprWithDot(self, ctx):
    #     function_name = ctx.id_().getText()
    #     function_type = self.get_expr_type(ctx.expr(0))
    #     expected_function_type = self.classes.get(function_type, {}).get(function_name)
    #     if expected_function_type is None:
    #         print(f"Error de tipo: función '{function_name}' no definida en la clase '{function_type}'")
    #     elif len(ctx.expr()) - 1 != len(ctx.expr_list().expr()):
    #         print(f"Error de tipo: número incorrecto de argumentos para la función '{function_name}' en la clase '{function_type}'")
    #     else:
    #         for expected_arg_type, actual_arg_expr in zip(expected_function_type[1:], ctx.expr_list().expr()):
    #             actual_arg_type = self.get_expr_type(actual_arg_expr)
    #             if expected_arg_type != actual_arg_type:
    #                 print(f"Error de tipo: se esperaba '{expected_arg_type}' pero se obtuvo '{actual_arg_type}' para el argumento de la función '{function_name}' en la clase '{function_type}'")

    def visitExprWithId(self, ctx):
        id_name = ctx.id_()[0].getText()  
        id_type = self.symbol_table[-1].get(id_name)
        expr_type = self.get_expr_type(ctx.expr(0))

        if id_type != expr_type:
            print(f"Error de tipo se esperaba '{id_type}' pero se obtuvo '{expr_type}' (linea {ctx.start.line})")

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
        function_type = self.symbol_table[-1].get(function_name)
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
           self.visitExprWithId(ctx)
        elif ctx.expr() and len(ctx.expr()) == 2:
            self.visitExprWithTwoChildren(ctx)
        elif ctx.NOT():
            self.visitExprWithNot(ctx)
        elif ctx.getChild(0).getText() == '{':
            for expre in ctx.expr():
                self.visitExpr(expre)
        elif ctx.PLUS():  
            return self.visitExprWithAdd(ctx)
        else:
            # Llama a la visita de los hijos directamente sin visitChildren
            result = []
            for child in ctx.getChildren():
                if isinstance(child, YAPLParser.ExprContext):
                    childResult = self.visitExpr(child)
                    if childResult is not None:
                        result.append(childResult)
            return result


    def get_expr_type(self, expr):
        if expr.getChildCount() == 3 and expr.getChild(1).getText() in ['+', '-', '*', '/']:
            left_type = self.get_expr_type(expr.getChild(0))
            right_type = self.get_expr_type(expr.getChild(2))
            if left_type == 'Int' and right_type == 'Int':
                return 'Int'
            print(f'Error de tipos de operandos para {expr.getChild(1).getText()}: "{left_type}" y "{right_type}" (línea {expr.start.line})')
        elif expr.getChildCount() == 3 and expr.getChild(1).getText() in ['<', '<=', '=']:
            left_type = self.get_expr_type(expr.getChild(0))
            right_type = self.get_expr_type(expr.getChild(2))
            if (left_type == 'Int' and right_type == 'Int') or \
               (left_type == 'Bool' and right_type == 'Bool') or \
               (left_type == 'String' and right_type == 'String'):
                return 'Bool'
            print(f'Error de tipos de operandos para {expr.getChild(1).getText()}: "{left_type}" y "{right_type}" (línea {expr.start.line})')
        elif expr.getChildCount() == 2 and expr.getChild(0).getText() == '~':
            expr_type = self.get_expr_type(expr.getChild(1))
            if expr_type == 'Int':
                return 'Int'
            elif expr_type == 'Bool':
                return 'Bool'
            else:
                print(f'Error de tipo de operando para ~: "{expr_type}" (línea {expr.start.line})')
        elif expr.getChildCount() == 2 and expr.getChild(0).getText() == 'not':
            expr_type = self.get_expr_type(expr.getChild(1))
            if expr_type == 'Bool':
                return 'Bool'
            else:
                print(f'Error de tipo de operando para "not": "{expr_type}" (línea {expr.start.line})')
        elif expr.getChildCount() == 1 and isinstance(expr.getChild(0), YAPLParser.IdContext):
            if expr.getText() in self.symbol_table[-1]:
                return self.symbol_table[-1].get(expr.getText())
            else:
                print(f'El símbolo {expr.getText()} no ha sido definido (línea {expr.start.line})')
                return 'Error'
        for child in expr.getChildren():
            if isinstance(child, TerminalNode):
                if child.getSymbol().type == YAPLParser.INTEGER:
                    return 'Int'
                elif child.getSymbol().type == YAPLParser.STRING:
                    return 'String'
                elif child.getSymbol().type in [YAPLParser.TRUE, YAPLParser.FALSE]:
                    return 'Bool'
                elif child.getSymbol().type == YAPLParser.OBJECT_ID:
                    return self.visitId(child)
        if expr.id_() and expr.expr():
            object_type = self.get_expr_type(expr.expr()[0])  
            method_name = expr.id_().getText()
            if object_type in self.classes:
                method_type = self.classes[object_type].get(method_name)
                if method_type:
                    return method_type
        return 'Error'






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

    if parser.getNumberOfSyntaxErrors() == 0:
        # Generar representación gráfica
        dot = Digraph(comment='Abstract Syntax Tree')
        visualize_tree(tree, dot)
        dot.render('tree', format='png', view=True)

        # Generar representación textual
        textual_representation = Trees.toStringTree(tree, None, parser)
        print(textual_representation)
    else:
        print("Se encontraron errores durante el análisis. No se generará ningún árbol.")

if __name__ == '__main__':
    main(sys.argv)

