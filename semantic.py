from antlr4 import *
from antlr.YAPLParser import YAPLParser
from antlr.YAPLVisitor import YAPLVisitor
from lib import *
import copy

class TypeCheckingVisitor(YAPLVisitor):
    def __init__(self):
        self.current_class = None
        self.current_method = None
        self.classes = {}
        self.inheritance_info = {}
        self.active_lets = []
        self.last_let = 0
        self.found_errors = False
        self.output = ""

        # Agregar las clases especiales
        self.classes['Object'] = ClassObj('Object')
        self.classes['Object'].add_method('abort', Method('Object', {}))
        self.classes['Object'].add_method('type_name', Method('String', {}))
        self.classes['Object'].add_method('copy', Method('SELF_TYPE', {}))
        
        self.classes['IO'] = ClassObj('IO')
        self.classes['IO'].inherit(self.classes['Object'])
        self.classes['IO'].add_method('in_int', Method('Int', {}))
        self.classes['IO'].add_method('in_string', Method('String', {}))
        self.classes['IO'].add_method('out_int', Method('SELF_TYPE', {'x': 'Int'}))
        self.classes['IO'].add_method('out_string', Method('SELF_TYPE', {'x': 'String'}))

        self.classes['Int'] = ClassObj('Int')
        self.classes['Int'].inherit(self.classes['Object'])

        self.classes['String'] = ClassObj('String')
        self.classes['String'].inherit(self.classes['Object'])
        self.classes['String'].add_method('length', Method('Int', {}))
        self.classes['String'].add_method('concat', Method('String', {'s': 'String'}))
        self.classes['String'].add_method('substr', Method('String', {'i': 'Int', 'l': 'Int'}))

        self.classes['Bool'] = ClassObj('Bool')
        self.classes['Bool'].inherit(self.classes['Object'])

        self.RESERVED_WORDS = {"class", "else", "fi", "if", "in", "inherits", "isvoid", "loop", "pool", "then", "while", "new", "not", "false", "true"}
        
    def log(self, out):
        self.output += out + '\n'
    
    def getTable(self):
        return copy.deepcopy(self.classes)

    def getOutput(self):
        return self.output
        
    def setClasses(self, source:YAPLParser.SourceContext):
        for class_ in source.class_prod():
            class_name = class_.getChild(1).getText()
            if class_name in self.classes:
                self.log(f"La clase {class_name} ya ha sido definida (línea {class_.start.line})")
                self.found_errors = True
                continue
            self.classes[class_name] = ClassObj(class_name)
            self.classes[class_name].inherit(self.classes['Object'])
            if class_.INHERITS():
                inherited_class = class_.TYPE_ID(1).getText()
                if inherited_class in self.classes:
                    self.classes[class_name].inherit(self.classes[inherited_class])
                    self.inheritance_info[class_name] = inherited_class
                else:
                    self.log(f"La clase {inherited_class} no ha sido definida (línea {class_.start.line})")
                    self.found_errors = True
            for feature in class_.feature():
                self.setFeature(feature, class_name)
    
    def methodInSuperclass(self, method_name, class_name) -> Method:
        current_class = class_name
        while True:
            if method_name in self.classes[current_class].methods:
                return self.classes[current_class].methods[method_name]
            if current_class in self.inheritance_info:
                current_class = self.inheritance_info[current_class]
            else:
                break
        return None


    def setFeature(self, feature:YAPLParser.FeatureContext, class_name):
        if feature.getChild(1).getText() == "(": # method
            method_name = feature.id_().getText()
            if method_name in self.RESERVED_WORDS:
                self.log(f"El nombre del método {method_name} es una palabra reservada (línea {feature.start.line})")
                self.found_errors = True
                return
            method_type = feature.TYPE_ID().getText()
            params = {}
            for param in feature.formal():
                param_type = param.TYPE_ID().getText()
                param_name = param.id_().getText()
                params[param_name] = param_type

            # Verifica si el metodo ya ha sido definido en la clase actual
            if method_name in self.classes[class_name].methods and not self.classes[class_name].is_inherited_method(method_name):
                self.log(f"El método {method_name} ya ha sido definido en la clase {class_name} (línea {feature.start.line})")
                self.found_errors = True
                return

            # Verifica si el metodo ya ha sido definido en una superclase
            existing_method = self.methodInSuperclass(method_name, class_name)
            if existing_method:
                # Verifica si el tipo de retorno y los parametros coinciden
                if existing_method.return_type != method_type or existing_method.get_params() != params:
                    self.log(f"El método {method_name} ya ha sido definido en una superclase de {class_name} con un tipo de retorno o parámetros diferentes (línea {feature.start.line})")
                    self.found_errors = True
                    return
                self.classes[class_name].inherited_methods.discard(method_name)

            self.classes[class_name].add_method(method_name, Method(method_type, params))
        
        else: # attribute
            attribute_name = feature.id_().getText()
            if attribute_name in self.RESERVED_WORDS:
                self.log(f"El nombre del atributo {attribute_name} es una palabra reservada (línea {feature.start.line})")
                self.found_errors = True
                return
            attribute_type = feature.TYPE_ID().getText()
            if attribute_name in self.classes[class_name].attributes:
                self.log(f"El atributo {attribute_name} ya ha sido definido en la clase {class_name} (línea {feature.start.line})")
                self.found_errors = True
                return
            self.classes[class_name].add_attribute(attribute_name, attribute_type)


    def visitClass_prod(self, ctx:YAPLParser.Class_prodContext):
        self.current_class = ctx.TYPE_ID(0).getText()
        self.visitChildren(ctx)
        self.current_class = None


    def visitFeature(self, ctx:YAPLParser.FeatureContext):
        if ctx.getChild(1).getText() == "(": # method
            method_name = ctx.id_().getText()
            method_type = ctx.TYPE_ID().getText()
            self.current_method = method_name
            return_type = self.get_expr_type(ctx.expr())
            if not self.check_casting(return_type, method_type, self.current_class):
                self.log(f"Error en el tipo de retorno del método '{method_name}', se esperaba '{method_type}' pero se obtuvo '{return_type}'. (línea {ctx.start.line})")
                self.found_errors = True
            self.current_method = None

        else: # attribute
            attribute_name = ctx.id_().getText()
            attribute_type = ctx.TYPE_ID().getText()
            if ctx.expr():
                assigned_type = self.get_expr_type(ctx.expr())
                if not self.check_casting(assigned_type, attribute_type, self.current_class):
                    self.log(f"Error en asignación de valor para atributo '{attribute_name}', se esperaba '{attribute_type}' pero se obtuvo '{assigned_type}'. (línea {ctx.start.line})")
                    self.found_errors = True


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

    def get_expr_type(self, expr: YAPLParser.ExprContext, extdata=None):
        if extdata:
            self.current_class = extdata["current_class"]
            self.current_method = extdata["current_method"]
            self.active_lets = extdata["active_lets"]
        if expr.getChild(0).getText() == "{": #code block
            code_block_type = None
            for child in expr.expr():
                if code_block_type != "Error":
                    code_block_type = self.get_expr_type(child)
            return code_block_type
        elif expr.getChildCount() == 7 and expr.getChild(0).getSymbol().type == YAPLParser.IF: # If
            conditional_type = self.get_expr_type(expr.getChild(1))
            if conditional_type not in ["Bool", "Int"]:
                self.log(f"Se esperaba tipo Bool pero se obtuvo tipo {conditional_type} (línea {expr.start.line})")
                return "Error"
            then_type = self.get_expr_type(expr.getChild(3))
            else_type = self.get_expr_type(expr.getChild(5))

            # calculando el supertipo
            if then_type == else_type:
                return then_type
            elif then_type == "Object" or else_type == "Object":
                return "Object"
            elif then_type in self.inheritance_info and else_type in self.inheritance_info:
                if self.inheritance_info[then_type] == self.inheritance_info[else_type]:
                    return self.inheritance_info[then_type]
            elif then_type in self.inheritance_info:
                if self.inheritance_info[then_type] == else_type:
                    return else_type
            elif else_type in self.inheritance_info:
                if then_type == self.inheritance_info[else_type]:
                    return then_type
            return "Object"
        elif expr.getChildCount() >= 6 and expr.getChild(0).getText() == "let": # let
            self.last_let += 1
            let_name = f"let{self.last_let}"

            att_names = []
            att_types = []
            curr_check = 1
            while True:
                att_name = expr.getChild(curr_check).getText()
                if att_name in att_names or self.classes[self.current_class].has_attribute(self.current_method, self.active_lets, att_name):
                    self.log(f"Variable local '{att_name}' definida previamente (línea {expr.start.line})")
                    return "Error"
                att_type = expr.getChild(curr_check + 2).getText()
                att_names.append(att_name)
                att_types.append(att_type)
                if expr.getChild(curr_check + 3).getText() == "<-":
                    eval_type = self.get_expr_type(expr.getChild(curr_check + 4))
                    if not self.check_casting(eval_type, att_type, self.current_class):
                        self.log(f"Error de tipo se esperaba '{att_type}' pero se obtuvo '{eval_type}' (linea {expr.start.line})")
                        return "Error"
                    curr_check += 6
                else:
                    curr_check += 4
                if expr.getChild(curr_check - 1).getText() != ",":
                    break
            self.classes[self.current_class].methods[self.current_method].add_let(let_name, att_names, att_types)
            self.active_lets.append(let_name)
            let_type = self.get_expr_type(expr.expr()[-1])
            self.active_lets.pop()
            return let_type
        elif expr.getChildCount() >= 5 and (expr.getChild(1).getText() == "." or expr.getChild(3).getText() == "."): # class.method call
            class_type = self.get_expr_type(expr.getChild(0))
            if class_type not in self.classes:
                self.log(f"La clase {class_type} no ha sido declarada. (línea {expr.start.line})")
                return "Error"
            if expr.getChild(1).getText() == "@":
                target_class = expr.getChild(2).getText()
                child_class = class_type
                visited = [class_type]
                while True:
                    if child_class not in self.inheritance_info:
                        self.log(f"La clase {class_type} no hereda de {target_class}. (línea {expr.start.line})")
                        return "Error"
                    parent_class = self.inheritance_info[child_class]
                    if parent_class == target_class:
                        break
                    if parent_class in visited:
                        self.log(f"Error de heredación recursiva (línea {expr.start.line})")
                        return "Error"
                    child_class = parent_class

                method_name = expr.getChild(4).getText()
                called_class = target_class
            else:
                method_name = expr.getChild(2).getText()
                called_class = class_type
            if method_name not in self.classes[called_class].methods:
                self.log(f"El método {method_name} no ha sido declarado en la clase {called_class}. (línea {expr.start.line})")
                return "Error"
            param_types = [self.get_expr_type(param) for param in expr.expr()[1:]]
            method_params = self.classes[called_class].methods[method_name].get_params()
            method_param_num = len(method_params)
            param_num = len(param_types)
            if param_num != method_param_num:
                self.log(f"En la llamada del método {method_name} se esperaban {method_param_num} parámetros pero se obtuvieron {param_num}. (línea {expr.start.line})")
                return "Error"
            foundError = False
            for i in range(param_num):
                if not self.check_casting(list(method_params.values())[i], param_types[i], self.current_class):
                    foundError = True
                    self.log(f"Error de tipo para el parámetro '{list(method_params.keys())[i]}'. Se esperaba el tipo '{list(method_params.values())[i]}' pero se obtuvo '{param_types[i]}'. (línea {expr.start.line})")
            if foundError: return "Error"
            if self.classes[called_class].methods[method_name].return_type == "SELF_TYPE":
                return called_class
            return self.classes[called_class].methods[method_name].return_type
        elif expr.getChildCount() == 5 and expr.getChild(0).getSymbol().type == YAPLParser.WHILE: # While
            conditional_type = self.get_expr_type(expr.getChild(1))
            if conditional_type not in ["Bool", "Int"]:
                self.log(f"Se esperaba tipo Bool pero se obtuvo tipo {conditional_type} (línea {expr.start.line})")
                return "Error"
            if self.get_expr_type(expr.getChild(3)) == "Error":
                return "Error"
            return "Object"
        elif expr.getChildCount() >= 3 and expr.getChild(1).getText() == "(": # method call
            method_name = expr.getChild(0).getText()
            if method_name not in self.classes[self.current_class].methods:
                self.log(f"El método {method_name} no ha sido declarado. (línea {expr.start.line})")
                return "Error"
            param_types = [self.get_expr_type(param) for param in expr.expr()]
            method_params = self.classes[self.current_class].methods[method_name].get_params()
            method_param_num = len(method_params)
            param_num = len(param_types)
            if param_num != method_param_num:
                self.log(f"En la llamada del método {method_name} se esperaban {method_param_num} parámetros pero se obtuvieron {param_num}. (línea {expr.start.line})")
                return "Error"
            foundError = False
            for i in range(param_num):
                if not self.check_casting(list(method_params.values())[i], param_types[i], self.current_class):
                    foundError = True
                    self.log(f"Error de tipo para el parámetro '{list(method_params.keys())[i]}'. Se esperaba el tipo '{list(method_params.values())[i]}' pero se obtuvo '{param_types[i]}'. (línea {expr.start.line})")
            if foundError: return "Error"
            if self.classes[self.current_class].methods[method_name].return_type == "SELF_TYPE": return self.current_class
            return self.classes[self.current_class].methods[method_name].return_type
        elif expr.getChildCount() == 3 and expr.getChild(1).getText() == "<-": # assign
            return self.visitAssign(expr)
        elif expr.getChildCount() == 3 and expr.getChild(0).getText() == "(": # parentheses
            return self.get_expr_type(expr.getChild(1))
        elif expr.getChildCount() == 3 and expr.getChild(1).getText() in ['+', '-', '*', '/']: # arith operations
            left_type = self.get_expr_type(expr.getChild(0))
            right_type = self.get_expr_type(expr.getChild(2))
            if self.check_casting(left_type, "Int", self.current_class) and self.check_casting(right_type, "Int", self.current_class):
                return 'Int'
            self.log(f'Error de tipos de operandos para {expr.getChild(1).getText()}: "{left_type}" y "{right_type}" (línea {expr.start.line})')
            return "Error"
        elif expr.getChildCount() == 3 and expr.getChild(1).getText() in ['<', '<=', '=']: # comparisons
            left_type = self.get_expr_type(expr.getChild(0))
            right_type = self.get_expr_type(expr.getChild(2))
            if (self.check_casting(left_type, "Int", self.current_class) and self.check_casting(right_type, "Int", self.current_class)) or \
               (self.check_casting(left_type, "Bool", self.current_class) and self.check_casting(right_type, "Bool", self.current_class)) or \
               (self.check_casting(left_type, "String", self.current_class) and self.check_casting(right_type, "String", self.current_class)):
                return 'Bool'
            self.log(f'Error de tipos de operandos para {expr.getChild(1).getText()}: "{left_type}" y "{right_type}" (línea {expr.start.line})')
            return "Error"
        elif expr.getChildCount() == 2 and expr.getChild(0).getText() in ['~', '-', 'not']: # unary operators
            expr_type = self.get_expr_type(expr.getChild(1))
            if self.check_casting(expr_type, "Int", self.current_class) and expr.getChild(0).getText() in ['~', '-']:
                return 'Int'
            elif self.check_casting(expr_type, "Bool", self.current_class) and expr.getChild(0).getText() in ['not']:
                return 'Bool'
            self.log(f'Error de tipo de operando para {expr.getChild(0).getText()}: "{expr_type}" (línea {expr.start.line})')
            return "Error"
        elif expr.getChildCount() == 2 and expr.getChild(0).getSymbol().type == YAPLParser.NEW: # new
            class_name = expr.getChild(1).getText()
            if class_name not in self.classes:
                self.log(f"La clase {class_name} no ha sido declarada. (línea {expr.start.line})")
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
                self.log(f'El símbolo {expr.getText()} no ha sido definido (línea {expr.start.line})')
                return 'Error'
            elif expr.getChild(0).getSymbol().type == YAPLParser.INTEGER: # int
                return 'Int'
            elif expr.getChild(0).getSymbol().type == YAPLParser.STRING: # str
                return 'String'
            elif expr.getChild(0).getSymbol().type in [YAPLParser.TRUE, YAPLParser.FALSE]: #bool
                return 'Bool'
            elif expr.getText() == "self": # self
                return 'SELF_TYPE'
            return "Error"
        return 'Error'

    def visitAssign(self, ctx):
        id_name = ctx.id_()[0].getText()
        if not self.classes[self.current_class].has_attribute(self.current_method, self.active_lets, id_name):
            self.log(f'El símbolo {id_name} no ha sido definido (línea {ctx.start.line})')
            return 'Error'
        id_type = self.classes[self.current_class].get_attribute_type(self.current_method, self.active_lets, id_name)
        expr_type = self.get_expr_type(ctx.expr(0))

        if not self.check_casting(expr_type, id_type, self.current_class):
            self.log(f"Error de tipo se esperaba '{id_type}' pero se obtuvo '{expr_type}' (linea {ctx.start.line})")
            return "Error"
        return id_type


    def verify_main_class(self):
        # Verificar que existe una clase llamada 'Main'
        if 'Main' not in self.classes:
            self.log("Error: La clase 'Main' no está definida.")
            return

        # Verificar que la clase 'Main' tiene un método llamado 'main'
        main_class_methods = self.classes['Main'].methods
        if 'main' not in main_class_methods:
            self.log("Error: La clase 'Main' no tiene un método 'main'.")
            return



    def verify_inheritance_rules(self):
        def check_recursive_inheritance(start_class):
            visited = set()
            current_class = start_class
            while current_class in self.inheritance_info:
                if current_class in visited:
                    self.log(f"Error: Herencia recursiva detectada con la clase '{current_class}'.")
                    return True
                visited.add(current_class)
                current_class = self.inheritance_info[current_class]
            return False

        #self.log(f"Reglas de herencia: {self.inheritance_info}")
        #self.log(f"Tabla de clases: {self.classes}")


        # Verificar que las clases de tipos básicos no son superclases.
        basic_types = ['Int', 'String', 'Bool']
        for basic_type in basic_types:
            if basic_type in self.inheritance_info.values():
                self.log(f"Error: La clase '{basic_type}' no puede ser heredada.")
                return

        # Verificar herencia recursiva.
        for cls in self.inheritance_info:
            if check_recursive_inheritance(cls):
                return

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
                self.log(f"'{variable_name}' ha sido inicializada con valor por defecto: {default_value}")
            else:
                self.log(f"Tipo desconocido '{variable_type}' para la variable '{variable_name}'. No se pudo inicializar con un valor por defecto.")


    def check_casting(self, expr_type, expected_type, class_name):
        if expected_type == "Object" and expr_type != "Error":
            return True
        if expected_type == "SELF_TYPE":
            expected_type = class_name
        if expr_type == "SELF_TYPE":
            expr_type = class_name
        if expr_type == expected_type:
            return True

        if expr_type == 'Int' and expected_type == 'Bool':
            # Int a Bool: 0 es False, cualquier valor positivo es True.
            return True
        
        if expr_type == 'Bool' and expected_type == 'Int':
            # Bool a Int: False es 0, True es 1.
            return True
        
        child_class = expr_type
        while True:
            if child_class in self.inheritance_info:
                parent_class = self.inheritance_info[child_class]
                if parent_class == expected_type:
                    return True
                child_class = parent_class
            else:
                break

        return False
