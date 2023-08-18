class ClassObj(object):
    def __init__(self, name):
        self.name = name
        self.methods = {}
        self.attributes = {}
    
    def inherit(self, o_class):
        self.methods = o_class.methods
        self.attributes = o_class.attributes
    
    def get_attribute_type(self, current_method, attribute_name):
        if attribute_name in self.methods[current_method].params.keys():
            return self.methods[current_method].params[attribute_name]
        if attribute_name in self.attributes.keys():
            return self.attributes[attribute_name]
        return "Error"
    
    def has_attribute(self, current_method, attribute_name):
        return attribute_name in self.methods[current_method].params.keys() or attribute_name in self.attributes.keys()
        
class Method():
    def __init__(self, return_type, params):
        self.return_type = return_type
        self.params = params
        
class Attribute():
    def __init__(self, name, type):
        self.name = name
        self.type = type
        