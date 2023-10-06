from antlr4 import *
from antlr.YAPLParser import YAPLParser
from antlr.YAPLVisitor import YAPLVisitor
from lib import *
import copy

class IntermediateCodeVisitor(YAPLVisitor):
    def __init__(self, type_checker):
        self.code = []
        self.temp_manager = TemporalManager()
        self.current_class = None
        self.current_method = None
        self.type_checker = type_checker

    def new_temp(self):
        return self.temp_manager.get_new_temporal()

    def visitExpr(self, ctx: YAPLParser.ExprContext):

        # Asignaciones
        if ctx.getChildCount() == 3 and ctx.getChild(1).getText() == "<-":
            left_var = ctx.id_()[0].getText()
            right_expr = self.visit(ctx.expr(0))
            self.code.append(('ASSIGN', right_expr, None, left_var))
            return left_var


        # Operaciones binarias (+, -, *, /)
        elif ctx.getChildCount() == 3 and ctx.getChild(1).getText() in ['+', '-', '*', '/']:
            left_expr = self.visit(ctx.getChild(0))
            op = ctx.getChild(1).getText()
            right_expr = self.visit(ctx.getChild(2))
            result = self.new_temp()
            if op == '+':
                self.code.append(('ADD', left_expr, right_expr, result))
            elif op == '-':
                self.code.append(('SUB', left_expr, right_expr, result))
            elif op == '*':
                self.code.append(('MUL', left_expr, right_expr, result))
            elif op == '/':
                self.code.append(('DIV', left_expr, right_expr, result))
            return result

        # Operaciones binarias (comparaciones: <, <=, =)
        elif ctx.getChildCount() == 3 and ctx.getChild(1).getText() in ['<', '<=', '=']:
            left_expr = self.visit(ctx.getChild(0))
            op = ctx.getChild(1).getText()
            right_expr = self.visit(ctx.getChild(2))
            result = self.new_temp()
            if op == '<':
                self.code.append(('LT', left_expr, right_expr, result))
            elif op == '<=':
                self.code.append(('LTE', left_expr, right_expr, result))
            elif op == '=':
                self.code.append(('EQUAL', left_expr, right_expr, result))
            return result

        # Literales
        elif ctx.getChildCount() == 1:
            child = ctx.getChild(0)
            if isinstance(child, YAPLParser.INTEGER):
                return child.getText()
            elif isinstance(child, YAPLParser.STRING):
                return f'"{child.getText()}"'
            elif isinstance(child, YAPLParser.TRUE) or isinstance(child, YAPLParser.FALSE):
                return child.getText().lower()

        return None

    def visitChildren(self, node):
        result = None
        for child in node.getChildren():
            result = child.accept(self)
        return result

    def visitClass_prod(self, ctx:YAPLParser.Class_prodContext):
        pass

    def visitFeature(self, ctx:YAPLParser.FeatureContext):
        pass
