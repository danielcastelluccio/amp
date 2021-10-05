import sys
import os
import random
random.seed(0)
import string
import inspect
from enum import Enum

class Token:
    pass

class Program(Token):
    def __init__(self, tokens):
        self.tokens = tokens
    
class Function(Token):
    def __init__(self, name, tokens, locals):
        self.name = name
        self.tokens = tokens
        self.locals = locals
    
class Statement(Token):
    def __init__(self, instructions):
        self.instructions = instructions

class Instruction():
    pass

class Declare(Instruction):
    def __init__(self, name):
        self.name = name
    
class Assign(Instruction):
    def __init__(self, name):
        self.name = name
    
class Retrieve(Instruction):
    def __init__(self, name):
        self.name = name
    
class Constant(Instruction):
    def __init__(self, value):
        self.value = value
    
class Invoke(Instruction):
    def __init__(self, name):
        self.name = name
    
class Return(Instruction):
    def __init__(self):
        pass
    
class Raw(Instruction):
    def __init__(self, instruction):
        self.instruction = instruction
    
class Push(Instruction):
    def __init__(self):
        pass

class Pop(Instruction):
    def __init__(self):
        pass
    
def parse_file(file):
    file = open(file, "r")
    contents = file.read()
    contents = contents.replace("\n", "")
    return parse(contents, "Program")

def getType(statement):
    if statement.startswith("function"):
        return "Function"
    else:
        return "Statement"
    
def parse(contents, type):
    if type == "Program":
        current_thing = ""
        things = []
        current_indent = 0
        for character in contents:
            if character == ';' and current_indent == 0:
                things.append(parse(current_thing, getType(current_thing)))
                current_thing = ""
            else:
                current_thing += character

            if character == '{':
                current_indent += 1
            elif character == '}':
                current_indent -= 1
        return Program(things)
    elif type == "Function":
        current_thing = ""
        statements = []
        current_indent = 0

        statements.append(Statement([Declare("stack"), Assign("stack")]))

        parameters = contents[contents.index("(") + 1 : contents.index(")")].split(",")
        for parameter in parameters[::-1]:
            if parameter:
                name = parameter.lstrip().split(" ")[1]
                statements.append(Statement([Declare(name), Assign(name)]))
        
        statements.append(Statement([Retrieve("stack")]))

        for character in contents[contents.index("{") + 1 : contents.rindex("}")]:
            if character == ';' and current_indent == 0:
                statements.append(parse(current_thing, getType(current_thing)))
                current_thing = ""
            else:
                current_thing += character

            if character == '{':
                current_indent += 1
            elif character == '}':
                current_indent -= 1
        
        locals = []
                
        for statement in statements:
            for instruction in statement.instructions:
                if isinstance(instruction, Declare):
                    locals.append(instruction.name)

        return Function(contents.split(" ")[1][0: contents.split(" ")[1].index("(")], statements, locals)
    elif type == "Statement":
        return Statement(parse_statement(contents))
        
def parse_statement(contents):
    contents = contents.lstrip()
    instructions = []

    if contents.startswith("variable "):
        name = contents.split(" ")[1]
        instructions.append(Declare(name))

        if contents.find("=") != -1:
            expression = contents[contents.index("=") + 1 : len(contents)]
            expression = expression.lstrip()
            instructions.extend(parse_statement(expression))
            instructions.append(Assign(name))
    elif contents.startswith("return "):
        instructions.append(Assign("stack"))
        instructions.extend(parse_statement(contents[7 : len(contents)]))
        instructions.append(Return())
        instructions.append(Retrieve("stack"))
    elif contents[0].isnumeric() or contents[0] == "-":
        instructions.append(Constant(int(contents)))
    elif contents.startswith("\""):
        instructions.append(Constant(contents[1 : len(contents) - 1]))
    elif contents.startswith("asm "):
        instructions.append(Raw(contents[4: len(contents)]))
    elif contents.startswith("push "):
        instructions.extend(parse_statement(contents[5 : len(contents)]))
        instructions.append(Push())
    elif contents.startswith("pop"):
        instructions.append(Pop())
    elif contents.find("(") != -1:
        inside_parenthesis = contents[contents.index("(") + 1 : contents.rindex(")")].split(",")
        for parameter in inside_parenthesis:
            if parameter:
                instructions.extend(parse_statement(parameter.lstrip()))
        instructions.append(Invoke(contents[0 : contents.index("(")]))
    else:
        instructions.append(Retrieve(contents))
    return instructions
    
def create_asm(program, file_name_base):
    
    class AsmProgram:
        def __init__(self, functions, data):
            self.functions = functions
            self.data = data
    
    class AsmFunction:
        def __init__(self, name, instructions):
            self.name = name
            self.instructions = instructions
            
    class AsmData:
        def __init__(self, name, value):
            self.name = name
            self.value = value
    
    asm_program = AsmProgram([], [])
    
    locals = ["r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15"]

    for token in program.tokens:
        if isinstance(token, Function):
            asm_function = AsmFunction(token.name, [])
            for statement in token.tokens:
                call_present = False
                for instruction in statement.instructions:
                    if isinstance(instruction, Invoke):
                        call_present = True
                
                if call_present:
                    for local in locals:
                        asm_function.instructions.append("push " + local)
                        
                locals_popped = []

                for instruction in statement.instructions:
                    if isinstance(instruction, Constant):
                        if isinstance(instruction.value, int):
                            asm_function.instructions.append("push " + str(instruction.value))
                        elif isinstance(instruction.value, str):
                            letters = string.ascii_lowercase
                            name = ( ''.join(random.choice(letters) for i in range(8)) )
                            asm_program.data.append(AsmData(name, "\"" + instruction.value + "\", 0x00"))
                            asm_function.instructions.append("push " + name)
                    elif isinstance(instruction, Invoke):
                        asm_function.instructions.append("call " + instruction.name)
                    elif isinstance(instruction, Raw):
                        asm_function.instructions.append(instruction.instruction)
                    elif isinstance(instruction, Assign):
                        asm_function.instructions.append("pop " + locals[token.locals.index(instruction.name)])
                        locals_popped.append(locals[token.locals.index(instruction.name)])
                    elif isinstance(instruction, Retrieve):
                        asm_function.instructions.append("push " + locals[token.locals.index(instruction.name)])
                        
                if call_present:
                    for local in locals[::-1]:
                        if not local in locals_popped:
                            asm_function.instructions.append("pop " + local)
                        else:
                            asm_function.instructions.append("pop rax")

            asm_function.instructions.append("ret")
            asm_program.functions.append(asm_function)

    file = open(file_name_base + ".asm", "w")

    file.write(inspect.cleandoc("""
        global _start
        section .text
    """))
    file.write("\n")

    for function in asm_program.functions:
        file.write(function.name + ":\n")
        for instruction in function.instructions:
            file.write("   " + instruction + "\n")

    file.write(inspect.cleandoc("""
        section .data
    """))
    file.write("\n")

    for data in asm_program.data:
        file.write(data.name + ": db " + data.value + "\n")

    file.close()
    
    os.system("nasm -felf64 " + file_name_base + ".asm && ld " + file_name_base + ".o -o " + file_name_base)

file_name_base = sys.argv[1][0 : sys.argv[1].index(".")]
program = parse_file(sys.argv[1])
create_asm(program, file_name_base)