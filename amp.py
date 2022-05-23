import sys
import os
import string
import inspect
from enum import Enum
import platform

class Token:
    pass

class Program(Token):
    def __init__(self, tokens):
        self.tokens = tokens
    
class Function(Token):
    def __init__(self, name, tokens, locals, parameters, return_):
        self.name = name
        self.tokens = tokens
        self.locals = locals
        self.parameters = parameters
        self.return_ = return_

class StructMarker(Token):
    def __init__(self, name):
        self.name = name
        
class Use(Token):
    def __init__(self, file):
        self.file = file

class Instruction():
    pass

class Declare(Instruction):
    def __init__(self, name, type):
        self.name = name
        self.type = type
    
class Assign(Instruction):
    def __init__(self, name):
        self.name = name
    
class Retrieve(Instruction):
    def __init__(self, name, data):
        self.name = name
        self.data = data
    
class Constant(Instruction):
    def __init__(self, value):
        self.value = value
    
class Invoke(Instruction):
    def __init__(self, name, parameter_count, parameters, return_ = ""):
        self.name = name
        self.parameter_count = parameter_count
        self.parameters = parameters
        self.return_ = return_
    
class Return(Instruction):
    def __init__(self, is_value):
        self.is_value = is_value

class PreCheckIf(Instruction):
    def __init__(self, id):
        self.id = id

class CheckIf(Instruction):
    def __init__(self, false_id, checking):
        self.false_id = false_id
        self.checking = checking

class EndIf(Instruction):
    def __init__(self, id):
        self.id = id

class EndIfBlock(Instruction):
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
    contents_split = file.read().split("\n")
    contents = "" 
    
    for content in contents_split:
        if "//" in content:
            contents += content[0 : content.index("//")]
        else:
            contents += content

    program = parse(contents, "Program", None)
    
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
    elif statement.startswith("enum "):
        return "Enum"    
    else:
        return "Statement"
    
def parse(contents, type, extra):
    if type == "Program":
        current_thing = ""
        things = []
        current_indent = 0
        for character in contents:
            if character == ';' and current_indent == 0:
                things.extend(parse(current_thing, getType(current_thing), things))
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
        arguments_old = contents[len("fn " + name) : contents.index("{")]
        arguments = arguments_old[0 : arguments_old.rindex(")")]

        current_argument = ""
        for character in arguments:
            if character == "," or character == ")":
                arguments_array.append(current_argument)
                current_argument = ""

            if (not character == " " and not character == "(" and not character == ")" and not character == ","):
                current_argument += character
        
        if arguments:
            arguments_array.append(current_argument)

        parameters = []
        for argument in arguments_array[::-1]:
            if argument:
                instructions.append(Declare(argument.split(":")[0], argument.split(":")[1].strip()))

        for argument in arguments_array:
            if argument:
                parameters.append(argument.split(":")[1].strip())
        
        for character in contents[contents.index("{") + 1 : contents.rindex("}")]:
            if character == ';' and current_indent == 0:
                instructions.extend(parse(current_thing, getType(current_thing), instructions))
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

        return_ = arguments_old[arguments_old.rindex(":") + 1 : len(arguments_old)] if ":" in arguments_old[arguments_old.rindex(")") : len(arguments_old)] else ""

        return [Function(name, instructions, locals, parameters, return_.strip() if return_.strip() else "none")]
    elif type == "Use":
        use = contents[contents.index(" ") + 1 : len(contents)]
        use = use[1 : len(use) - 1]
        return [Use(use)]
    elif type == "Struct":
        name = contents.split(" ")[1]
        items = {}
        items_list = []
        tokens = []

        body = contents[contents.index("{") + 1 : contents.index("}")]
        for item in body.split(";"):
            if item:
                item = item.strip()
                item_name = item.split(":")[0]

                get_name = name + "." + item_name
                instructions = []
                locals = []

                instructions.append(Declare("instance", name))
                instructions.append(Retrieve("instance", None))
                instructions.append(Constant(8 * len(items)))
                instructions.append(Invoke("@add", 2, []))
                instructions.append(Invoke("@get_8", 1, []))
                instructions.append(Invoke("@cast_" + item.split(":")[1].strip(), 1, []))
                instructions.append(Return(True))

                locals.append("instance")

                function = Function(get_name, instructions, locals, [name], item.split(":")[1].strip())
                tokens.append(function)

                set_name = name + "." + item_name
                instructions = []
                locals = []

                instructions.append(Declare("instance", name))
                instructions.append(Declare(item_name, item.split(":")[1].strip()))
                instructions.append(Retrieve("instance", None))
                instructions.append(Constant(8 * len(items)))
                instructions.append(Invoke("@add", 2, []))
                instructions.append(Retrieve(item_name, None))
                instructions.append(Invoke("@cast_integer", 1, []))
                instructions.append(Invoke("@set_8", 2, []))
                instructions.append(Return(False))

                locals.append(item_name)
                locals.append("instance")

                function = Function(set_name, instructions, locals, [name, item.split(":")[1].strip()], "none")
                tokens.append(function)

                items[item.split(":")[0]] = item.split(":")[1].strip()
                items_list.append(item.split(":")[0])

        instructions = []
        locals = []

        for item, type_ in reversed(items.items()):
            instructions.append(Declare(item, type_))
            locals.append(item)

        instructions.append(Declare("instance", name))

        instructions.append(Constant(8 * len(items)))
        instructions.append(Invoke("@allocate", 1, []))
        instructions.append(Invoke("@cast_" + name, 1, []))
        instructions.append(Assign("instance"))

        for item in items:
            instructions.append(Constant(8 * items_list.index(item)))
            instructions.append(Invoke("@cast_any", 1, []))
            instructions.append(Retrieve("instance", None))
            instructions.append(Invoke("@add", 2, []))
            instructions.append(Retrieve(item, None))
            instructions.append(Invoke("@cast_integer", 1, []))
            instructions.append(Invoke("@set_8", 2, []))

        instructions.append(Retrieve("instance", None))
        instructions.append(Return(True))

        locals.append("instance")

        function = Function(name + ".new", instructions, locals, list(items.values()), name)
        tokens.append(function)

        tokens.append(StructMarker(name))

        return tokens
    elif type == "Enum":
        name = contents.split(" ")[1]
        items = {}
        items_list = []
        tokens = []

        body = contents[contents.index("{") + 1 : contents.index("}")]
        for item in body.split(";"):
            if item:
                item = item.strip()

                get_name = name + "." + item
                instructions = []
                locals = []

                instructions.append(Constant(len(items_list)))
                instructions.append(Invoke("@cast_" + name, 1, []))
                instructions.append(Return(True))

                function = Function(get_name, instructions, locals, [], name)
                tokens.append(function)

                check_name = name + "." + item
                instructions = []
                locals = []

                instructions.append(Declare("instance", name))
                instructions.append(Retrieve("instance", None))
                instructions.append(Constant(len(items_list)))
                instructions.append(Invoke("@equal", 2, []))
                instructions.append(Return(True))

                locals.append("instance")

                function = Function(check_name, instructions, locals, [name], "boolean")
                tokens.append(function)

                items_list.append(item)

        tokens.append(StructMarker(name))

        return tokens
    elif type == "Statement":
        return parse_statement(contents, extra)
        
