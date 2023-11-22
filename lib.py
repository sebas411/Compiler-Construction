class ClassObj(object):
    def __init__(self, name):
        self.name = name
        self.methods = {}
        self.attributes = {}
        self.inherited_methods = set()
        self.memory_address = None
        self.size = 0
    
    def inherit(self, o_class):
        self.methods = o_class.methods.copy()
        self.attributes = o_class.attributes.copy()
        self.inherited_methods = set(o_class.methods.keys())

    def is_inherited_method(self, method_name):
        return method_name in self.inherited_methods
    
    def add_method(self, name, method):
        if name in self.inherited_methods:
            self.inherited_methods.discard(name)
        self.methods[name] = method
    
    def add_attribute(self, name, type):
        new_att = Attribute(type)
        if type == "Int":
            att_size = 4
        elif type == "Bool":
            att_size = 4
        else: #punteros
            att_size = 4
        new_att.size = att_size
        new_att.offset = self.size
        self.size+= att_size
        self.attributes[name] = new_att
        
    
    def get_attribute_type(self, current_method, active_lets, attribute_name):
        if attribute_name in self.attributes:
            return self.attributes[attribute_name].type
        if current_method:
            return self.methods[current_method].get_attribute_type(attribute_name, active_lets)
        return "Error"
    
    def get_attribute(self, current_method, active_lets, attribute_name):
        if attribute_name in self.attributes:
            return self.attributes[attribute_name], "global"
        if current_method:
            return self.methods[current_method].get_attribute(attribute_name, active_lets), "local"
        return "Error", ""
    
    def has_attribute(self, current_method, active_lets, attribute_name):
        return attribute_name in self.attributes or (current_method and self.methods[current_method].has_attribute(attribute_name, active_lets))
        

class Method():
    def __init__(self, return_type, params):
        self.return_type = return_type
        self.params = {}
        self.max_off = 0
        self.add_params(list(params.keys()), list(params.values()))
        self.label = None
        self.lets = {}
        self.temporals = {}

    def add_params(self, attrs, types):
        for i in range(len(attrs)):
            new_att = Attribute(types[i])
            if types[i] == "Int":
                att_size = 4
            elif types[i] == "Bool":
                att_size = 4
            else: #punteros
                att_size = 4
            new_att.size = att_size
            new_att.offset = self.max_off
            self.max_off += att_size
            self.params[attrs[i]] = new_att

    def add_let(self, let_name, attrs, types):
        let = {}
        for i in range(len(attrs)):
            new_att = Attribute(types[i])
            if types[i] == "Int":
                att_size = 4
            elif types[i] == "Bool":
                att_size = 4
            else: #punteros
                att_size = 4
            new_att.size = att_size
            new_att.offset = self.max_off
            self.max_off += att_size
            let[attrs[i]] = new_att
        self.lets[let_name] = let
    
    def get_params(self):
        params = {}
        for param in self.params:
            params[param] = self.params[param].type
        return params

    def get_attribute_type(self, att_name, active_lets):
        if att_name in self.params:
            return self.params[att_name].type
        for _let in active_lets:
            if att_name in self.lets[_let]:
                return self.lets[_let][att_name].type
        return "Error"
    
    def get_attribute(self, att_name, active_lets):
        if att_name in self.params:
            return self.params[att_name]
        for _let in active_lets:
            if att_name in self.lets[_let]:
                return self.lets[_let][att_name]
        return "Error"
        

    def has_attribute(self, att_name, active_lets):
        for let_ in active_lets:
            if att_name in self.lets[let_]:
                return True
        return att_name in self.params


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
    
    def __str__(self) -> str:
        return f"{self.op}"
    def __repr__(self) -> str:
        return str(self)


class Label():
    def __init__(self, name):
        self.name = name
        self.line = 0
    
    def set_line(self, line):
        self.line = line

    def __str__(self) -> str:
        return f"{self.name}: {self.line}"
    
    def __repr__(self) -> str:
        return str(self)
        

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
                pcode+=f"return {instruction.arg1 or ''}"
            elif instruction.op == "call":
                pcode+=f"{instruction.result} = call {instruction.arg1},{instruction.arg2}"
            elif instruction.op == "if":
                pcode+=f"if {instruction.arg1} goto {instruction.result}"
            elif instruction.op == "ifFalse":
                pcode+=f"ifFalse {instruction.arg1} goto {instruction.result}"
            elif instruction.op == "goto":
                pcode+=f"goto {instruction.result}"
            elif instruction.op == "new":
                pcode+=f"{instruction.result} = new {instruction.arg1}"
            elif instruction.op == "HALT":
                pcode+="HALT"
            elif instruction.op == "not":
                pcode+=f"{instruction.result} = not {instruction.arg1}"
            elif instruction.op == "lnot":
                pcode+=f"{instruction.result} = lnot {instruction.arg1}"
            elif instruction.op == "minus":
                pcode+=f"{instruction.result} = minus {instruction.arg1}"
            elif instruction.op == "savera":
                pcode+="save $ra"
            elif instruction.op == "reserve":
                pcode+=f"reserve {instruction.arg1} {instruction.arg2}"
            elif instruction.op == "paramnum":
                pcode+=f"param_num {instruction.arg1}"
            elif instruction.op == "savetemporal":
                pcode+=f"save_temporal {instruction.arg1}"
            elif instruction.op == "restoretemporal":
                pcode+=f"restore_temporal {instruction.arg1}"
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
            # self.labels.append(n_label)
            return n_label
        return "Error"
    

    def set_label(self, l_label):
        if l_label:
            l_label.set_line(self.current_line)
            self.labels.append(l_label)
            return l_label
        return "Error"


class TemporalManager:
    def __init__(self):
        self.temporals = []
        self.pointers = []
        self.maxTemp = 0
        self.maxPointer = 0
        self.available_temporals = []

    def get_new_temporal(self):
        if len(self.available_temporals) > 0:
            temporal = self.available_temporals.pop(0)
        else:
            self.maxTemp += 1
            temporal = f"T{self.maxTemp}"
            self.temporals.append(temporal)
        return temporal
    
    def get_used_temporals(self):
        used_temporals = []
        for temporal in self.temporals:
            if temporal not in self.available_temporals:
                used_temporals.append(temporal)
        return used_temporals
    
    def get_pointer(self):
        self.maxPointer += 1
        pointer = f"P{self.maxPointer}"
        self.pointers.append(pointer)
        return pointer

    def free_temporal(self, temporal):
        if temporal not in self.temporals: return
        self.available_temporals.append(temporal)

    def reset_temps(self):
        self.maxTemp = 0
        self.available_temporals = []
        self.temporals = []
