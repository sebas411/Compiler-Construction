def is_num(s):
    try:
        int(s)
        return True
    except:
        return False

class MIPSTranslator:
    def __init__(self, intermediateCode):
        self.intermediateCode = intermediateCode
        self.mipsCode = []
        self.availableTempRegs = [f"$t{i}" for i in range(7)]

    def translate(self):
        self.mipsCode.append(".data")
        instructions = self.intermediateCode.code
        self.mipsCode.append(".text")
        for instruction in instructions:
            if instruction.op == "+":
                temp_dest = self.getTemp()
                op1 = self.genVarCode(instruction.arg1, "$s0")
                op2 = self.genVarCode(instruction.arg2, "$s1")
                self.mipsCode.append(f"add {temp_dest}, {op1}, {op2}")
                self.genStoreCode(instruction.result, temp_dest)
                
            if instruction.op == "/":
                temp_dest = self.getTemp()
                op1 = self.genVarCode(instruction.arg1, "$s0")
                op2 = self.genVarCode(instruction.arg2, "$s1")
                self.mipsCode.append(f"div {op1}, {op2}")
                self.mipsCode.append(f"mflo {temp_dest}")
                self.genStoreCode(instruction.result, temp_dest)
            
            if instruction.op == "=":
                if len(instruction.result.split(".")) > 1: continue
                op1 = self.genVarCode(instruction.arg1, "$s0")
                self.genStoreCode(instruction.result, op1)


    def genStoreCode(self, var, reg):
        st_name = ""
        if var[0] == "T":
            st_name = f"{int(var[1])*4}($gp)"
        elif var[:3] == "SP[":
                st_name = f"{int(var[3])*4}($sp)"
        else:
            return False
        self.mipsCode.append(f"sw {reg}, {st_name}")
    
    def genVarCode(self, var, reg):
        if var[0] == "T":
            self.mipsCode.append(f"lw {reg}, {int(var[1])*4}($gp)")
        elif var[:3] == "SP[":
            self.mipsCode.append(f"lw {reg}, {int(var[3])*4}($sp)")
        elif is_num(var):
            self.mipsCode.append(f"li {reg}, {var}")
        if reg:
            return reg
        return var

    def getTemp(self):
        if len(self.availableTempRegs) > 0:
            return self.availableTempRegs.pop(0)
        else:
            return None
        
    def freeTemp(self, temp):
        self.availableTempRegs.append(temp)

    def getCode(self):
        return self.mipsCode

    def printMIPSCode(self):
        print("\n".join(self.mipsCode))