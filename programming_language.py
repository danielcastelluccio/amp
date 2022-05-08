import sys
import os
import random
import string
import inspect
from enum import Enum
import platform

random.seed(0)

class Token:
    pass

class Program(Token):
    def __init__(self, tokens):
        self.tokens = tokens
    
class Function(Token):
    def __init__(self, name, tokens, locals, parameter_count):
        self.name = name
        self.tokens = tokens
        self.locals = locals
        self.parameter_count = parameter_count
        
class Use(Token):
    def __init__(self, file):
        self.file = file

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
    def __init__(self, name, parameter_count):
        self.name = name
        self.parameter_count = parameter_count
    
class Return(Instruction):
    def __init__(self, is_value):
        self.is_value = is_value
    
#class Raw(Instruction):
#    def __init__(self, instruction):
#        self.instruction = instruction
    
#class Push(Instruction):
#    def __init__(self):
#        pass

#class Pop(Instruction):
#    def __init__(self):
#        pass

class StartIf(Instruction):
    def __init__(self, id):
        self.id = id

class EndIf(Instruction):
    def __init__(self, id):
        self.id = id

class PreStartWhile(Instruction):
    def __init__(self, id1, id2):
        self.id1 = id1
        self.id2 = id2

class StartWhile(Instruction):
    def __init__(self, id1, id2):
        self.id1 = id1
        self.id2 = id2

class EndWhile(Instruction):
    def __init__(self, id1, id2):
        self.id1 = id1
        self.id2 = id2

if_id = 0
    
def parse_file(file):
    file = open(file, "r")
    contents = file.read()
    contents = contents.replace("\n", "")
    program = parse(contents, "Program")
    
    for token in program.tokens:
        if isinstance(token, Use):
            program.tokens.extend(parse_file(token.file).tokens)
    
    return program

def getType(statement):
    if statement.startswith("fn "):
        return "Function"
    elif statement.startswith("use "):
        return "Use"
    elif statement.startswith("struct "):
        return "Struct"    
    else:
        return "Statement"
    
def parse(contents, type):
    if type == "Program":
        current_thing = ""
        things = []
        current_indent = 0
        for character in contents:
            if character == ';' and current_indent == 0:
                things.extend(parse(current_thing, getType(current_thing)))
                current_thing = ""
            else:
                current_thing += character

            if character == '{':
                current_indent += 1
            elif character == '}':
                current_indent -= 1

        return Program(things)
    elif type == "Function":
        name = contents.split(" ")[1].split("(")[0]
        current_thing = ""
        instructions = []
        current_indent = 0

        arguments_array = []
        arguments = contents[len("fn " + name) : contents.index("{")]

        current_argument = ""
        for character in arguments:
            if character == "," or character == ")":
                arguments_array.append(current_argument)
                current_argument = ""

            if (not character == " " and not character == "(" and not character == ")" and not character == ","):
                current_argument += character
        
        if arguments:
            arguments_array.append(current_argument)

        parameter_count = 0
        for argument in arguments_array[::-1]:
            if argument:
                instructions.append(Declare(argument))
                parameter_count += 1
        
        for character in contents[contents.index("{") + 1 : contents.rindex("}")]:
            if character == ';' and current_indent == 0:
                instructions.extend(parse(current_thing, getType(current_thing)))
                current_thing = ""
            else:
                current_thing += character

            if character == '{':
                current_indent += 1
            elif character == '}':
                current_indent -= 1
                
        locals = []
                
        for instruction in instructions:
            if isinstance(instruction, Declare):
                locals.append(instruction.name)

        if len(instructions) == 0 or not isinstance(instructions[-1], Return):
            instructions.append(Return(False))

        return [Function(name, instructions, locals, parameter_count)]
    elif type == "Use":
        use = contents[contents.index(" ") + 1 : len(contents)]
        use = use[1 : len(use) - 1]
        return [Use(use)]
    elif type == "Struct":
        name = contents.split(" ")[1]
        items = []
        functions = []

        body = contents[contents.index("{") + 1 : contents.index("}")]
        for item in body.split(";"):
            if item:
                item = item.strip()

                get_name = name + "." + item
                instructions = []
                locals = []

                instructions.append(Declare("instance"))
                instructions.append(Retrieve("instance"))
                instructions.append(Constant(8 * len(items)))
                instructions.append(Invoke("add", 2))
                instructions.append(Invoke("get_8", 1))
                instructions.append(Return(True))

                locals.append("instance")

                function = Function(get_name, instructions, locals, 1)
                functions.append(function)

                set_name = name + "." + item
                instructions = []
                locals = []

                instructions.append(Declare("instance"))
                instructions.append(Declare(item))
                instructions.append(Retrieve("instance"))
                instructions.append(Constant(8 * len(items)))
                instructions.append(Invoke("add", 2))
                instructions.append(Retrieve(item))
                instructions.append(Invoke("set_8", 2))
                instructions.append(Return(False))

                locals.append(item)
                locals.append("instance")

                function = Function(set_name, instructions, locals, 2)
                functions.append(function)

                items.append(item)

        instructions = []
        locals = []

        for item in reversed(items):
            instructions.append(Declare(item))
            locals.append(item)

        instructions.append(Declare("instance"))

        instructions.append(Constant(8 * len(items)))
        instructions.append(Invoke("allocate", 1))
        instructions.append(Assign("instance"))

        for item in items:
            instructions.append(Constant(8 * items.index(item)))
            instructions.append(Retrieve("instance"))
            instructions.append(Invoke("add", 2))
            instructions.append(Retrieve(item))
            instructions.append(Invoke("set_8", 2))

        instructions.append(Retrieve("instance"))
        instructions.append(Return(True))

        locals.append("instance")

        function = Function(name + ".new", instructions, locals, len(items))
        functions.append(function)

        return functions
    elif type == "Statement":
        return parse_statement(contents)
        
