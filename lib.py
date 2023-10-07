class ClassObj(object):
    def __init__(self, name):
        self.name = name
        self.methods = {}
        self.lets = {}
        self.attributes = {}
        self.inherited_methods = set()
        self.memory_address = None
    
    def inherit(self, o_class):
        self.methods = o_class.methods.copy()
        self.attributes = o_class.attributes.copy()
        self.inherited_methods = set(o_class.methods.keys())

    def is_inherited_method(self, method_name):
        return method_name in self.inherited_methods
    
    def get_attribute_type(self, current_method, active_lets, attribute_name):
        if current_method and attribute_name in self.methods[current_method].params:
            return self.methods[current_method].params[attribute_name]
        if attribute_name in self.attributes:
            return self.attributes[attribute_name]
        for let_ in active_lets:
            if attribute_name in self.lets[let_]:
                return self.lets[let_][attribute_name]
        return "Error"
    
    def has_attribute(self, current_method, active_lets, attribute_name):
        for let_ in active_lets:
            if attribute_name in self.lets[let_]:
                return True
        return attribute_name in self.attributes or (current_method and attribute_name in self.methods[current_method].params)
        

class Method():
    def __init__(self, return_type, params):
        self.return_type = return_type
        self.params = params
        self.label = None
        self.temporals = {} 


class Attribute():
    def __init__(self, att_type):
        self.type = att_type
        self.size = 0
        self.offset = 0
        

class IntermediateInstruction():
    def __init__(self, op, arg1, arg2, result):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result


class Label():
    def __init__(self, name):
        self.name = name
        self.line = 0
    
    def set_line(self, line):
        self.line = line
        

class IntermediateCode():
    def __init__(self):
        self.code = []
        self.labels = []
        self.max_generic_label = 0
        self.current_line = 0

    def addInstruction(self, op, arg1=None, arg2=None, result=None):
        self.code.append(IntermediateInstruction(op, arg1, arg2, result))
        self.current_line += 1

    def printable(self):
        pcode = ""
        c = 0
        label_counter = 0
        if len(self.labels) > 0: next_label = self.labels[label_counter]
        for instruction in self.code:
            if len(self.labels) > 0:
                while c == next_label.line:
                    label_counter += 1
                    pcode+=f"{next_label.name}:\n"
                    if label_counter >= len(self.labels): break
                    next_label = self.labels[label_counter]
            pcode+="    "
            if instruction.op == '=':
                pcode+=f"{instruction.result} = {instruction.arg1}"
            elif instruction.op in ['+', '-', '/', '*', 'eq', '<', '<=']:
                pcode+=f"{instruction.result} = {instruction.arg1} {instruction.op} {instruction.arg2}"
            elif instruction.op == "param":
                pcode+=f"param {instruction.arg1}"
            elif instruction.op == "return":
                pcode+=f"return {instruction.arg1}"
            elif instruction.op == "call":
                pcode+=f"{instruction.result} = call {instruction.arg1},{instruction.arg2}"
            elif instruction.op == "if":
                pcode+=f"if {instruction.arg1} goto {instruction.result}"
            elif instruction.op == "ifFalse":
                pcode+=f"ifFalse {instruction.arg1} goto {instruction.result}"
            elif instruction.op == "goto":
                pcode+=f"goto {instruction.result}"
            pcode+="\n"
            c += 1
        return pcode
    
    def has_label(self, label):
        for l in self.labels:
            if l.name == label:
                return l
        return False
    
    def new_label(self, name=None):
        if name is None:
            self.max_generic_label += 1
            name = f"L{self.max_generic_label}"
            while(self.has_label(name)):
                self.max_generic_label += 1
                name = f"L{self.max_generic_label}"

        if not self.has_label(name):
            n_label = Label(name)
            self.labels.append(n_label)
            return n_label
        return "Error"
    

    def set_label(self, label):
        l_label = self.has_label(label.name)
        if l_label:
            l_label.set_line(self.current_line)
            return l_label
        return "Error"


class TemporalManager:
    def __init__(self):
        self.temporals = []
        self.maxTemp = 0
        self.available_temporals = []

    def get_new_temporal(self):
        if len(self.available_temporals) > 0:
            temporal = self.available_temporals.pop(0)
        else:
            self.maxTemp += 1
            temporal = f"T{self.maxTemp}"
            self.temporals.append(temporal)
        return temporal
    

    def free_temporal(self, temporal):
        if temporal not in self.temporals: return
        self.available_temporals.append(temporal)