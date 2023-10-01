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
        
class MIPSInstruction:
    def __init__(self, opcode, rs, rt, rd, shamt, funct):
        self.opcode = opcode
        self.rs = rs
        self.rt = rt
        self.rd = rd
        self.shamt = shamt
        self.funct = funct

class TemporalManager:
    def __init__(self):
        self.available_temporals = [f"$t{i}" for i in range(10)]

    def get_new_temporal(self):
        if not self.available_temporals:
            raise Exception("No hay temporales disponibles")
        return self.available_temporals.pop()

    def recycle_temporal(self, temporal):
        self.available_temporals.append(temporal)