def parse_statement(contents, extra):
    contents = contents.strip()
    instructions = []

    global if_id

    if contents.startswith("let "):
        name = contents.split(" ")[1].replace(":", "")
        type_ = contents.split(" ")[2] if ":" in contents else ""
        instructions.append(Declare(name, type_))

        if contents.find("=") != -1:
            expression = contents[contents.index("=") + 1 : len(contents)]
            expression = expression.lstrip()
            instructions.extend(parse_statement(expression, extra + instructions))
            instructions.append(Assign(name))
    elif contents.startswith("return ") or contents == "return":
        return_value_statement = contents[7 : len(contents)]
        if return_value_statement:
            instructions.extend(parse_statement(return_value_statement, extra + instructions))
        instructions.append(Return(return_value_statement))
    elif contents.isnumeric():
        instructions.append(Constant(int(contents)))
    elif contents == "true" or contents == "false":
        instructions.append(Constant(contents == "true"))
    elif contents.startswith("\"") and contents.endswith("\"") and contents.count("\"") == 2:
        instructions.append(Constant(contents[1 : len(contents) - 1]))
    elif contents.startswith("if"):
        instructions.extend(parse_statement(contents[contents.index("(") + 1 : contents[0 : contents.index("{")].rindex(")")], extra + instructions))

        current_thing = ""
        current_indent = 0
        instructions2 = []

        id = if_id
        if_id += 1

        false_id = if_id
        if_id += 1

        end_id = if_id
        if_id += 1

        instructions.append(CheckIf(false_id, True))

        for character in contents[contents.index("{") + 1 : contents.rindex("}")]:
            if character == ';' and current_indent == 0:
                instructions2.extend(parse(current_thing, getType(current_thing), extra + instructions))
                current_thing = ""
            else:
                current_thing += character

            if character == '{':
                current_indent += 1
                if current_indent == 0:
                    element = current_thing[0 : len(current_thing) - 1].strip()
                    if element == "else":
                        id = false_id

                        false_id = if_id
                        if_id += 1

                        instructions2.append(PreCheckIf(id))
                        instructions2.append(CheckIf(false_id, False))
                    elif element.startswith("else if"):
                        id = false_id

                        false_id = if_id
                        if_id += 1

                        instructions2.append(PreCheckIf(id))
                        instructions2.extend(parse_statement(element[element.index("(") + 1 : element.rindex(")")], extra + instructions))
                        instructions2.append(CheckIf(false_id, True))
                    current_thing = ""
            elif character == '}':
                current_indent -= 1
                if current_indent < 0:
                    instructions2.append(EndIfBlock(end_id))
                    current_thing = ""

        instructions.extend(instructions2)

        instructions.append(EndIf(false_id))
        instructions.append(EndIf(end_id))
    elif contents.startswith("while"):
        id1 = if_id
        if_id += 1
        id2 = if_id
        if_id += 1

        instructions.append(PreStartWhile(id1, id2))

        instructions.extend(parse_statement(contents[contents.index("(") + 1 : contents[0 : contents.index("{")].rindex(")")], extra + instructions))

        current_thing = ""
        current_indent = 0
        instructions2 = []

        instructions.append(StartWhile(id1, id2))

        for character in contents[contents.index("{") + 1 : contents.rindex("}")]:
            if character == ';' and current_indent == 0:
                instructions2.extend(parse(current_thing, getType(current_thing), extra + instructions2))
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
        special_sign = ""
        special_index = -1
        current_parenthesis = 0
        last_character = ""
        for index, character in enumerate(contents):
            if character == "(":
                current_parenthesis += 1
            elif character == ")":
                current_parenthesis -= 1
            elif character == "+" and current_parenthesis == 0:
                special_sign = "+"
                special_index = index
            elif character == "*" and current_parenthesis == 0:
                special_sign = "*"
                special_index = index
            elif character == "/" and current_parenthesis == 0:
                special_sign = "/"
                special_index = index
            elif character == "%" and current_parenthesis == 0:
                special_sign = "%"
                special_index = index
            elif character == "=" and last_character == "=" and current_parenthesis == 0:
                special_sign = "=="
                special_index = index - 1
            elif character == "=" and last_character == "!" and current_parenthesis == 0:
                special_sign = "!="
                special_index = index - 1
            elif character == "<" and current_parenthesis == 0:
                special_sign = "<"
                special_index = index
            elif character == ">" and current_parenthesis == 0:
                special_sign = ">"
                special_index = index
            
            last_character = character
            
            if special_index != -1:
                break
            
        if "=" in contents and not contents[contents.index("=") + 1] == "=" and not contents[contents.index("=") - 1] == "!":
                name = contents.split(" ")[0]
                expression = contents[contents.index("=") + 1 : len(contents)]
                expression = expression.lstrip()
                instructions.extend(parse_statement(expression, extra + instructions))
                instructions.append(Assign(name))
        elif special_sign == "+":
            before = contents[0 : special_index].strip()
            after = contents[special_index + 1 : len(contents)].strip()
            instructions.extend(parse_statement(after, extra + instructions))
            instructions.extend(parse_statement(before, extra + instructions))
            instructions.append(Invoke("_+", 2, []))
        elif special_sign == "*":
            before = contents[0 : special_index].strip()
            after = contents[special_index + 1 : len(contents)].strip()
            instructions.extend(parse_statement(before, extra + instructions))
            instructions.extend(parse_statement(after, extra + instructions))
            instructions.append(Invoke("_*", 2, []))
        elif special_sign == "/":
            before = contents[0 : special_index].strip()
            after = contents[special_index + 1 : len(contents)].strip()
            instructions.extend(parse_statement(after, extra + instructions))
            instructions.extend(parse_statement(before, extra + instructions))
            instructions.append(Invoke("_/", 2, []))
        elif special_sign == "%":
            before = contents[0 : special_index].strip()
            after = contents[special_index + 1 : len(contents)].strip()
            instructions.extend(parse_statement(after, extra + instructions))
            instructions.extend(parse_statement(before, extra + instructions))
            instructions.append(Invoke("_%", 2, []))
        elif special_sign == "==":
            before = contents[0 : special_index].strip()
            after = contents[special_index + 2 : len(contents)].strip()
            instructions.extend(parse_statement(after, extra + instructions))
            instructions.extend(parse_statement(before, extra + instructions))
            instructions.append(Invoke("_==", 2, []))
        elif special_sign == "!=":
            before = contents[0 : special_index].strip()
            after = contents[special_index + 2 : len(contents)].strip()
            instructions.extend(parse_statement(after, extra + instructions))
            instructions.extend(parse_statement(before, extra + instructions))
            instructions.append(Invoke("_!=", 2, []))
        elif special_sign == "<":
            before = contents[0 : special_index].strip()
            after = contents[special_index + 2 : len(contents)].strip()
            instructions.extend(parse_statement(after, extra + instructions))
            instructions.extend(parse_statement(before, extra + instructions))
            instructions.append(Invoke("_<", 2, []))
        elif special_sign == ">":
            before = contents[0 : special_index].strip()
            after = contents[special_index + 2 : len(contents)].strip()
            instructions.extend(parse_statement(after, extra + instructions))
            instructions.extend(parse_statement(before, extra + instructions))
            instructions.append(Invoke("_>", 2, []))
        elif "(" in contents and contents.endswith(")"):
            max = 0
            index_thing = -1
            for index, character in enumerate(contents):
                if character == "(":
                    if max == 0:
                        index_thing = index
                    max += 1
                elif character == ")":
                    max -= 1
                    
            
            name = contents[0 : index_thing]
            
            if name:
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
                        instructions.extend(parse_statement(parameter, extra + instructions))
                
                if "." in name:
                    parsed = parse_statement(name[0 : name.rindex(".")], extra + instructions)
                    if isinstance(parsed[0], Retrieve) and len(parsed) == 1:
                        for instruction in (extra + instructions):
                            if isinstance(instruction, Declare):
                                if instruction.name == parsed[0].name:
                                    instructions.extend(parsed)
                                    name = "_." + name[name.rindex(".") + 1 : len(name)]
                    else:
                        instructions.extend(parsed)
                        name = "_." + name[name.rindex(".") + 1 : len(name)]

                instructions.append(Invoke(name, len(arguments_array), []))
            else:
                instructions.extend(parse_statement(contents[1 : len(contents) - 1], extra +  instructions))
        else:
            instructions.append(Retrieve(contents, None))
        
    return instructions
    
