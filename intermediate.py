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
        print(f"Processing genCode for: {ctx.getText()}")
            
        # Method Calls
        if ctx.getChildCount() >= 4 and ctx.getChild(1).getText() == '.':
                if len(ctx.id_()) > 1:
                    method_name = ctx.id_()[1].getText()  
                else:
                    method_name = ctx.id_()[0].getText()
                instance = self.genCode(ctx.getChild(0))
                args = [self.genCode(expr) for expr in ctx.expr()]
                for arg in args:
                    self.code.addInstruction('param', arg)
                self.code.addInstruction('call', method_name, instance)
                
        # Conditionals
        elif ctx.IF():
                condition = self.genCode(ctx.expr(0))
                then_code = self.genCode(ctx.expr(1))
                else_code = self.genCode(ctx.expr(2))
                self.code.addInstruction('if', condition, then_code, else_code)
                
        # Loops
        elif ctx.WHILE():
                condition = self.genCode(ctx.expr(0))
                loop_code = self.genCode(ctx.expr(1))
                self.code.addInstruction('while', condition, loop_code)
                
        # Code Blocks
        elif ctx.getChild(0).getText() == '{':
                for child_expr in ctx.expr():
                    return self.genCode(child_expr)
                    
        # New Object Creation
        elif ctx.NEW():
                type_name = ctx.TYPE_ID().getText()
                result = self.new_temp()
                self.code.addInstruction('new', type_name, result=result)
                return result
                
        # Unary Operations
        elif ctx.getChildCount() == 2:
                if ctx.getChild(0).getText() in ['ISVOID', 'NOT', '-', '~']:
                    op = ctx.getChild(0).getText()
                    operand = self.genCode(ctx.getChild(1))
                    result = self.new_temp()
                    self.code.addInstruction(op, operand, result=result)
                    return result
                    
        # Let Assignments
        elif ctx.getChild(0).getText() == 'let':
                assignments = [(id_.getText(), type_id.getText(), self.genCode(expr) if expr else None) 
                            for id_, type_id, expr in zip(ctx.id_(), ctx.TYPE_ID(), ctx.expr())]
                for var_name, type_name, value in assignments:
                    self.code.addInstruction('let', var_name, type_name, value)
                body = self.genCode(ctx.expr(-1))
                return body       

        # Asignaciones
        elif ctx.getChildCount() == 3 and ctx.getChild(1).getText() == "<-":
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


        return None

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
