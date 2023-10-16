class MIPSTranslator:
    def __init__(self, intermediateCode):
        self.intermediateCode = intermediateCode
        self.mipsCode = []

    def translate(self):
        lines = self.intermediateCode.split("\n")
        for line in lines:

            if "=" in line and "+" in line:
                dest, expr = line.split("=")
                y, op, z = expr.strip().split()
                self.mipsCode.append(f"add {dest.strip()}, {y}, {z}")
            
            elif "=" in line and "/" in line:
                dest, expr = line.split("=")
                y, op, z = expr.strip().split()
                self.mipsCode.append(f"div {y}, {z}")
                self.mipsCode.append(f"mflo {dest.strip()}")

    def getMIPSCode(self):
        return "\n".join(self.mipsCode)

    def printMIPSCode(self):
        print(self.getMIPSCode())