internals = [
    Function("@print_size", [], [], ["any", "integer"], "none"),
    Function("@add", [], [], ["any", "any"], "any"),
    Function("@get_8", [], [], ["any"], "integer"),
    Function("@set_8", [], [], ["integer", "any"], "none"),
    Function("@allocate", [], [], ["integer"], "any"),
    Function("@free", [], [], ["any", "integer"], "none"),
    Function("@print_memory", [], [], [], "none"),
    Function("@error_size", [], [], ["any", "integer"], "none"),
    Function("@read_size", [], [], ["any", "integer"], "none"),
    Function("@get_1", [], [], ["any"], "integer"),
    Function("@equal", [], [], ["any", "any"], "boolean"),
    Function("@copy", [], [], ["any", "any", "integer"], "none"),
    Function("@greater", [], [], ["integer", "integer"], "boolean"),
    Function("@modulo", [], [], ["integer", "integer"], "integer"),
    Function("@divide", [], [], ["integer", "integer"], "integer"),
    Function("@set_1", [], [], ["integer", "any"], "none"),
    Function("@not", [], [], ["boolean"], "boolean"),
    Function("@multiply", [], [], ["integer", "integer"], "integer"),
    Function("@less", [], [], ["integer", "integer"], "boolean"),
    Function("@exit", [], [], [], "none"),
    Function("@execute", [], [], ["any", "any", "boolean"], "none"),
    Function("@call_function", [], [], ["any", "any", "integer"], "any")
]

def process_program(program):
    return_value = 0
    
    functions = {}
    functions2 = {}
    program_types = ["integer", "boolean", "any"]

    for token in program.tokens:
        if isinstance(token, Function):
            id = token.name + "_" + str(len(token.parameters))
            functions.setdefault(id, [])

            for other_function in functions[id]:
                matches = True
                for i in range(0, len(other_function.parameters)):
                    if not other_function.parameters[i] == token.parameters[i]:
                        matches = False
                
                if matches:
                    print("PROCESS: " + token.name + " has duplicate definitions.")
                    return 1

            functions[id].append(token)
            functions2[token.name] = token
        elif isinstance(token, StructMarker):
            program_types.append(token.name)
    
    for function in internals:
        id = function.name + "_" + str(len(function.parameters))
        functions.setdefault(id, [])
        functions[id].append(function)
        functions2[token.name] = function
        
    for function in program.tokens:
        if isinstance(function, Function):
            types = []
            variables = {}
            j = 0
            while True:
                if j > len(function.tokens) - 1:
                    break

                instruction = function.tokens[j]
                if isinstance(instruction, Constant):
                    if isinstance(instruction.value, bool):
                        types.append("boolean")
                    elif isinstance(instruction.value, int):
                        types.append("integer")
                    elif isinstance(instruction.value, str):
                        types.append("String")
                elif isinstance(instruction, CheckIf):
                    if instruction.checking:
                        given_type = types.pop()
                elif isinstance(instruction, StartWhile):
                    given_type = types.pop()
                elif isinstance(instruction, Declare):
                    variables[instruction.name] = instruction.type
                elif isinstance(instruction, Assign):
                    given_type = types.pop()
                    if instruction.name in variables:
                        if variables[instruction.name] == "":
                            variables[instruction.name] = given_type
                elif isinstance(instruction, Retrieve):
                    if instruction.name in functions2 and not instruction.name in variables:
                        types.append("Function")
                    else:
                        if not instruction.name in variables:
                            types.append("unknown")
                        else:
                            types.append(variables[instruction.name])
                elif isinstance(instruction, Invoke):
                    if instruction.name.startswith("_."):
                        type_ = types[len(types) - 1]
                        instruction.name = instruction.name.replace("_.", type_ + ".")
                        instruction.parameter_count += 1

                    if instruction.name.startswith("@cast_") and instruction.name[6 : len(instruction.name)] in program_types:
                        types.pop()
                        types.append(instruction.name[6 : len(instruction.name)])
                    else:
                        id = instruction.name + "_" + str(instruction.parameter_count)

                        if id in functions:
                            named_functions = list(functions[id])
                            function2 = named_functions[0]

                            for i in range(0, instruction.parameter_count):
                                if len(types) > 0:
                                    given_type = types.pop()

                            instruction.parameters = function2.parameters
                            if not function2.return_ == "none":
                                types.append(function2.return_)
                        
                j += 1

    # type checking
    for token in program.tokens:
        if isinstance(token, Function):
            if type_check(token, token.tokens, program_types, functions, functions2, True) == 1:
                return_value = 1

    for function in list(program.tokens):
        if isinstance(function, Function):
            if not is_used(function, program.tokens):
                program.tokens.remove(function)

    return return_value

