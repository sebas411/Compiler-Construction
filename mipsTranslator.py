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
        self.data = []
        self.maxstr = 0

    def translate(self):
        instructions = self.intermediateCode.code
        self.mipsCode.append(".text")
        self.mipsCode.append(".globl main")

        self.mipsCode.append("main:")
        self.mipsCode.append("    la $s7, Main_attrs")
        self.mipsCode.append("    jal Main_main")

        self.mipsCode.append("IO_out_string:")
        self.mipsCode.append("    li		$v0, 4")
        self.mipsCode.append("    lw		$a0, 0($sp)")
        self.mipsCode.append("    syscall")
        self.mipsCode.append("    jr      $ra")

        self.mipsCode.append("IO_out_int:")
        self.mipsCode.append("    li      $v0, 1")
        self.mipsCode.append("    lw		$a0, 0($sp)")
        self.mipsCode.append("    syscall")
        self.mipsCode.append("    jr      $ra")

        self.mipsCode.append("IO_in_int:")
        self.mipsCode.append("    li      $v0, 5")
        self.mipsCode.append("    syscall")
        self.mipsCode.append("    jr      $ra")

        c = 0
        label_counter = 0
        if len(self.intermediateCode.labels) > 0: next_label = self.intermediateCode.labels[label_counter]
        for instruction in instructions:
            if len(self.intermediateCode.labels) > 0:
                while c == next_label.line:
                    label_counter += 1
                    self.mipsCode.append(f"{next_label.name}:")
                    if label_counter >= len(self.intermediateCode.labels): break
                    next_label = self.intermediateCode.labels[label_counter]
            if instruction.op == "+":
                temp_dest = self.getTemp()
                op1 = self.genVarCode(instruction.arg1, "$s0")
                op2 = self.genVarCode(instruction.arg2, "$s1")
                self.mipsCode.append(f"    add {temp_dest}, {op1}, {op2}")
                self.genStoreCode(instruction.result, temp_dest)
                
            if instruction.op == "/":
                temp_dest = self.getTemp()
                op1 = self.genVarCode(instruction.arg1, "$s0")
                op2 = self.genVarCode(instruction.arg2, "$s1")
                self.mipsCode.append(f"    div {op1}, {op2}")
                self.mipsCode.append(f"    mflo {temp_dest}")
                self.genStoreCode(instruction.result, temp_dest)
            
            if instruction.op == "=":
                if len(instruction.result.split(".")) > 1:
                    c += 1
                    continue
                op1 = self.genVarCode(instruction.arg1, "$s0")
                self.genStoreCode(instruction.result, op1)
            
            if instruction.op == "HALT":
                self.mipsCode.append("    li		$v0, 10")
                self.mipsCode.append("    syscall")

            if instruction.op == "-":
                temp_dest = self.getTemp()
                op1 = self.genVarCode(instruction.arg1, "$s0")
                op2 = self.genVarCode(instruction.arg2, "$s1")
                self.mipsCode.append(f"    sub {temp_dest}, {op1}, {op2}")
                self.genStoreCode(instruction.result, temp_dest)

            if instruction.op == "eq":
                temp_dest = self.getTemp()
                op1 = self.genVarCode(instruction.arg1, "$s0")
                op2 = self.genVarCode(instruction.arg2, "$s1")
                self.mipsCode.append(f"    seq {temp_dest}, {op1}, {op2}")
                self.genStoreCode(instruction.result, temp_dest)

            if instruction.op == "ifFalse":
                op1 = self.genVarCode(instruction.arg1, "$s0")
                self.mipsCode.append(f"    slt $s1, $0, $s0")
                self.mipsCode.append(f"    beq $s1, $0, {instruction.result}")

            if instruction.op == "goto":
                self.mipsCode.append(f"    j {instruction.result}")

            if instruction.op == "savera":
                self.mipsCode.append("    sub $sp, $sp, 4")
                self.mipsCode.append("    sw		$ra, 0($sp)")

            if instruction.op == "param":
                op1 = self.genVarCode(instruction.arg1, "$s0")
                self.mipsCode.append("    sub $sp, $sp, 4")
                self.mipsCode.append(f"    sw		{op1}, 0($sp)")

            if instruction.op == "call":
                self.mipsCode.append(f"    jal {instruction.arg1}")
                if int(instruction.arg2) > 0:
                    self.mipsCode.append(f"    addi $sp, $sp, {int(instruction.arg2)*4}")
                self.mipsCode.append("    lw $ra, 0($sp)")
                self.mipsCode.append("    addi $sp, $sp, 4")
                self.genStoreCode(instruction.result, "$v0")
            
            if instruction.op == "reserve":
                self.data.append(f"{instruction.arg1}_attrs: .space {instruction.arg2}")

            if instruction.op == "return":
                if instruction.arg1:
                    op1 = self.genVarCode(instruction.arg1, "$s0")
                    self.mipsCode.append(f"    move {op1}, $v0")
                self.mipsCode.append("    jr $ra")


            c+=1
        
        self.mipsCode.append(".data")
        for line in self.data:
            self.mipsCode.append(line)


    def genStoreCode(self, var, reg):
        st_name = ""
        if var[0] == "T":
            st_name = f"{int(var[1])*4}($gp)"
        elif var[:3] == "SP[":
                st_name = f"{int(var[3])*4}($sp)"
        elif var[:3] == "IP[":
                st_name = f"{int(var[3])*4}($s7)"
        else:
            return False
        self.mipsCode.append(f"    sw {reg}, {st_name}")
    
    def genVarCode(self, var, reg):
        if var[0] == "T":
            self.mipsCode.append(f"    lw {reg}, {int(var[1])*4}($gp)")
        elif var[:3] == "SP[":
            self.mipsCode.append(f"    lw {reg}, {int(var[3])*4}($sp)")
        elif var[:3] == "IP[":
            self.mipsCode.append(f"    lw {reg}, {int(var[3])*4}($s7)")
        elif is_num(var):
            self.mipsCode.append(f"    li {reg}, {var}")
        elif var[0] == '"':
            if not reg:
                reg = "$s0"
            self.maxstr += 1
            self.data.append(f"str{self.maxstr}: .asciiz {var}")
            self.mipsCode.append(f"    la {reg}, str{self.maxstr}")
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