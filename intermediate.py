from antlr4 import *
from antlr.YAPLParser import YAPLParser
from antlr.YAPLVisitor import YAPLVisitor
from lib import *
import copy

class IntermediateCodeVisitor(YAPLVisitor):
    def __init__(self):
        self.code = ""
        
    def getIntermediateCode(self):
        return self.code
        
    def visitClass_prod(self, ctx:YAPLParser.Class_prodContext):
        pass


    def visitFeature(self, ctx:YAPLParser.FeatureContext):
        pass