def type_check(function, instructions, program_types, functions, functions2, alter):
    return_value = 0

    types = []
    variables = {}
    for instruction in list(instructions):
        if isinstance(instruction, Constant):
            if isinstance(instruction.value, bool):
                types.append("boolean")
            elif isinstance(instruction.value, int):
                types.append("integer")
            elif isinstance(instruction.value, str):
                types.append("String")
        elif isinstance(instruction, CheckIf):
            if instruction.checking:
                if len(types) == 0:
                    print("PROCESS: If in " + function.name + " expects boolean, given nothing.")
                    return 1

                given_type = types.pop()
                if not is_type(given_type, "boolean"):
                    print("PROCESS: If in " + function.name + " expects boolean, given " + given_type + ".")
                    return 1
        elif isinstance(instruction, StartWhile):
            if len(types) == 0:
                print("PROCESS: While in " + function.name + " expects boolean, given nothing.")
                return 1

            given_type = types.pop()
            if not is_type(given_type, "boolean"):
                print("PROCESS: While in " + function.name + " expects boolean, given " + given_type + ".")
                return 1
        elif isinstance(instruction, Declare):
            variables[instruction.name] = instruction.type
        elif isinstance(instruction, Assign):
            if len(types) == 0:
                print("PROCESS: Assign of " + instruction.name + " in " + function.name + " expects " + (variables[instruction.name] if variables[instruction.name] else "a value") + ", given nothing.")
                return 1
            
            given_type = types.pop()

            if not instruction.name in variables:
                print("PROCESS: Variable " + instruction.name + " in " + function.name + " not found.")
                return 1

            if variables[instruction.name] == "":
                variables[instruction.name] = given_type

            if not is_type(given_type, variables[instruction.name]):
                print("PROCESS: Assign of " + instruction.name + " in " + function.name + " expects " + variables[instruction.name] + ", given " + given_type + ".")
                return 1
        elif isinstance(instruction, Retrieve):
            if instruction.name in functions2 and not instruction.name in variables:
                types.append("Function")
                instruction.data = functions2[instruction.name].parameters
            else:
                if not instruction.name in variables:
                    print("PROCESS: Variable " + instruction.name + " in " + function.name + " not found.")
                    return 1
                types.append(variables[instruction.name])
        elif isinstance(instruction, Invoke):
            if instruction.name.startswith("@cast_") and instruction.name[6 : len(instruction.name)] in program_types:
                types.pop()
                types.append(instruction.name[6 : len(instruction.name)])

                if alter:
                    function.tokens.remove(instruction)
            else:
                id = instruction.name + "_" + str(instruction.parameter_count)

                if not id in functions:
                    print("PROCESS: Function " + instruction.name + " with " + str(instruction.parameter_count) + " parameters in " + function.name + " not defined.")
                    return 1

                named_functions = list(functions[id])
                function2 = named_functions[0]

                cached_types = []

                i = 0
                while i < instruction.parameter_count:
                    if len(types) == 0:
                        print("PROCESS: Invoke of " + instruction.name + " in " + function.name + " expects " + function.parameters[i] + " as a parameter, given nothing.")
                        return 1

                    given_type = types.pop()
                    cached_types.append(given_type)

                    for function3 in named_functions:
                        if not is_type(given_type, function3.parameters[i]):
                            named_functions.remove(function3)

                    if len(named_functions) == 0:
                        print("PROCESS: Invoke of " + instruction.name + " in " + function.name + " expects " + function2.parameters[i] + " as a parameter, given " + given_type + ".")
                        return 1

                    function2 = named_functions[0]

                    #if not is_type(given_type, function2.parameters[i]):
                        #named_functions.remove(function2)
                        #if len(named_functions) == 0:
                            #print("PROCESS: Invoke of " + instruction.name + " in " + function.name + " expects " + function2.parameters[i] + " as a parameter, given " + given_type + ".")
                            #return 1
                    
                    i += 1
                    
                cached_types = cached_types[::-1]
                    
                if len(named_functions) > 1:
                    for i in range(0, instruction.parameter_count):
                        given_type = cached_types.pop()
                        for function3 in named_functions:
                            if not given_type == function3.parameters[i] and len(named_functions) > 1:
                                named_functions.remove(function3)
                                
                function2 = named_functions[0]

                instruction.parameters = function2.parameters
                instruction.return_ = function2.return_
                if not function2.return_ == "none":
                    types.append(function2.return_)
        elif isinstance(instruction, Return):
            if not function.return_ == "none":
                if len(types) == 0:
                    print("PROCESS: Return in " + function.name + " expects " + function.return_ + ", given nothing.")
                    return 1

                given_type = types.pop()
                if not is_type(given_type, function.return_):
                    print("PROCESS: Return in " + function.name + " expects " + function.return_ + ", given " + given_type + ".")
                    return 1

            if not len(types) == 0:
                print("PROCESS: Return in " + function.name + " has data in stack.")
                return 1
                
    if len(types) > 0:
        return types.pop()
    

def is_used(function, functions):
    if function.name == "main" or (function.name == "String.new" and function.parameters[0] == "any") or (function.name == "Function.new" and function.parameters[0] == "any") or (function.name == "Array.new" and function.parameters[0] == "any" and function.parameters[1] == "integer"):
        return True

    for other_function in functions:
        if isinstance(other_function, Function) and not other_function.name == function.name:
            for instruction in other_function.tokens:
                if isinstance(instruction, Invoke) and instruction.name == function.name and (other_function.name == "main" or is_used(other_function, functions)):
                    return True
                elif isinstance(instruction, Retrieve) and isinstance(instruction.data, list) and instruction.name == function.name and (other_function.name == "main" or is_used(other_function, functions)):
                    return True
        
    return False

