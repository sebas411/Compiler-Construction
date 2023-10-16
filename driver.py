import sys
from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener
from antlr.YAPLLexer import YAPLLexer
from antlr.YAPLParser import YAPLParser
from antlr.YAPLListener import YAPLListener
from graphviz import Digraph
from antlr4.tree.Trees import Trees
from lib import *
from semantic import TypeCheckingVisitor
from intermediate import IntermediateCodeVisitor
from mipsTranslator import *

class MyListener(YAPLListener, ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        print(f"Error de sintaxis en la línea {line}, columna {column}: {msg}")

    def visitErrorNode(self, node):
        print(f"Error: nodo no reconocido '{node.getText()}'")

class MIPSCode:
    def __init__(self):
        self.instructions = []

    def add_instruction(self, instruction):
        self.instructions.append(instruction)

def visualize_tree(node, dot):
    if isinstance(node, TerminalNode):
        dot.node(str(id(node)), str(node.getSymbol().text))
    else:
        rule_name = YAPLParser.ruleNames[node.getRuleContext().getRuleIndex()]
        dot.node(str(id(node)), rule_name)
        for i in range(node.getChildCount()):
            child = node.getChild(i)
            visualize_tree(child, dot)
            dot.edge(str(id(node)), str(id(child)))

def main(argv):
    if len(argv) < 2:
        print("Ingrese el programa yapl.")
        return
    input_stream = FileStream(argv[1], encoding='utf-8')
    lexer = YAPLLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = YAPLParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(MyListener())

    tree = parser.source()

    semanticVisitor = TypeCheckingVisitor()
    semanticVisitor.setClasses(tree)
    semanticVisitor.visit(tree)
    semanticVisitor.verify_main_class()
    semanticVisitor.verify_inheritance_rules()
    table = semanticVisitor.getTable()

    if parser.getNumberOfSyntaxErrors() == 0 and not semanticVisitor.found_errors:
        # Generar representación gráfica
        dot = Digraph(comment='Abstract Syntax Tree')
        visualize_tree(tree, dot)
        #dot.render('tree', format='png', view=True)

        # Generar representación textual
        textual_representation = Trees.toStringTree(tree, None, parser)
        #print(textual_representation)
        intermediateGenerator = IntermediateCodeVisitor(semanticVisitor)
        intermediateGenerator.setTable(table)
        intermediateGenerator.visit(tree)
        generated_code = intermediateGenerator.getCode()
        print("CÓDIGO INTERMEDIO")
        print(generated_code.printable())
        mipsTranslator = MIPSTranslator(generated_code.printable())
        mipsTranslator.translate()
        print("CÓDIGO MIPS")
        print(mipsTranslator.mipsCode)
        print("Código compilado exitosamente")
    else:
        print(semanticVisitor.getOutput())
        print("Se encontraron errores durante el análisis. Compilación falló.")

if __name__ == '__main__':
    main(sys.argv)

