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
        self.availableTempRegs = [f"$t{i}" for i in range(8)]
        self.data = []
        self.maxstr = 0
        self.saved_temps = 0
        self.loadIP = None
        self.type_sizes = {}

    def translate(self):
        instructions = self.intermediateCode.code
        self.mipsCode.append(".text")
        self.mipsCode.append(".globl main")

        self.mipsCode.append("main:")
        self.mipsCode.append("    move $s7, $gp")
        self.mipsCode.append("    jal Main_Init")
        self.mipsCode.append("    jal Main_main")

        self.mipsCode.append("Object_abort:")
        self.mipsCode.append("    li		$v0, 10")
        self.mipsCode.append("    syscall")

        self.mipsCode.append("Object_Init:")
        self.mipsCode.append("    jr $ra")

        self.mipsCode.append("Object_type_name:")
        self.data.append('Type_name_object: .asciiz "Object"')
        self.mipsCode.append("    la		$v0, Type_name_object")
        self.mipsCode.append("    jr      $ra")

        self.mipsCode.append("Bool_type_name:")
        self.data.append('Type_name_bool: .asciiz "Bool"')
        self.mipsCode.append("    la		$v0, Type_name_bool")
        self.mipsCode.append("    jr      $ra")

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

        self.mipsCode.append("isvoid:")
        self.mipsCode.append("    li      $v0, 0")
        self.mipsCode.append("    jr      $ra")

        self.mipsCode.append("String_substr:")
        self.mipsCode.append("    lw        $s1, 0($sp)")
        self.mipsCode.append("    add		$s0, $s7, $s1")
        self.mipsCode.append("    lw        $s1, 4($sp)")
        self.mipsCode.append("    add		$s3, $gp, $s6")
        self.mipsCode.append("    add		$s6, $s6, $s1")
        self.mipsCode.append("    addi		$s6, $s6, 1")
        self.mipsCode.append("    move		$v0, $s3")
        self.mipsCode.append("Lsubstr1:")
        self.mipsCode.append("    slt       $t7, $0, $s1")
        self.mipsCode.append("    beq       $t7, $0, Lsubstr2")
        self.mipsCode.append("    lbu       $t6, 0($s0)")
        self.mipsCode.append("    sb        $t6, 0($s3)")
        self.mipsCode.append("    addi      $s0, $s0, 1")
        self.mipsCode.append("    addi      $s3, $s3, 1")
        self.mipsCode.append("    sub       $s1, $s1, 1")
        self.mipsCode.append("    j         Lsubstr1")
        self.mipsCode.append("Lsubstr2:")
        self.mipsCode.append("    sb        $0, 0($s3)")
        self.mipsCode.append("    jr        $ra")

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
                self.freeTemp(temp_dest)
                
            if instruction.op == "-":
                temp_dest = self.getTemp()
                op1 = self.genVarCode(instruction.arg1, "$s0")
                op2 = self.genVarCode(instruction.arg2, "$s1")
                self.mipsCode.append(f"    sub {temp_dest}, {op1}, {op2}")
                self.genStoreCode(instruction.result, temp_dest)
                self.freeTemp(temp_dest)
            
            if instruction.op == "/":
                temp_dest = self.getTemp()
                op1 = self.genVarCode(instruction.arg1, "$s0")
                op2 = self.genVarCode(instruction.arg2, "$s1")
                self.mipsCode.append(f"    div {op1}, {op2}")
                self.mipsCode.append(f"    mflo {temp_dest}")
                self.genStoreCode(instruction.result, temp_dest)
                self.freeTemp(temp_dest)

            if instruction.op == "*":
                temp_dest = self.getTemp()
                op1 = self.genVarCode(instruction.arg1, "$s0")
                op2 = self.genVarCode(instruction.arg2, "$s1")
                self.mipsCode.append(f"    mul {temp_dest}, {op1}, {op2}")
                self.genStoreCode(instruction.result, temp_dest)
                self.freeTemp(temp_dest)

            if instruction.op == "eq":
                temp_dest = self.getTemp()
                op1 = self.genVarCode(instruction.arg1, "$s0")
                op2 = self.genVarCode(instruction.arg2, "$s1")
                self.mipsCode.append(f"    seq {temp_dest}, {op1}, {op2}")
                self.genStoreCode(instruction.result, temp_dest)
                self.freeTemp(temp_dest)

            if instruction.op == "<":
                temp_dest = self.getTemp()
                op1 = self.genVarCode(instruction.arg1, "$s0")
                op2 = self.genVarCode(instruction.arg2, "$s1")
                self.mipsCode.append(f"    slt {temp_dest}, {op1}, {op2}")
                self.genStoreCode(instruction.result, temp_dest)
                self.freeTemp(temp_dest)

            if instruction.op == "<=":
                temp_dest = self.getTemp()
                op1 = self.genVarCode(instruction.arg1, "$s0")
                op2 = self.genVarCode(instruction.arg2, "$s1")
                self.mipsCode.append(f"    sle {temp_dest}, {op1}, {op2}")
                self.genStoreCode(instruction.result, temp_dest)
                self.freeTemp(temp_dest)

            if instruction.op == "=":
                if len(instruction.result.split(".")) > 1:
                    c += 1
                    continue
                op1 = self.genVarCode(instruction.arg1, "$s0")
                self.genStoreCode(instruction.result, op1)
            
            if instruction.op == "HALT":
                self.mipsCode.append("    li		$v0, 10")
                self.mipsCode.append("    syscall")

            if instruction.op == "ifFalse":
                op1 = self.genVarCode(instruction.arg1, "$s0")
                self.mipsCode.append(f"    slt $s1, $0, $s0")
                self.mipsCode.append(f"    beq $s1, $0, {instruction.result}")

            if instruction.op == "goto":
                self.mipsCode.append(f"    j {instruction.result}")

            if instruction.op == "savera":
                self.mipsCode.append("    sub $sp, $sp, 4")
                self.mipsCode.append("    sw		$ra, 0($sp)")
            
            if instruction.op == "savetemporal":
                op1 = self.genVarCode(instruction.arg1, "$s0")
                self.mipsCode.append("    sub $sp, $sp, 4")
                self.mipsCode.append(f"    sw		$s0, 0($sp)")
                self.saved_temps += 1

            if instruction.op == "restoretemporal":
                self.saved_temps = 0
                self.mipsCode.append(f"    lw		$s0, 0($sp)")
                self.mipsCode.append("    addi $sp, $sp, 4")
                self.genStoreCode(instruction.arg1, "$s0")


            if instruction.op == "paramnum":
                self.active_param_num = instruction.arg1
                self.mipsCode.append(f"    sub $sp, $sp, {instruction.arg1*4}")

            if instruction.op == "param":
                op1 = self.genVarCode(instruction.arg1, "$s0", extra_temps=(self.saved_temps+1+self.active_param_num))
                self.mipsCode.append(f"    sw		{op1}, 0($sp)")
                self.mipsCode.append("    addi $sp, $sp, 4")

            if instruction.op == "call":
                if int(instruction.arg2) > 0:
                    self.mipsCode.append(f"    sub $sp, $sp, {int(instruction.arg2)*4}")
                if self.loadIP:
                    op1 = self.genVarCode(self.loadIP, "$s7")
                self.mipsCode.append(f"    jal {instruction.arg1}")
                if int(instruction.arg2) > 0:
                    self.mipsCode.append(f"    addi $sp, $sp, {int(instruction.arg2)*4}")
                self.mipsCode.append("    lw $ra, 0($sp)")
                self.mipsCode.append("    addi $sp, $sp, 4")
                self.genStoreCode(instruction.result, "$v0")

            if instruction.op == "loadIP":
                self.loadIP = instruction.arg1
                self.mipsCode.append("    sub $sp, $sp, 4")
                self.mipsCode.append("    sw		$s7, 0($sp)")

            if instruction.op == "restoreIP":
                self.mipsCode.append("    lw $s7, 0($sp)")
                self.mipsCode.append("    addi $sp, $sp, 4")
                self.loadIP = None

            if instruction.op == "new":
                size = self.type_sizes[instruction.arg1]
                self.mipsCode.append("    add $s0, $gp, $s6")
                self.mipsCode.append(f"    addi $s6, $s6, {size}")
                self.genStoreCode(instruction.result, "$s0")

            if instruction.op == "reserve":
                self.type_sizes[instruction.arg1] = int(instruction.arg2)
            
            if instruction.op == "return":
                if instruction.arg1:
                    op1 = self.genVarCode(instruction.arg1, "$s0")
                    self.mipsCode.append(f"    move $v0, {op1}")
                self.mipsCode.append("    jr $ra")



            c+=1
        
        self.mipsCode.append(".data")
        for line in self.data:
            self.mipsCode.append(line)


    def genStoreCode(self, var, reg):
        if var == "T0":
            return
        st_name = ""
        if var[0] == "T":
            st_name = f"-{int(var[1])*4}($gp)"
        elif var[:3] == "SP[":
                st_name = f"{int(var[3])}($sp)"
        elif var[:3] == "IP[":
                st_name = f"{int(var[3:-1])}($s7)"
        else:
            return False
        self.mipsCode.append(f"    sw {reg}, {st_name}")
    
    def genVarCode(self, var, reg, extra_temps=None):
        extra_stack_space = 0
        if extra_temps:
            extra_stack_space = extra_temps * 4
        if var[0] == "T":
            self.mipsCode.append(f"    lw {reg}, -{int(var[1])*4}($gp)")
        elif var[:3] == "SP[":
            self.mipsCode.append(f"    lw {reg}, {int(var[3])+extra_stack_space}($sp)")
        elif var[:3] == "IP[":
            self.mipsCode.append(f"    lw {reg}, {int(var[3:-1])}($s7)")
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