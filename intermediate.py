from antlr4 import *
from antlr.YAPLParser import YAPLParser
from antlr.YAPLVisitor import YAPLVisitor
from lib import *

class IntermediateCodeVisitor(YAPLVisitor): 
    def __init__(self):
        self.code = IntermediateCode()
        self.temp_manager = TemporalManager()
        self.current_class = None
        self.current_method = None
        self.classes = {}

    def getCode(self):
        return self.code

    def setTable(self, table):
        self.classes = table

    def new_temp(self):
        return self.temp_manager.get_new_temporal()
    
    def visitClass_prod(self, ctx:YAPLParser.Class_prodContext):
        self.current_class = ctx.TYPE_ID(0).getText()
        self.visitChildren(ctx)
        self.current_class = None

    def visitFeature(self, ctx:YAPLParser.FeatureContext):
        if ctx.getChild(1).getText() == "(": # Es un método
            self.current_method = ctx.id_().getText()
            # self.code.append(('METHOD_START', self.current_class, self.current_method))
            res =self.genCode(ctx.expr())
            print(f"res: {res}")
            # self.code.append(('METHOD_END', self.current_class, self.current_method))
            self.current_method = None
        else: # Es un atributo
            if ctx.expr():
                self.genCode(ctx.expr())

    def visitChildren(self, node):
        result = None
        for child in node.getChildren():
            result = child.accept(self)
        return result

    def genCode(self, ctx: YAPLParser.ExprContext):

        # Asignaciones
        if ctx.getChildCount() == 3 and ctx.getChild(1).getText() == "<-":
            left_var = ctx.id_()[0].getText()
            right_val = self.genCode(ctx.expr(0))
            self.code.addInstruction('=', right_val, result=left_var)
            return left_var


        # Operaciones binarias (+, -, *, /)
        elif ctx.getChildCount() == 3 and ctx.getChild(1).getText() in ['+', '-', '*', '/']:
            left_expr = self.genCode(ctx.getChild(0))
            op = ctx.getChild(1).getText()
            right_expr = self.genCode(ctx.getChild(2))
            result = self.new_temp()
            self.code.addInstruction(op, left_expr, right_expr, result)
            return result

        # Operaciones binarias (comparaciones: <, <=, =)
        elif ctx.getChildCount() == 3 and ctx.getChild(1).getText() in ['<', '<=', '=']:
            left_expr = self.genCode(ctx.getChild(0))
            op = ctx.getChild(1).getText()
            if op == '=':
                relop = 'eq'
            else:
                relop = op
            right_expr = self.genCode(ctx.getChild(2))
            result = self.new_temp()
            self.code.addInstruction(relop, left_expr, right_expr, result)
            return result

        # Literales
        elif ctx.getChildCount() == 1:
            child = ctx.getChild(0)
            if isinstance(child, YAPLParser.IdContext):
                return ctx.getText()
            elif child.getSymbol().type == YAPLParser.INTEGER:
                return child.getText()
            elif child.getSymbol().type == YAPLParser.STRING:
                #TODO
                return child.getText()
            elif child.getSymbol().type == YAPLParser.TRUE:
                return "1"
            elif child.getSymbol().type == YAPLParser. FALSE:
                return "0"

        # LLamadas de función y método
        # elif ctx.getChildCount() >= 3 and ctx.getChild(1).getText() == ".":
        #     method_name = ctx.getChild(2).getText()
        #     instance = self.visit(ctx.getChild(0))
        #     method_params = [self.visit(expr) for expr in ctx.expr()]
        #     result = self.new_temp()
        #     self.code.append(('METHOD_CALL', instance, method_name, method_params, result))
        #     return result
        
        # elif ctx.getChildCount() >= 3 and ctx.getChild(1).getText() == "(":
        #     method_name = ctx.getChild(0).getText()
        #     method_params = [self.visit(expr) for expr in ctx.expr()]
        #     result = self.new_temp()
        #     self.code.append(('FUNC_CALL', method_name, method_params, result))
        #     return result

        # Condicionales
        # elif ctx.IF():
        #     label_then = len(self.code) + 1
        #     self.code.append(('IF', self.visit(ctx.expr(0)), None, label_then))
        #     self.visit(ctx.expr(1))
        #     label_else = len(self.code) + 1
        #     self.code.append(('GOTO', None, None, label_else))
        #     self.visit(ctx.expr(2))
            
        # Ciclos
        # elif ctx.WHILE():
        #     label_begin = len(self.code)
        #     self.code.append(('IF', self.visit(ctx.expr(0)), None, label_begin))
        #     self.visit(ctx.expr(1))
        #     self.code.append(('GOTO', None, None, label_begin))
            
        # Bloques
        # elif ctx.getChild(0).getText() == '{':
        #     self.visitChildren(ctx)

        # Verificación de tipo vacío
        # elif ctx.ISVOID():
        #     result = self.new_temp()
        #     self.code.append(('ISVOID', self.visit(ctx.expr(0)), None, result))
        #     return result
        
        # Operaciones unarias
        # elif ctx.getChildCount() == 2 and ctx.getChild(0).getText() in ['~', '-', 'not']:
        #     result = self.new_temp()
        #     operand = self.visit(ctx.expr(0))
        #     op = ctx.getChild(0).getText()
        #     if op == '~':
        #         self.code.append(('NOT', operand, None, result))
        #     elif op == '-':
        #         self.code.append(('NEG', operand, None, result))
        #     elif op == 'not':
        #         self.code.append(('LOGICAL_NOT', operand, None, result))
        #     return result

        # Acceso a atributos y llamada a métodos
        # elif ctx.getChildCount() >= 5 and (ctx.getChild(1).getText() == "." or ctx.getChild(3).getText() == "."):
        #     obj = self.visit(ctx.expr(0))
        #     method_or_attr = ctx.id_().getText()
        #     result = self.new_temp()
        #     self.code.append(('ACCESS', obj, method_or_attr, result))
        #     return result

        return None