def parse_statement(contents):
    contents = contents.lstrip()
    instructions = []

    global if_id

    if contents.startswith("let "):
        name = contents.split(" ")[1]
        instructions.append(Declare(name))

        if contents.find("=") != -1:
            expression = contents[contents.index("=") + 1 : len(contents)]
            expression = expression.lstrip()
            instructions.extend(parse_statement(expression))
            instructions.append(Assign(name))
    elif contents.startswith("return ") or contents == "return":
        return_value_statement = contents[7 : len(contents)]
        if return_value_statement:
            instructions.extend(parse_statement(return_value_statement))
        instructions.append(Return(return_value_statement))
    elif contents[0].isnumeric() or contents[0] == "-":
        instructions.append(Constant(int(contents)))
    elif contents == "true" or contents == "false":
        instructions.append(Constant(contents == "true"))
    elif contents.startswith("\""):
        instructions.append(Constant(contents[1 : len(contents) - 1]))
    #elif contents.startswith("asm "):
    #    instructions.append(Raw(contents[4: len(contents)]))
    #elif contents.startswith("push "):
    #    instructions.extend(parse_statement(contents[5 : len(contents)]))
    #    instructions.append(Push())
    #elif contents.startswith("pop"):
    #    instructions.append(Pop())
    elif contents.startswith("if"):
        instructions.extend(parse_statement(contents[contents.index("(") + 1 : contents[0 : contents.index("{")].rindex(")")]))

        current_thing = ""
        current_indent = 0
        instructions2 = []

        id = if_id
        if_id += 1

        instructions.append(StartIf(id))

        for character in contents[contents.index("{") + 1 : contents.rindex("}")]:
            if character == ';' and current_indent == 0:
                instructions2.extend(parse(current_thing, getType(current_thing)))
                current_thing = ""
            else:
                current_thing += character

            if character == '{':
                current_indent += 1
            elif character == '}':
                current_indent -= 1

        instructions.extend(instructions2)

        instructions.append(EndIf(id))
    elif contents.startswith("while"):
        id1 = if_id
        if_id += 1
        id2 = if_id
        if_id += 1

        instructions.append(PreStartWhile(id1, id2))

        instructions.extend(parse_statement(contents[contents.index("(") + 1 : contents[0 : contents.index("{")].rindex(")")]))

        current_thing = ""
        current_indent = 0
        instructions2 = []

        instructions.append(StartWhile(id1, id2))

        for character in contents[contents.index("{") + 1 : contents.rindex("}")]:
            if character == ';' and current_indent == 0:
                instructions2.extend(parse(current_thing, getType(current_thing)))
                current_thing = ""
            else:
                current_thing += character

            if character == '{':
                current_indent += 1
            elif character == '}':
                current_indent -= 1

        instructions.extend(instructions2)

        instructions.append(EndWhile(id1, id2))
    else:
        if "=" in contents:
                name = contents.split(" ")[0]
                expression = contents[contents.index("=") + 1 : len(contents)]
                expression = expression.lstrip()
                instructions.extend(parse_statement(expression))
                instructions.append(Assign(name))
        elif "(" in contents:
            name = contents[0 : contents.index("(")]

            arguments_array = []
            arguments = contents[len(name) + 1 : len(contents) - 1]

            current_argument = ""
            current_parenthesis = 0
            in_quotations = False
            for character in arguments:
                if character == "," and current_parenthesis == 0 and not in_quotations:
                    arguments_array.append(current_argument)
                    current_argument = ""
                elif character == "\"":
                    in_quotations = not in_quotations
                elif character == "(":
                    current_parenthesis += 1
                elif character == ")":
                    current_parenthesis -= 1

                if (not character == " " and not character == ",") or (not current_parenthesis == 0) or (in_quotations):
                    current_argument += character

            if arguments:
                arguments_array.append(current_argument)
            
            for parameter in arguments_array[::-1]:
                if parameter:
                    instructions.extend(parse_statement(parameter))
            instructions.append(Invoke(name, len(arguments_array)))
        else:
            instructions.append(Retrieve(contents))
        
    return instructions
    
