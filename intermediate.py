from antlr4 import *
from antlr.YAPLParser import YAPLParser
from antlr.YAPLVisitor import YAPLVisitor
from lib import *

class IntermediateCodeVisitor(YAPLVisitor): 
    def __init__(self, typechecker):
        self.code = IntermediateCode()
        self.temp_manager = TemporalManager()
        self.current_class = None
        self.current_method = None
        self.classes = {}
        self.typechecker = typechecker
        self.inheritance_info = self.typechecker.inheritance_info
        self.active_lets = []
        self.last_let = 0
        

    def getExtData(self):
        data = {
            "current_class": self.current_class,
            "current_method": self.current_method,
            "active_lets": self.active_lets
        }
        return data

    def getCode(self):
        return self.code
    
    def getPointer(self):
        return self.temp_manager.get_pointer()

    def setTable(self, table):
        self.classes = table
        for clas in list(self.classes.keys()):
            if clas in ['Object', 'IO', 'Int', 'String', 'Bool']:
                continue
            self.code.addInstruction("reserve", clas, self.classes[clas].size)
        self.code.addInstruction("reserve", "Object", 0)
        # t1 = self.new_temp()
        # self.code.addInstruction("new", "Main", result=t1)
        # self.code.addInstruction("call", "Main_Init", 0, result=t1)
        # t2 = self.new_temp()
        # self.code.addInstruction("call", "Main_main", "0", result=t2)

    def new_temp(self):
        return self.temp_manager.get_new_temporal()
    
    def free_temp(self, temp):
        self.temp_manager.free_temporal(temp)
    
    def visitClass_prod(self, ctx:YAPLParser.Class_prodContext):
        self.current_class = ctx.TYPE_ID(0).getText()
        methods = []
        attributes = []
        features = ctx.feature()
        for feature in features:
            if feature.getChild(1).getText() == "(":
                methods.append(feature)
            else:
                attributes.append(feature)
        init_label = self.code.new_label(f"{self.current_class}_Init")
        self.code.set_label(init_label)
        for attribute in attributes:
            self.visitAttribute(attribute)
        self.code.addInstruction("return")
        for method in methods:
            self.visitMethod(method)
        self.current_class = None

    def visitMethod(self, ctx:YAPLParser.FeatureContext):
        self.temp_manager.reset_temps()
        self.current_method = ctx.id_().getText()
        l = self.code.new_label(f"{self.current_class}_{self.current_method}")
        self.code.set_label(l)
        res = self.genCode(ctx.expr())
        if self.current_class == "Main" and self.current_method == "main":
            self.code.addInstruction("HALT")
        self.code.addInstruction("return", res)
        self.free_temp(res)
        self.current_method = None

    def visitAttribute(self, ctx:YAPLParser.FeatureContext):
        attribute, _ = self.classes[self.current_class].get_attribute(None, None, ctx.getChild(0).getText())
        offset = attribute.offset
        left_var = f"IP[{offset}]"
        #att_name = f"{self.current_class}.{ctx.getChild(0).getText()}"
        if ctx.expr():
            code = self.genCode(ctx.expr())
            self.code.addInstruction("=", code, result=left_var)
        else:
            att_type = self.classes[self.current_class].get_attribute_type(self.current_method, self.active_lets, ctx.getChild(0).getText())
            if att_type in ["Int", "Bool"]:
                self.code.addInstruction("=", "0", result=left_var)
            elif att_type == "String":
                self.code.addInstruction("=", '""', result=left_var)


    def visitChildren(self, node):
        result = None
        for child in node.getChildren():
            result = child.accept(self)
        return result

    def genCode(self, ctx: YAPLParser.ExprContext):

        # Asignaciones
        if ctx.getChildCount() == 3 and ctx.getChild(1).getText() == "<-":
            attribute, att_scope = self.classes[self.current_class].get_attribute(self.current_method, self.active_lets, ctx.id_()[0].getText())
            offset = attribute.offset
            if att_scope == "global":
                left_var = f"IP[{offset}]"
            else:
                left_var = f"SP[{offset}]"
            right_val = self.genCode(ctx.expr(0))
            self.code.addInstruction('=', right_val, result=left_var)
            self.free_temp(right_val)
            return left_var

        # Operaciones binarias (+, -, *, /)
        elif ctx.getChildCount() == 3 and ctx.getChild(1).getText() in ['+', '-', '*', '/']:
            left_expr = self.genCode(ctx.getChild(0))
            op = ctx.getChild(1).getText()
            right_expr = self.genCode(ctx.getChild(2))
            result = self.new_temp()
            self.code.addInstruction(op, left_expr, right_expr, result)
            self.free_temp(left_expr)
            self.free_temp(right_expr)
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
            self.free_temp(left_expr)
            self.free_temp(right_expr)
            return result

        # Literales
        elif ctx.getChildCount() == 1:
            child = ctx.getChild(0)
            if isinstance(child, YAPLParser.IdContext):
                attribute, att_scope = self.classes[self.current_class].get_attribute(self.current_method, self.active_lets, ctx.getText())
                offset = attribute.offset
                if att_scope == "global":
                    left_var = f"IP[{offset}]"
                else:
                    left_var = f"SP[{offset}]"
                return left_var
            elif child.getSymbol().type == YAPLParser.INTEGER:
                return child.getText()
            elif child.getSymbol().type == YAPLParser.STRING:
                #TODO
                return child.getText()
            elif child.getSymbol().type == YAPLParser.TRUE:
                return "1"
            elif child.getSymbol().type == YAPLParser. FALSE:
                return "0"
            elif ctx.getText() == "self":
                return "IP"

        # LLamadas de función y método
        elif ctx.getChildCount() >= 5 and (ctx.getChild(1).getText() == "." or ctx.getChild(3).getText() == "."):
            instance = self.genCode(ctx.getChild(0))
            self.code.addInstruction("loadIP", instance)
            if ctx.getChild(1).getText() == "@":
                className = ctx.getChild(2).getText()
                methodName = ctx.getChild(4).getText()
            else:
                extData = self.getExtData()
                className = self.typechecker.get_expr_type(ctx.expr(0), extData)
                methodName = ctx.getChild(2).getText()
            method_params = [self.genCode(expr) for expr in ctx.expr()[1:]]
            pre_call_temporals = self.temp_manager.get_used_temporals()
            for temporal in pre_call_temporals:
                self.code.addInstruction('savetemporal', temporal)
            self.code.addInstruction('savera')
            param_num = len(method_params)
            self.code.addInstruction('paramnum', param_num)
            for param in method_params:
                self.code.addInstruction('param', param)
            result = self.new_temp()
            called_class = className
            while True:
                if methodName in self.classes[called_class].inherited_methods:
                    if called_class not in self.inheritance_info:
                        called_class = className
                        break
                    else:
                        called_class = self.inheritance_info[called_class]
                else:
                    break
            if methodName == "abort": called_class = "Object"
            self.code.addInstruction('call', f"{called_class}_{methodName}", param_num, result)
            for temporal in pre_call_temporals[::-1]:
                self.code.addInstruction('restoretemporal', temporal)
            self.code.addInstruction("restoreIP")
            self.free_temp(instance)
            return result
        
        elif ctx.getChildCount() >= 3 and ctx.getChild(1).getText() == "(":
            method_name = ctx.getChild(0).getText()
            method_params = [self.genCode(expr) for expr in ctx.expr()]
            pre_call_temporals = self.temp_manager.get_used_temporals()
            for temporal in pre_call_temporals:
                self.code.addInstruction('savetemporal', temporal)
            self.code.addInstruction('savera')
            param_num = len(method_params)
            self.code.addInstruction('paramnum', param_num)
            for param in method_params:
                self.code.addInstruction('param', param)
            result = self.new_temp()
            called_class = self.current_class
            while True:
                if method_name in self.classes[called_class].inherited_methods:
                    if called_class not in self.inheritance_info:
                        called_class = self.current_class
                        break
                    else:
                        called_class = self.inheritance_info[called_class]
                else:
                    break
            if method_name == "abort": called_class = "Object"
            self.code.addInstruction('call', f"{called_class}_{method_name}", param_num, result)
            for temporal in pre_call_temporals[::-1]:
                self.code.addInstruction('restoretemporal', temporal)
            return result

        # Condicionales
        elif ctx.getChildCount() == 7 and ctx.getChild(0).getSymbol().type == YAPLParser.IF:
            conditional = self.genCode(ctx.getChild(1))
            label_else = self.code.new_label()
            label_next = self.code.new_label()
            self.code.addInstruction("ifFalse", conditional, result=label_else.name)
            self.free_temp(conditional)
            result = self.new_temp()

            then_code = self.genCode(ctx.getChild(3))
            self.code.addInstruction("=", then_code, result=result)
            self.code.addInstruction("goto", result=label_next.name)
            self.free_temp(then_code)

            self.code.set_label(label_else)
            else_code = self.genCode(ctx.getChild(5))
            self.code.addInstruction("=", else_code, result=result)
            self.free_temp(else_code)

            self.code.set_label(label_next)
            return result

        # Ciclos
        elif ctx.getChildCount() == 5 and ctx.getChild(0).getSymbol().type == YAPLParser.WHILE: # While
            label_begin = self.code.new_label()
            self.code.set_label(label_begin)
            conditional = self.genCode(ctx.getChild(1))
            label_next = self.code.new_label()
            self.code.addInstruction("ifFalse", conditional, result=label_next.name)
            result = self.genCode(ctx.getChild(3))
            self.code.addInstruction("goto", result=label_begin.name)
            self.code.set_label(label_next)
            self.free_temp(conditional)
            return result
            
        # Bloques
        elif ctx.getChild(0).getText() == '{':
            childCount = len(ctx.expr())
            for i in range(childCount-1):
                u_temp = self.genCode(ctx.expr(i))
                self.free_temp(u_temp)
            return self.genCode(ctx.expr(childCount-1))

        # Verificación de tipo vacío
        elif ctx.getChildCount() == 2 and ctx.getChild(0).getSymbol().type == YAPLParser.ISVOID:
            result = self.new_temp()
            contained = self.genCode(ctx.getChild(1))
            self.code.addInstruction("param", contained)
            self.code.addInstruction("call", "isvoid", 1, result)
            return result
        
        # Operaciones unarias
        elif ctx.getChildCount() == 2 and ctx.getChild(0).getText() in ['~', '-', 'not']:
            result = self.new_temp()
            operand = self.genCode(ctx.expr(0))
            op = ctx.getChild(0).getText()
            if op == '~':
                self.code.addInstruction("not", operand, result=result)
            elif op == '-':
                self.code.addInstruction("minus", operand, result=result)
            elif op == 'not':
                self.code.addInstruction("lnot", operand, result=result)
            return result
        
        elif ctx.getChildCount() == 3 and ctx.getChild(0).getText() == "(": # parentheses
            return self.genCode(ctx.getChild(1))
        
        elif ctx.getChildCount() >= 6 and ctx.getChild(0).getText() == "let": # let
            self.last_let += 1
            let_name = f"let{self.last_let}"

            att_names = []
            att_types = []
            curr_check = 1
            while True:
                att_name = ctx.getChild(curr_check).getText()
                att_type = ctx.getChild(curr_check + 2).getText()
                att_names.append(att_name)
                att_types.append(att_type)
                if ctx.getChild(curr_check + 3).getText() == "<-":
                    assign = self.genCode(ctx.getChild(curr_check + 4))
                    self.code.addInstruction("=", assign, result=f"{self.current_class}.{att_name}")
                    curr_check += 6
                else:
                    if att_type in ["Int", "Bool"]:
                        self.code.addInstruction("=", "0", result=f"{self.current_class}.{att_name}")
                    elif att_type == "String":
                        self.code.addInstruction("=", '""', result=f"{self.current_class}.{att_name}")
                    curr_check += 4
                if ctx.getChild(curr_check - 1).getText() != ",":
                    break
            self.active_lets.append(let_name)
            result = self.genCode(ctx.expr()[-1])
            self.active_lets.pop()
            return result

        elif ctx.getChildCount() == 2 and ctx.getChild(0).getSymbol().type == YAPLParser.NEW: # new
            pointer = self.new_temp()
            self.code.addInstruction("new", ctx.TYPE_ID(0).getText(), result=pointer)
            self.code.addInstruction("call", f"{ctx.TYPE_ID(0).getText()}_Init", 0, result="T0")
            return pointer

        return None