def is_type(given, wanted):
    if wanted == "any":
        return True

    return given == wanted

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

    print_size = AsmFunction("@print_size_any~integer", [])
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

    error_size = AsmFunction("@error_size_any~integer", [])
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

    _start = AsmFunction("_start", [])
    _start.instructions.append("push rbp")
    _start.instructions.append("mov rbp, rsp")
    _start.instructions.append("mov qword [memory], 8")
    _start.instructions.append("mov qword [memory+16], 16376")
    _start.instructions.append("mov rax, [rbp+8]")
    _start.instructions.append("mov rcx, rax")
    _start.instructions.append("mov rdx, 8")
    _start.instructions.append("mul rdx")
    _start.instructions.append("push rcx")
    _start.instructions.append("push rax")
    _start.instructions.append("call @allocate_integer")
    _start.instructions.append("add rsp, 8")
    _start.instructions.append("pop rcx")
    _start.instructions.append("mov rax, 0")
    _start.instructions.append("dec rcx")
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
    _start.instructions.append("push r8")
    _start.instructions.append("push r10")
    _start.instructions.append("push rcx")
    _start.instructions.append("push rdx")
    _start.instructions.append("push rbx")
    _start.instructions.append("push r9")
    _start.instructions.append("call String.new_any")
    _start.instructions.append("add rsp, 8")
    _start.instructions.append("pop rbx")
    _start.instructions.append("pop rdx")
    _start.instructions.append("pop rcx")
    _start.instructions.append("pop r10")
    _start.instructions.append("mov [r10], r8")
    _start.instructions.append("pop r8")
    _start.instructions.append("pop rax")
    _start.instructions.append("inc rax")
    _start.instructions.append("jmp arguments_loop")
    _start.instructions.append("arguments_loop_end:")
    _start.instructions.append("push rcx")
    _start.instructions.append("push r8")
    _start.instructions.append("call Array.new_any~integer")
    _start.instructions.append("add rsp, 16")
    _start.instructions.append("push r8")
    _start.instructions.append("call main")
    _start.instructions.append("mov rax, 60")
    _start.instructions.append("xor rdi, rdi")
    _start.instructions.append("syscall")
    asm_program.functions.append(_start)

    add = AsmFunction("@add_any~any", [])
    add.instructions.append("push rbp")
    add.instructions.append("mov rbp, rsp")
    add.instructions.append("mov r8, [rbp+16]")
    add.instructions.append("add r8, [rbp+24]")
    add.instructions.append("mov rsp, rbp")
    add.instructions.append("pop rbp")
    add.instructions.append("ret")
    asm_program.functions.append(add)

    multiply = AsmFunction("@multiply_integer~integer", [])
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

    subtract = AsmFunction("@subtract_integer~integer", [])
    subtract.instructions.append("push rbp")
    subtract.instructions.append("mov rbp, rsp")
    subtract.instructions.append("mov r8, [rbp+16]")
    subtract.instructions.append("sub r8, [rbp+24]")
    subtract.instructions.append("mov rsp, rbp")
    subtract.instructions.append("pop rbp")
    subtract.instructions.append("ret")
    asm_program.functions.append(subtract)

    divide = AsmFunction("@divide_integer~integer", [])
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

    modulo = AsmFunction("@modulo_integer~integer", [])
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

    allocate = AsmFunction("@allocate_integer", [])
    allocate.instructions.append("push rbp")
    allocate.instructions.append("mov rbp, rsp")
    allocate.instructions.append("mov rbx, [rbp+16]") # rbx = allocated size
    allocate.instructions.append("mov r10, rbx") # rbx = allocated size
    
    allocate.instructions.append("xor rdx, rdx") # hacky solution bc buggyness happens when it's not a multiple of 8
    allocate.instructions.append("mov rax, rbx")
    allocate.instructions.append("mov r9, 8")
    allocate.instructions.append("div r9")
    allocate.instructions.append("cmp rdx, 0")
    allocate.instructions.append("je allocate_skip_filter")
    allocate.instructions.append("inc rax")
    allocate.instructions.append("mul r9")
    allocate.instructions.append("mov rbx, rax")
    allocate.instructions.append("allocate_skip_filter:")
    
    allocate.instructions.append("add rbx, 16") # add some padding which will be used for freeing later
    allocate.instructions.append("mov rcx, [memory]") # move the pointer to the first free value into rcx
    allocate.instructions.append("mov r9, 0")
    allocate.instructions.append("allocate_mark:") # used for jumping back if the memory block is not big enough
    allocate.instructions.append("mov rax, memory")
    allocate.instructions.append("add rax, rcx") # now rax stores beginning of new free memory

    allocate.instructions.append("mov r11, [rax+8]") # r11 stores the size of the free memory block

    allocate.instructions.append("cmp rbx, r11")
    allocate.instructions.append("jle allocate_done")
    allocate.instructions.append("mov r9, rcx") # r9 stores the previous location used
    allocate.instructions.append("mov rcx, [rax]")
    allocate.instructions.append("jmp allocate_mark")
    allocate.instructions.append("allocate_done:")
    allocate.instructions.append("mov r10, rcx") # rcx = location
    #allocate.instructions.append("sub rbx, 16") # the 16 bytes were just for a buffer anyways
    allocate.instructions.append("add r10, rbx") # rbx = size, r10 = location + size
    allocate.instructions.append("add r9, memory")
    allocate.instructions.append("sub r11, rbx") # r11 now with new length
    allocate.instructions.append("cmp r11, 16")
    allocate.instructions.append("jge not_zero")

    allocate.instructions.append("mov rdi, [rax]")
    allocate.instructions.append("mov [r9], rdi") # store next in previous location's next

    allocate.instructions.append("jmp done")
    allocate.instructions.append("not_zero:")

    allocate.instructions.append("mov [r9], r10") # store location + size in the previous location's next
    allocate.instructions.append("add r10, memory")
    allocate.instructions.append("mov r9, [rax]")
    allocate.instructions.append("mov qword [r10], r9") # store at location + size = the next location
    allocate.instructions.append("mov [r10+8], r11") # store length in location + size + 8

    allocate.instructions.append("done:")
    
    #allocate.instructions.append("add rbx, 16") # add the bytes back for length calculations
    
    allocate.instructions.append("mov r8, rcx") # move the index of the memory into r8
    allocate.instructions.append("add r8, memory") # make the value an actually relevant memory value
    allocate.instructions.append("sub rbx, 16")
    allocate.instructions.append("mov rcx, 0")
    allocate.instructions.append("allocate_zero:")
    allocate.instructions.append("cmp rcx, rbx")
    allocate.instructions.append("je allocate_zero_done")
    allocate.instructions.append("mov r9, r8")
    allocate.instructions.append("add r9, rcx")
    allocate.instructions.append("mov byte [r9], 0")
    allocate.instructions.append("add rcx, 1")
    allocate.instructions.append("jmp allocate_zero")
    allocate.instructions.append("allocate_zero_done:")
    allocate.instructions.append("mov rsp, rbp")
    allocate.instructions.append("pop rbp")
    allocate.instructions.append("ret")
    asm_program.functions.append(allocate)

    # TODO: automatically detect adjacent sections of free memory and combine to create a larger memory chunk (ex: | 8 bytes | 8 bytes | -> | 16 bytes |)
    free = AsmFunction("@free_any~integer", [])
    free.instructions.append("push rbp")
    free.instructions.append("mov rbp, rsp")
    free.instructions.append("mov rax, [rbp+16]") # rax is the pointer to freed memory
    free.instructions.append("mov r9, rax") # r9 = freed_head
    free.instructions.append("mov rcx, [memory]") # rcx stores the pointed head (before free)
    free.instructions.append("mov [rax], rcx") # now we store the head as our next memory slot
    free.instructions.append("mov rbx, [rbp+24]") # length
    
    free.instructions.append("push rax")

    free.instructions.append("xor rdx, rdx") # hacky solution bc buggyness happens when it's not a multiple of 8
    free.instructions.append("mov rax, rbx")
    free.instructions.append("mov r10, 8")
    free.instructions.append("div r10")
    free.instructions.append("cmp rdx, 0")
    free.instructions.append("je free_skip_filter")
    free.instructions.append("inc rax")
    free.instructions.append("mul r10")
    free.instructions.append("mov rbx, rax")
    free.instructions.append("free_skip_filter:")

    free.instructions.append("pop rax")
    
    free.instructions.append("add rbx, 16")
    free.instructions.append("mov [rax+8], rbx") # storing length of free space (including the 16 bytes for data storage)
    free.instructions.append("sub rax, memory")
    free.instructions.append("mov [memory], rax") # set new head to our location
    
    free.instructions.append("add rax, memory")
    free.instructions.append("add rax, rbx") # rax = freed_tail
    free.instructions.append("mov rcx, 0") # rcx = previous_current_check
    free.instructions.append("mov rdx, [memory]") # rdx = current_check
    free.instructions.append("free_loop:")
    
    free.instructions.append("cmp rdx, 0")
    free.instructions.append("je free_done")
    free.instructions.append("mov rbx, rdx")
    free.instructions.append("add rbx, memory")

    free.instructions.append("cmp rbx, rax") # if (current_check == freed_tail)

    free.instructions.append("jne free_done_if")

    free.instructions.append("mov r10, [rax+8]") # add length of the second segment to this segment's length
    free.instructions.append("add [r9+8], r10")

    free.instructions.append("push rdx")
    free.instructions.append("push rbx")
    free.instructions.append("push rcx")

    free.instructions.append("add rcx, memory")
    free.instructions.append("add rdx, memory")
    free.instructions.append("mov rbx, [rdx]")
    free.instructions.append("mov [rcx], rbx")

    free.instructions.append("pop rcx")
    free.instructions.append("pop rbx")
    free.instructions.append("pop rdx")

    free.instructions.append("jmp free_done_if2")

    free.instructions.append("free_done_if:")

    free.instructions.append("mov r12, rbx")
    free.instructions.append("add r12, [rbx+8]")
    free.instructions.append("cmp r12, r9") # if (current_tail == freed_head)
    free.instructions.append("jne free_done_if2")
    
    free.instructions.append("mov r10, [r9+8]") # add this segments length to the length of the segment before
    free.instructions.append("add [rbx+8], r10")
    
    free.instructions.append("push rcx")
    free.instructions.append("push r11")
    free.instructions.append("push r12")

    free.instructions.append("mov r11, 0")
    free.instructions.append("before_loop:")
    free.instructions.append("add r11, memory")
    free.instructions.append("mov r12, [r11]")
    free.instructions.append("sub r11, memory")
    free.instructions.append("add r12, memory")
    
    free.instructions.append("cmp r12, r9")
    free.instructions.append("jne not_pointing")

    free.instructions.append("mov rcx, [r12]")
    free.instructions.append("mov [r11+memory], rcx")

    free.instructions.append("not_pointing:")

    free.instructions.append("add r11, memory")
    free.instructions.append("mov r11, [r11]")
    free.instructions.append("cmp r11, 0")
    free.instructions.append("je end_before_loop")
    free.instructions.append("jmp before_loop")
    free.instructions.append("end_before_loop:")
    free.instructions.append("mov r9, rbx")
    free.instructions.append("pop r12")
    free.instructions.append("pop r11")
    free.instructions.append("pop rcx")

    free.instructions.append("free_done_if2:")

    free.instructions.append("mov rcx, rdx")
    free.instructions.append("add rdx, memory")
    free.instructions.append("mov rdx, [rdx]")
    free.instructions.append("jmp free_loop")

    free.instructions.append("free_done:")
    free.instructions.append("mov rsp, rbp")
    free.instructions.append("pop rbp")
    free.instructions.append("ret")
    asm_program.functions.append(free)

    print_memory = AsmFunction("@print_memory_", [])
    print_memory.instructions.append("push rbp")
    print_memory.instructions.append("mov rbp, rsp")
    print_memory.instructions.append("add rbp, 8")

    print_memory.instructions.append("mov rdi, rbp")
    print_memory.instructions.append("call print_integer")

    print_memory.instructions.append("mov rax, [memory]")

    print_memory.instructions.append("push rbx")
    print_memory.instructions.append("push rcx")
    print_memory.instructions.append("push r9")
    print_memory.instructions.append("push rax")
    print_memory.instructions.append("push r11")
    print_memory.instructions.append("mov rdi, rax")
    #print_memory.instructions.append("call print_integer")
    print_memory.instructions.append("pop r11")
    print_memory.instructions.append("pop rax")
    print_memory.instructions.append("pop r9")
    print_memory.instructions.append("pop rcx")
    print_memory.instructions.append("pop rbx")
    
    print_memory.instructions.append("loop_thing:")

    print_memory.instructions.append("add rax, memory")

    print_memory.instructions.append("push rbx")
    print_memory.instructions.append("push rcx")
    print_memory.instructions.append("push r9")
    print_memory.instructions.append("push rax")
    print_memory.instructions.append("push r11")
    print_memory.instructions.append("mov rdi, [rax]")
    #print_memory.instructions.append("call print_integer")
    print_memory.instructions.append("pop r11")
    print_memory.instructions.append("pop rax")
    print_memory.instructions.append("pop r9")
    print_memory.instructions.append("pop rcx")
    print_memory.instructions.append("pop rbx")
    
    print_memory.instructions.append("push rbx")
    print_memory.instructions.append("push rcx")
    print_memory.instructions.append("push r9")
    print_memory.instructions.append("push rax")
    print_memory.instructions.append("push r11")
    print_memory.instructions.append("mov rdi, rax")
    print_memory.instructions.append("sub rdi, memory")
    print_memory.instructions.append("call print_integer_space")
    print_memory.instructions.append("pop r11")
    print_memory.instructions.append("pop rax")
    print_memory.instructions.append("pop r9")
    print_memory.instructions.append("pop rcx")
    print_memory.instructions.append("pop rbx")

    print_memory.instructions.append("push rbx")
    print_memory.instructions.append("push rcx")
    print_memory.instructions.append("push r9")
    print_memory.instructions.append("push rax")
    print_memory.instructions.append("push r11")
    print_memory.instructions.append("mov rdi, [rax+8]")
    print_memory.instructions.append("call print_integer")
    print_memory.instructions.append("pop r11")
    print_memory.instructions.append("pop rax")
    print_memory.instructions.append("pop r9")
    print_memory.instructions.append("pop rcx")
    print_memory.instructions.append("pop rbx")

    print_memory.instructions.append("mov rax, [rax]")
    print_memory.instructions.append("cmp rax, 0")
    print_memory.instructions.append("je loop_done")
    print_memory.instructions.append("jmp loop_thing")
    print_memory.instructions.append("loop_done:")
    print_memory.instructions.append("sub rbp, 8")
    print_memory.instructions.append("mov rsp, rbp")
    print_memory.instructions.append("pop rbp")
    print_memory.instructions.append("ret")
    asm_program.functions.append(print_memory)

    copy = AsmFunction("@copy_any~any~integer", [])
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

    or_ = AsmFunction("@or_boolean~boolean", [])
    or_.instructions.append("push rbp")
    or_.instructions.append("mov rbp, rsp")
    or_.instructions.append("mov r8, [rbp+16]")
    or_.instructions.append("or r8, [rbp+24]")
    or_.instructions.append("mov rsp, rbp")
    or_.instructions.append("pop rbp")
    or_.instructions.append("ret")
    asm_program.functions.append(or_)

    and_ = AsmFunction("@and_boolean~boolean", [])
    and_.instructions.append("push rbp")
    and_.instructions.append("mov rbp, rsp")
    and_.instructions.append("mov r8, [rbp+16]")
    and_.instructions.append("and r8, [rbp+24]")
    and_.instructions.append("mov rsp, rbp")
    and_.instructions.append("pop rbp")
    and_.instructions.append("ret")
    asm_program.functions.append(and_)

    not_ = AsmFunction("@not_boolean", [])
    not_.instructions.append("push rbp")
    not_.instructions.append("mov rbp, rsp")
    not_.instructions.append("mov r8, [rbp+16]")
    not_.instructions.append("xor r8, 1")
    not_.instructions.append("mov rsp, rbp")
    not_.instructions.append("pop rbp")
    not_.instructions.append("ret")
    asm_program.functions.append(not_)

    equal = AsmFunction("@equal_any~any", [])
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

    less = AsmFunction("@less_integer~integer", [])
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

    greater = AsmFunction("@greater_integer~integer", [])
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

    set_1 = AsmFunction("@set_1_integer~any", [])
    set_1.instructions.append("push rbp")
    set_1.instructions.append("mov rbp, rsp")
    set_1.instructions.append("mov r8, [rbp+16]")
    set_1.instructions.append("mov r9, [rbp+24]")
    set_1.instructions.append("mov [r9], r8b")
    set_1.instructions.append("mov rsp, rbp")
    set_1.instructions.append("pop rbp")
    set_1.instructions.append("ret")
    asm_program.functions.append(set_1)

    set_8 = AsmFunction("@set_8_integer~any", [])
    set_8.instructions.append("push rbp")
    set_8.instructions.append("mov rbp, rsp")
    set_8.instructions.append("mov r8, [rbp+16]")
    set_8.instructions.append("mov r9, [rbp+24]")
    set_8.instructions.append("mov [r9], r8")
    set_8.instructions.append("mov rsp, rbp")
    set_8.instructions.append("pop rbp")
    set_8.instructions.append("ret")
    asm_program.functions.append(set_8)

    get = AsmFunction("@get_1_any", [])
    get.instructions.append("push rbp")
    get.instructions.append("mov rbp, rsp")
    get.instructions.append("mov r9, [rbp+16]")
    get.instructions.append("mov r8b, [r9]")
    get.instructions.append("mov rsp, rbp")
    get.instructions.append("pop rbp")
    get.instructions.append("ret")
    asm_program.functions.append(get)

    get = AsmFunction("@get_8_any", [])
    get.instructions.append("push rbp")
    get.instructions.append("mov rbp, rsp")
    get.instructions.append("mov r9, [rbp+16]")
    get.instructions.append("mov r8, [r9]")
    get.instructions.append("mov rsp, rbp")
    get.instructions.append("pop rbp")
    get.instructions.append("ret")
    asm_program.functions.append(get)

    read_size = AsmFunction("@read_size_any~integer", [])
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

    exit = AsmFunction("@exit_", [])
    exit.instructions.append("mov rax, 60")
    exit.instructions.append("xor rdi, rdi")
    exit.instructions.append("syscall")
    asm_program.functions.append(exit)

    execute = AsmFunction("@execute_any~any~boolean", [])
    execute.instructions.append("push rbp")
    execute.instructions.append("mov rbp, rsp")
    execute.instructions.append("mov rax, 57")
    execute.instructions.append("syscall")
    execute.instructions.append("cmp rax, 0")
    execute.instructions.append("jne _execute_thing")
    execute.instructions.append("mov rdi, [rbp+16]")
    execute.instructions.append("mov rsi, [rbp+24]")
    execute.instructions.append("mov rdx, 0")
    execute.instructions.append("mov rax, 59")
    execute.instructions.append("syscall")
    execute.instructions.append("mov rax, 60")
    execute.instructions.append("xor rdi, rdi")
    execute.instructions.append("syscall")
    execute.instructions.append("_execute_thing:")
    execute.instructions.append("mov rbx, [rbp+32]")
    execute.instructions.append("cmp rbx, 0")
    execute.instructions.append("je _execute_thing2")
    execute.instructions.append("mov rsi, rax")
    execute.instructions.append("mov rax, 247")
    execute.instructions.append("mov rdi, 1")
    execute.instructions.append("mov r10, 4")
    execute.instructions.append("mov r8, 0")
    execute.instructions.append("syscall")
    execute.instructions.append("mov rax, 247")
    execute.instructions.append("_execute_thing2:")
    execute.instructions.append("mov rsp, rbp")
    execute.instructions.append("pop rbp")
    execute.instructions.append("ret")
    asm_program.functions.append(execute)

    call_function = AsmFunction("@call_function_any~any~integer", [])
    call_function.instructions.append("push rbp")
    call_function.instructions.append("mov rbp, rsp")
    call_function.instructions.append("mov r9, [rbp+16]")
    call_function.instructions.append("mov rax, 8")
    call_function.instructions.append("xor rdx, rdx")
    call_function.instructions.append("mul qword [rbp+32]")
    call_function.instructions.append("sub rsp, rax")
    call_function.instructions.append("mov rdx, [rbp+24]")
    call_function.instructions.append("_call_function_not_done:")
    call_function.instructions.append("cmp qword [rdx], 0")
    call_function.instructions.append("je _call_function_done")
    call_function.instructions.append("push qword [rdx]")
    call_function.instructions.append("add rdx, 8")
    call_function.instructions.append("jmp _call_function_not_done")
    call_function.instructions.append("_call_function_done:")
    call_function.instructions.append("call r9")
    call_function.instructions.append("mov rsp, rbp")
    call_function.instructions.append("pop rbp")
    call_function.instructions.append("ret")
    asm_program.functions.append(call_function)
    
    functions = ["_start"]
    for token in program.tokens:
        if isinstance(token, Function):
            for instruction in token.tokens:
                if isinstance(instruction, Invoke):
                    functions.append(instruction.name + "_" + "~".join(instruction.parameters))
                    
    for function in list(asm_program.functions):
        if not function.name in functions:
            asm_program.functions.remove(function)

    index_thing = 0
    
    def get_asm_name(name):
        bad = "+=%/*<>!"
        new_name = ""
        for letter in name:
            if letter in bad:
                new_name += str(ord(letter))
            else:
                new_name += letter
        return new_name


    for token in program.tokens:
        if isinstance(token, Function):
            asm_function = AsmFunction("main" if token.name == "main" else get_asm_name(token.name) + "_" + "~".join(token.parameters), [])
            
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
                            if byte == 0x6e and encoded[index - 1] == 0x5c:
                                put.pop()
                                put.append("0xa")
                            elif byte == 0x30 and encoded[index - 1] == 0x5c:
                                put.pop()
                                put.append("0x0")
                            else:
                                put.append(hex(byte))

                        put_string = ",".join(put)

                        asm_function.instructions.append("push " + str(0 if not put_string else len(put_string.split(","))))
                        asm_function.instructions.append("push qword " + name)
                        asm_function.instructions.append("call String.new_any~integer")
                        asm_function.instructions.append("add rsp, 16")
                        asm_function.instructions.append("push r8")

                        if not put_string:
                            put_string = "0x0"

                        asm_program.data.append(AsmData(name, put_string))
                elif isinstance(instruction, Invoke):
                    asm_function.instructions.append("call " + get_asm_name(instruction.name) + "_" + "~".join(instruction.parameters))
                    asm_function.instructions.append("add rsp, " + str(instruction.parameter_count * 8))
                    if not instruction.return_ == "none":
                        asm_function.instructions.append("push r8")
                elif isinstance(instruction, Assign):
                    asm_function.instructions.append("pop r8")
                    index = token.locals.index(instruction.name)
                    if index <= len(token.parameters) - 1:
                        index -= 2
                    asm_function.instructions.append("mov [rbp" + "{:+d}".format(-index * 8 - 8 + 8 * len(token.parameters)) + "], r8")
                elif isinstance(instruction, Retrieve):
                    if isinstance(instruction.data, list) and not instruction.name in token.locals:
                        asm_function.instructions.append("push " + instruction.name + "_" + "~".join(instruction.data))
                        asm_function.instructions.append("call Function.new_any")
                        asm_function.instructions.append("add rsp, 8")
                        asm_function.instructions.append("push r8")
                    else:
                        index = token.locals.index(instruction.name)
                        if index <= len(token.parameters) - 1:
                            index -= 2
                        asm_function.instructions.append("push qword [rbp" + "{:+d}".format(-index * 8 - 8 + 8 * len(token.parameters)) + "]")
                elif isinstance(instruction, Return):
                    if instruction.is_value:
                         asm_function.instructions.append("pop r8")

                    asm_function.instructions.append("mov rsp, rbp")
                    asm_function.instructions.append("pop rbp")
                    asm_function.instructions.append("ret")
                elif isinstance(instruction, PreCheckIf):
                    asm_function.instructions.append("if_" + str(instruction.id) + ":") 
                elif isinstance(instruction, CheckIf):
                    if instruction.checking:
                        asm_function.instructions.append("pop r8")
                        asm_function.instructions.append("cmp r8, 1")
                        asm_function.instructions.append("jne if_" + str(instruction.false_id))
                elif isinstance(instruction, EndIf):
                    asm_function.instructions.append("if_" + str(instruction.id) + ":")
                elif isinstance(instruction, EndIfBlock):
                    asm_function.instructions.append("jmp if_" + str(instruction.id))
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
        
        function.instructions.insert(2, "sub rsp, " + str(stack_index_max * 8 * 2))
    
        for instruction in function.instructions:
            file.write("   " + instruction + "\n")
            
    file.write("""
    print_integer_space:
    mov     r9, -3689348814741910323
    sub     rsp, 40
    mov     BYTE [rsp+31], 32
    lea     rcx, [rsp+30]
.L2:
    mov     rax, rdi
    lea     r8, [rsp+32]
    mul     r9
    mov     rax, rdi
    sub     r8, rcx
    shr     rdx, 3
    lea     rsi, [rdx+rdx*4]
    add     rsi, rsi
    sub     rax, rsi
    add     eax, 48
    mov     BYTE [rcx], al
    mov     rax, rdi
    mov     rdi, rdx
    mov     rdx, rcx
    sub     rcx, 1
    cmp     rax, 9
    ja      .L2
    lea     rax, [rsp+32]
    mov     edi, 1
    sub     rdx, rax
    xor     eax, eax
    lea     rsi, [rsp+32+rdx]
    mov     rdx, r8
    mov     rax, 1
    syscall
    add     rsp, 40
    ret
    print_integer:
    mov     r9, -3689348814741910323
    sub     rsp, 40
    mov     BYTE [rsp+31], 10
    lea     rcx, [rsp+30]
.L2:
    mov     rax, rdi
    lea     r8, [rsp+32]
    mul     r9
    mov     rax, rdi
    sub     r8, rcx
    shr     rdx, 3
    lea     rsi, [rdx+rdx*4]
    add     rsi, rsi
    sub     rax, rsi
    add     eax, 48
    mov     BYTE [rcx], al
    mov     rax, rdi
    mov     rdi, rdx
    mov     rdx, rcx
    sub     rcx, 1
    cmp     rax, 9
    ja      .L2
    lea     rax, [rsp+32]
    mov     edi, 1
    sub     rdx, rax
    xor     eax, eax
    lea     rsi, [rsp+32+rdx]
    mov     rdx, r8
    mov     rax, 1
    syscall
    add     rsp, 40
    ret
    """)

    file.write(inspect.cleandoc("""
        section .data
    """))
    file.write("\n")

    for data in asm_program.data:
        file.write(data.name + ": db " + data.value + "\n")

    file.write(inspect.cleandoc("""
        section .bss
        memory: resb 16384
    """))

    file.close()

file_name_base = sys.argv[1][0 : sys.argv[1].index(".")]
program = parse_file(sys.argv[1])
if process_program(program) == 1:
    exit()

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