def create_linux_binary(program, file_name_base):
    
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

    print_size = AsmFunction("print_size_2", [])
    print_size.instructions.append("push rbp")
    print_size.instructions.append("mov rbp, rsp")
    print_size.instructions.append("mov rdx, [rbp+24]")
    print_size.instructions.append("mov rsi, [rbp+16]")
    print_size.instructions.append("mov rdi, 1")
    print_size.instructions.append("mov rax, 1")
    print_size.instructions.append("syscall")
    print_size.instructions.append("mov rsp, rbp")
    print_size.instructions.append("pop rbp")
    print_size.instructions.append("ret")
    asm_program.functions.append(print_size)

    error_size = AsmFunction("error_size_2", [])
    error_size.instructions.append("push rbp")
    error_size.instructions.append("mov rbp, rsp")
    error_size.instructions.append("mov rdx, [rbp+24]")
    error_size.instructions.append("mov rsi, [rbp+16]")
    error_size.instructions.append("mov rdi, 2")
    error_size.instructions.append("mov rax, 1")
    error_size.instructions.append("syscall")
    error_size.instructions.append("mov rsp, rbp")
    error_size.instructions.append("pop rbp")
    error_size.instructions.append("ret")
    asm_program.functions.append(error_size)

    length = AsmFunction("length_1", [])
    length.instructions.append("push rbp")
    length.instructions.append("mov rbp, rsp")
    length.instructions.append("mov rdi, [rbp+16]")
    length.instructions.append("xor rax, rax")
    length.instructions.append("mov rcx, -1")
    length.instructions.append("cld")
    length.instructions.append("repne scasb")
    length.instructions.append("not rcx")
    length.instructions.append("dec rcx")
    length.instructions.append("mov r8, rcx")
    length.instructions.append("mov rsp, rbp")
    length.instructions.append("pop rbp")
    length.instructions.append("ret")
    asm_program.functions.append(length)

    _start = AsmFunction("_start", [])
    _start.instructions.append("push rbp")
    _start.instructions.append("mov rbp, rsp")
    _start.instructions.append("mov rax, [rbp+8]")
    _start.instructions.append("mov rcx, rax")
    _start.instructions.append("mov rdx, 8")
    _start.instructions.append("mul rdx")
    _start.instructions.append("push rcx")
    _start.instructions.append("push rax")
    _start.instructions.append("call allocate_1")
    _start.instructions.append("add rsp, 8")
    _start.instructions.append("pop rcx")
    _start.instructions.append("mov rax, 0")
    _start.instructions.append("arguments_loop:")
    _start.instructions.append("cmp rax, rcx")
    _start.instructions.append("je arguments_loop_end")
    _start.instructions.append("mov r10, rbp")
    _start.instructions.append("add r10, 24")
    _start.instructions.append("push rax")
    _start.instructions.append("mov rdx, 8")
    _start.instructions.append("mul rdx")
    _start.instructions.append("add r10, rax")
    _start.instructions.append("mov r9, [r10]")
    _start.instructions.append("mov r10, r8")
    _start.instructions.append("add r10, rax")
    _start.instructions.append("mov [r10], r9")
    _start.instructions.append("pop rax")
    _start.instructions.append("inc rax")
    _start.instructions.append("jmp arguments_loop")
    _start.instructions.append("arguments_loop_end:")
    _start.instructions.append("dec rcx")
    _start.instructions.append("push rcx")
    _start.instructions.append("push r8")
    _start.instructions.append("call Array.new_2")
    _start.instructions.append("add rsp, 16")
    _start.instructions.append("push r8")
    _start.instructions.append("call main")
    _start.instructions.append("mov rax, 60")
    _start.instructions.append("xor rdi, rdi")
    _start.instructions.append("syscall")
    asm_program.functions.append(_start)

    add = AsmFunction("add_2", [])
    add.instructions.append("push rbp")
    add.instructions.append("mov rbp, rsp")
    add.instructions.append("mov r8, [rbp+16]")
    add.instructions.append("add r8, [rbp+24]")
    add.instructions.append("mov rsp, rbp")
    add.instructions.append("pop rbp")
    add.instructions.append("ret")
    asm_program.functions.append(add)

    multiply = AsmFunction("multiply_2", [])
    multiply.instructions.append("push rbp")
    multiply.instructions.append("mov rbp, rsp")
    multiply.instructions.append("mov rax, [rbp+16]")
    multiply.instructions.append("xor rdx, rdx")
    multiply.instructions.append("mul qword [rbp+24]")
    multiply.instructions.append("mov r8, rax")
    multiply.instructions.append("mov rsp, rbp")
    multiply.instructions.append("pop rbp")
    multiply.instructions.append("ret")
    asm_program.functions.append(multiply)

    subtract = AsmFunction("subtract_2", [])
    subtract.instructions.append("push rbp")
    subtract.instructions.append("mov rbp, rsp")
    subtract.instructions.append("mov r8, [rbp+16]")
    subtract.instructions.append("sub r8, [rbp+24]")
    subtract.instructions.append("mov rsp, rbp")
    subtract.instructions.append("pop rbp")
    subtract.instructions.append("ret")
    asm_program.functions.append(subtract)

    divide = AsmFunction("divide_2", [])
    divide.instructions.append("push rbp")
    divide.instructions.append("mov rbp, rsp")
    divide.instructions.append("mov rax, [rbp+16]")
    divide.instructions.append("xor rdx, rdx")
    divide.instructions.append("div qword [rbp+24]")
    divide.instructions.append("mov r8, rax")
    divide.instructions.append("mov rsp, rbp")
    divide.instructions.append("pop rbp")
    divide.instructions.append("ret")
    asm_program.functions.append(divide)

    modulo = AsmFunction("modulo_2", [])
    modulo.instructions.append("push rbp")
    modulo.instructions.append("mov rbp, rsp")
    modulo.instructions.append("mov rax, [rbp+16]")
    modulo.instructions.append("xor rdx, rdx")
    modulo.instructions.append("div qword [rbp+24]")
    modulo.instructions.append("mov r8, rdx")
    modulo.instructions.append("mov rsp, rbp")
    modulo.instructions.append("pop rbp")
    modulo.instructions.append("ret")
    asm_program.functions.append(modulo)

    allocate = AsmFunction("allocate_1", [])
    allocate.instructions.append("push rbp")
    allocate.instructions.append("mov rbp, rsp")
    allocate.instructions.append("mov rax, [index]")
    allocate.instructions.append("mov rbx, rax")
    allocate.instructions.append("add rbx, [rbp+16]")
    allocate.instructions.append("mov [index], rbx")
    allocate.instructions.append("mov r8, memory")
    allocate.instructions.append("add r8, rax")
    allocate.instructions.append("mov rsp, rbp")
    allocate.instructions.append("pop rbp")
    allocate.instructions.append("ret")
    asm_program.functions.append(allocate)

    copy = AsmFunction("copy_3", [])
    copy.instructions.append("push rbp")
    copy.instructions.append("mov rbp, rsp")
    copy.instructions.append("mov rsi, [rbp+16]")
    copy.instructions.append("mov rdi, [rbp+24]")
    copy.instructions.append("mov rcx, [rbp+32]")
    copy.instructions.append("rep movsb")
    copy.instructions.append("mov rsp, rbp")
    copy.instructions.append("pop rbp")
    copy.instructions.append("ret")
    asm_program.functions.append(copy)

    or_ = AsmFunction("or_2", [])
    or_.instructions.append("push rbp")
    or_.instructions.append("mov rbp, rsp")
    or_.instructions.append("mov r8, [rbp+16]")
    or_.instructions.append("or r8, [rbp+24]")
    or_.instructions.append("mov rsp, rbp")
    or_.instructions.append("pop rbp")
    or_.instructions.append("ret")
    asm_program.functions.append(or_)

    and_ = AsmFunction("and_2", [])
    and_.instructions.append("push rbp")
    and_.instructions.append("mov rbp, rsp")
    and_.instructions.append("mov r8, [rbp+16]")
    and_.instructions.append("and r8, [rbp+24]")
    and_.instructions.append("mov rsp, rbp")
    and_.instructions.append("pop rbp")
    and_.instructions.append("ret")
    asm_program.functions.append(and_)

    not_ = AsmFunction("not_1", [])
    not_.instructions.append("push rbp")
    not_.instructions.append("mov rbp, rsp")
    not_.instructions.append("mov r8, [rbp+16]")
    not_.instructions.append("xor r8, 1")
    not_.instructions.append("mov rsp, rbp")
    not_.instructions.append("pop rbp")
    not_.instructions.append("ret")
    asm_program.functions.append(not_)

    equal = AsmFunction("equal_2", [])
    equal.instructions.append("push rbp")
    equal.instructions.append("mov rbp, rsp")
    equal.instructions.append("mov r8, [rbp+16]")
    equal.instructions.append("cmp r8, [rbp+24]")
    equal.instructions.append("jne equal_not_equal")
    equal.instructions.append("equal_equal:")
    equal.instructions.append("mov r8, 1")
    equal.instructions.append("mov rsp, rbp")
    equal.instructions.append("pop rbp")
    equal.instructions.append("ret")
    equal.instructions.append("equal_not_equal:")
    equal.instructions.append("mov r8, 0")
    equal.instructions.append("mov rsp, rbp")
    equal.instructions.append("pop rbp")
    equal.instructions.append("ret")
    asm_program.functions.append(equal)

    less = AsmFunction("less_2", [])
    less.instructions.append("push rbp")
    less.instructions.append("mov rbp, rsp")
    less.instructions.append("mov r8, [rbp+16]")
    less.instructions.append("cmp r8, [rbp+24]")
    less.instructions.append("jge less_not_less")
    less.instructions.append("less_less:")
    less.instructions.append("mov r8, 1")
    less.instructions.append("mov rsp, rbp")
    less.instructions.append("pop rbp")
    less.instructions.append("ret")
    less.instructions.append("less_not_less:")
    less.instructions.append("mov r8, 0")
    less.instructions.append("mov rsp, rbp")
    less.instructions.append("pop rbp")
    less.instructions.append("ret")
    asm_program.functions.append(less)

    greater = AsmFunction("greater_2", [])
    greater.instructions.append("push rbp")
    greater.instructions.append("mov rbp, rsp")
    greater.instructions.append("mov r8, [rbp+16]")
    greater.instructions.append("cmp r8, [rbp+24]")
    greater.instructions.append("jle greater_not_greater")
    greater.instructions.append("greater_greater:")
    greater.instructions.append("mov r8, 1")
    greater.instructions.append("mov rsp, rbp")
    greater.instructions.append("pop rbp")
    greater.instructions.append("ret")
    greater.instructions.append("greater_not_greater:")
    greater.instructions.append("mov r8, 0")
    greater.instructions.append("mov rsp, rbp")
    greater.instructions.append("pop rbp")
    greater.instructions.append("ret")
    asm_program.functions.append(greater)

    set_1 = AsmFunction("set_1_2", [])
    set_1.instructions.append("push rbp")
    set_1.instructions.append("mov rbp, rsp")
    set_1.instructions.append("mov r8, [rbp+16]")
    set_1.instructions.append("mov r9, [rbp+24]")
    set_1.instructions.append("mov [r9], r8b")
    set_1.instructions.append("mov rsp, rbp")
    set_1.instructions.append("pop rbp")
    set_1.instructions.append("ret")
    asm_program.functions.append(set_1)

    set_8 = AsmFunction("set_8_2", [])
    set_8.instructions.append("push rbp")
    set_8.instructions.append("mov rbp, rsp")
    set_8.instructions.append("mov r8, [rbp+16]")
    set_8.instructions.append("mov r9, [rbp+24]")
    set_8.instructions.append("mov [r9], r8")
    set_8.instructions.append("mov rsp, rbp")
    set_8.instructions.append("pop rbp")
    set_8.instructions.append("ret")
    asm_program.functions.append(set_8)

    get = AsmFunction("get_8_1", [])
    get.instructions.append("push rbp")
    get.instructions.append("mov rbp, rsp")
    get.instructions.append("mov r9, [rbp+16]")
    get.instructions.append("mov r8, [r9]")
    get.instructions.append("mov rsp, rbp")
    get.instructions.append("pop rbp")
    get.instructions.append("ret")
    asm_program.functions.append(get)

    read_size = AsmFunction("read_size_2", [])
    read_size.instructions.append("push rbp")
    read_size.instructions.append("mov rbp, rsp")
    read_size.instructions.append("mov rdx, [rbp+24]")
    read_size.instructions.append("mov rsi, [rbp+16]")
    read_size.instructions.append("mov rdi, 0")
    read_size.instructions.append("mov rax, 0")
    read_size.instructions.append("syscall")
    read_size.instructions.append("mov rsp, rbp")
    read_size.instructions.append("pop rbp")
    read_size.instructions.append("ret")
    asm_program.functions.append(read_size)

    index_thing = 0

    for token in program.tokens:
        if isinstance(token, Function):
            asm_function = AsmFunction("main" if token.name == "main" else token.name + "_" + str(token.parameter_count), [])
            
            asm_function.instructions.append("push rbp")
            asm_function.instructions.append("mov rbp, rsp")

            for instruction in token.tokens:
                if isinstance(instruction, Constant):
                    if isinstance(instruction.value, bool):
                        asm_function.instructions.append("push " + ("1" if instruction.value else "0"))
                    elif isinstance(instruction.value, int):
                        asm_function.instructions.append("push " + str(instruction.value))
                    elif isinstance(instruction.value, str):
                        letters = string.ascii_lowercase

                        printable = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
                        name = ''.join(filter(lambda x: x in printable, instruction.value)) + "_" + str(index_thing)
                        index_thing += 1

                        put = []
                        encoded = instruction.value.encode()
                        for index, byte in enumerate(encoded):
                            if byte == 0x6e:
                                if encoded[index - 1] == 0x5c:
                                    put.pop()
                                    put.append("0xa")
                                else:
                                    put.append(hex(byte))
                            else:
                                put.append(hex(byte))

                        put_string = ""
                        for thing in put:
                            put_string += thing + ","
    
                        put_string += "0x0"

                        asm_program.data.append(AsmData(name, put_string))
                        asm_function.instructions.append("mov r8, " + name)
                        asm_function.instructions.append("push r8")
                elif isinstance(instruction, Invoke):
                    asm_function.instructions.append("call " + instruction.name + "_" + str(instruction.parameter_count))
                    asm_function.instructions.append("add rsp, " + str(instruction.parameter_count * 8))
                    asm_function.instructions.append("push r8")
                #elif isinstance(instruction, Raw):
                #    asm_function.instructions.append(instruction.instruction)
                elif isinstance(instruction, Assign):
                    asm_function.instructions.append("pop r8")
                    index = token.locals.index(instruction.name)
                    if index <= token.parameter_count - 1:
                        index -= 2
                    asm_function.instructions.append("mov [rbp" + "{:+d}".format(-index * 8 - 8 + 8 * token.parameter_count) + "], r8")
                elif isinstance(instruction, Retrieve):
                    index = token.locals.index(instruction.name)
                    if index <= token.parameter_count - 1:
                        index -= 2
                    asm_function.instructions.append("push qword [rbp" + "{:+d}".format(-index * 8 - 8 + 8 * token.parameter_count) + "]")
                elif isinstance(instruction, Return):
                    if instruction.is_value:
                         asm_function.instructions.append("pop r8")

                    asm_function.instructions.append("mov rsp, rbp")
                    asm_function.instructions.append("pop rbp")
                    asm_function.instructions.append("ret")
                elif isinstance(instruction, StartIf):
                    asm_function.instructions.append("pop r8")
                    asm_function.instructions.append("cmp r8, 1")
                    asm_function.instructions.append("jne if_" + str(instruction.id))
                elif isinstance(instruction, EndIf):
                    asm_function.instructions.append("if_" + str(instruction.id) + ":")
                elif isinstance(instruction, PreStartWhile):
                    asm_function.instructions.append("while_" + str(instruction.id1) + ":")
                elif isinstance(instruction, StartWhile):
                    asm_function.instructions.append("pop r8")
                    asm_function.instructions.append("cmp r8, 1")
                    asm_function.instructions.append("jne while_" + str(instruction.id2))
                elif isinstance(instruction, EndWhile):
                    asm_function.instructions.append("jmp while_" + str(instruction.id1))
                    asm_function.instructions.append("while_" + str(instruction.id2) + ":")
            asm_program.functions.append(asm_function)

    try:
        os.mkdir(os.path.dirname("build/" + file_name_base + ".asm"))
    except:
        pass

    file = open("build/" + file_name_base + ".asm", "w")

    file.write(inspect.cleandoc("""
        global _start
        section .text
    """))
    file.write("\n")

    for function in asm_program.functions:
        file.write(function.name + ":\n")
        stack_index = 0
        stack_index_max = 0
        for instruction in function.instructions:
            if instruction.startswith("push "):
                stack_index += 1
            elif instruction.startswith("pop "):
                stack_index -= 1
            elif instruction.startswith("add rsp,"):
                stack_index -= int(int(instruction.split(" ")[2]) / 8)

            stack_index_max = max(stack_index, stack_index_max)

        function.instructions.insert(2, "sub rsp, " + str(stack_index_max * 8))
    
        for instruction in function.instructions:
            file.write("   " + instruction + "\n")

    file.write(inspect.cleandoc("""
        section .data
    """))
    file.write("\n")

    for data in asm_program.data:
        file.write(data.name + ": db " + data.value + "\n")

    file.write(inspect.cleandoc("""
        section .bss
        memory: resb 16384
        index: resb 8
    """))

    file.close()

file_name_base = sys.argv[1][0 : sys.argv[1].index(".")]
program = parse_file(sys.argv[1])

format = ""
system = platform.system()

try:
    os.mkdir("build")
except OSError:
    pass

if system == "Windows":
    #format = "win64"
    pass
elif system == "Linux":
    create_linux_binary(program, file_name_base)
    code = os.system("nasm -felf64 build/" + file_name_base + ".asm && ld build/" + file_name_base + ".o -o build/" + file_name_base)

    if "-r" in sys.argv and code == 0:
        arguments = " ".join(sys.argv[sys.argv.index("-r") + 1 :: ])
        os.system("./build/" + file_name_base + " " + arguments)
elif system == "Darwin":
    #format = "macho64"
    pass