import sys
import os
import subprocess
import string
import inspect
from enum import Enum
import platform
import copy

class Token:
    pass

class Program(Token):
    def __init__(self, tokens):
        self.tokens = tokens
    
class Function(Token):
    def __init__(self, name, tokens, locals, parameters, return_, generics, generics_applied = []):
        self.name = name
        self.tokens = tokens
        self.locals = locals
        self.parameters = parameters
        self.return_ = return_
        self.generics = generics
        self.generics_applied = generics_applied

class StructMarker(Token):
    def __init__(self, name, generics):
        self.name = name
        self.generics = generics

class EnumMarker(Token):
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

class Duplicate(Instruction):
    def __init__(self):
        pass
    
class Invoke(Instruction):
    def __init__(self, name, parameter_count, parameters, return_ = "", type_parameters = ""):
        self.name = name
        self.parameter_count = parameter_count
        self.parameters = parameters
        if not return_:
            return_ = []
        self.return_ = return_
        if not type_parameters:
            type_parameters = []
        self.type_parameters = type_parameters
    
class Return(Instruction):
    def __init__(self, value_count):
        self.value_count= value_count

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

class StartBlock(Instruction):
    def __init__(self, id):
        self.id = id

class EndBlock(Instruction):
    def __init__(self, id):
        self.id = id

if_id = 0
primitives = ["integer", "boolean", "any", "&any"]
    
def parse_file(file, top_level):
    file = open(file, "r")
    contents_split = file.read().split("\n")
    contents = "" 
    
    for content in contents_split:
        if "//" in content:
            contents += content[0 : content.index("//")] + "\n"
        else:
            contents += content + "\n"

    program = parse(contents, "Program", None)
    
    #included = []
    if top_level:
        for token in program.tokens:
            if isinstance(token, Use):
                program.tokens.extend(parse_file(token.file + ".amp", False).tokens)
    
    return program

def getType(statement):
    if statement.startswith("fn "):
        return "Function"
    elif statement.startswith("use "):
        return "Use"
    elif statement.startswith("struct "):
        return "Struct"
    elif statement.startswith("access "):
        return "Access"
    elif statement.startswith("enum "):
        return "Enum"    
    else:
        return "Statement"

    
def parse(contents, type, extra):
    if type == "Program":
        current_thing = ""
        things = []
        current_indent = 0
        in_quotes = False

        for character in contents:
            if character == '\n' and current_indent == 0:
                things.extend(parse(current_thing, getType(current_thing), things))
                current_thing = ""
            else:
                current_thing += character

            if character == '"':
                in_quotes = not in_quotes
            elif character == '{' and not in_quotes:
                current_indent += 1
            elif character == '}' and not in_quotes:
                current_indent -= 1

        return Program(things)
    elif type == "Function":
        name = contents[3 : contents.index("(")]

        current_thing = ""
        instructions = []
        current_indent = 0
        generics = []

        if "<" in name and ">" in name:
            for generic in name[name.index("<") + 1 : name.index(">")].split(","):
                generics.append(generic.strip())

            name = name[0 : name.index("<")]

        arguments_array = []
        arguments_old = contents[len(name) : contents.index("{") if "{" in contents else len(contents)]
        arguments = arguments_old[arguments_old.index("(") : arguments_old.rindex(")")]

        current_argument = ""
        current_indent = 0
        for character in arguments:
            if (character == "," and current_indent == 0) or character == ")":
                arguments_array.append(current_argument)
                current_argument = ""

            if character == "<":
                current_indent += 1
            elif character == ">":
                current_indent -= 1

            if (not character == " " and not character == "(" and not character == ")" and (not character == "," or current_indent > 0)):
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

        has_body = False
        if "{" in contents:
            has_body = True
            in_quotes = False
            for character in contents[contents.index("{") + 1 : contents.rindex("}")]:
                if character == '\n' and current_indent == 0:
                    instructions.extend(parse(current_thing, getType(current_thing), instructions))
                    current_thing = ""
                else:
                    current_thing += character

                if character == '"':
                    in_quotes = not in_quotes
                elif character == '{' and not in_quotes:
                    current_indent += 1
                elif character == '}' and not in_quotes:
                    current_indent -= 1
                
        locals = []
                
        if has_body:
            for instruction in instructions:
                if isinstance(instruction, Declare):
                    locals.append(instruction.name)

            if len(instructions) == 0 or not isinstance(instructions[-1], Return):
                instructions.append(Return(0))
        else:
            instructions = []

        return_ = (arguments_old[arguments_old.rindex(":") + 1 : len(arguments_old)] if ":" in arguments_old[arguments_old.rindex(")") : len(arguments_old)] else "").replace(" ", "")
        return_split = []
        index = 0
        built = ""
        for character in return_:
            if character == "<":
                index += 1
            elif character == ">":
                index -= 1

            if character == "," and index == 0:
                return_split.append(built)
                built = ""
            else:
                built += character

        if built.strip():
            return_split.append(built)

        return [Function(name, instructions, locals, parameters, return_split, generics)]
    elif type == "Use":
        use = contents[contents.index(" ") + 1 : len(contents)]
        use = use[1 : len(use) - 1]
        return [Use(use)]
    elif type == "Struct":
        name = contents[7 : first_non_quote_index(contents, "{")]
        name = name.strip()
        type_parameters = []
        name_full = name.replace(" ", "")
        if "<" in name:
            for parameter in name[name.index("<") + 1 : name.rindex(">")].split(","):
                parameter = parameter.strip()
                type_parameters.append(parameter)

            name = name[0 : name.index("<")]

        items = {}
        items_list = []
        tokens = []

        function_code = []

        body = contents[contents.index("{") + 1 : contents.rindex("}")]

        element = ""
        bracket_index = 0
        for character in body:
            if character == "\n" and bracket_index == 0:
                element = element.strip()
                if element:
                    element = element.strip()
                    if not "(" in element:
                        item = element
                        item_name = item.split(":")[0]

                        get_name = "_" + item_name
                        instructions = []
                        locals = []
                        
                        item_type = item.split(":")[1].strip()

                        instructions.append(Declare("instance", "&" + name_full))
                        instructions.append(Retrieve("instance", None))
                        instructions.append(Constant(8 * len(items)))
                        instructions.append(Invoke("@add", 2, ["&any", "&any"], ["any"]))
                        instructions.append(Invoke("@get_8", 1, ["any"], ["integer"]))
                        instructions.append(Invoke("@cast_" + item_type, 1, []))
                        instructions.append(Return(1))

                        if item_type[0] == "?":
                            item_type = item_type[1:]

                        if (not item_type in primitives or item_type == "any"):
                            item_type = "&" + item_type

                        locals.append("instance")
                        
                        function = Function(get_name, instructions, locals, ["&" + name_full], [item_type], type_parameters)
                        tokens.append(function)

                        instructions = []
                        locals = []

                        instructions.append(Declare("instance", "&" + name_full))
                        instructions.append(Declare(item_name, item.split(":")[1].strip()))
                        instructions.append(Retrieve(item_name, None))
                        #instructions.append(Invoke("@cast_integer", 1, []))
                        instructions.append(Retrieve("instance", None))
                        instructions.append(Constant(8 * len(items)))
                        instructions.append(Invoke("@add", 2, ["&any", "&any"], ["any"]))
                        instructions.append(Invoke("@set_8", 2, ["any", "integer"]))
                        instructions.append(Return(0))

                        locals.append(item_name)
                        locals.append("instance")

                        function = Function("_" + item_name + "=", instructions, locals, ["&" + name_full, item.split(":")[1].strip().replace("&", "")], [], type_parameters)
                        tokens.append(function)

                        items[item.split(":")[0]] = item.split(":")[1].strip()
                        items_list.append(item.split(":")[0])
                    else:
                        function = parse(element, "Function", extra + tokens)[0]
                        if function.name and len(function.parameters) > 0 and is_type(name, function.parameters[0]) and not function.parameters[0] == "any":
                            function.name = "_." + function.name
                        else:
                            if function.name:
                                function.name = name + "::" + function.name
                            else:
                                function.name = name

                        tokens.append(function)
                    element = ""
            elif character == "{":
                bracket_index += 1
            elif character == "}":
                bracket_index -= 1

            if not character == "\n" or not bracket_index == 0:
                element += character


        for item in items:
            get_consume_name = "_." + item + "_consume"
            instructions = []
            locals = []
                
            item_type = items[item]

            instructions.append(Declare("instance", "&" + name_full))
            instructions.append(Retrieve("instance", None))
            instructions.append(Constant(8 * items_list.index(item)))
            instructions.append(Invoke("@add", 2, []))
            instructions.append(Invoke("@get_8", 1, []))
            instructions.append(Invoke("@cast_" + item_type, 1, []))

            generics = []

            for item2 in items:
                if not items[item2] in primitives and not items[item2][0] == "&" and not items[item2][0] == "?":
                    if len(items[item2]) == 1:
                        generics.append(items[item2])

                    if not item == item2:
                        instructions.append(Invoke(items[item2] + "::memory_size", 0, [], "integer"))
                        instructions.append(Retrieve("instance", None))
                        instructions.append(Constant(8 * items_list.index(item2)))
                        instructions.append(Invoke("@add", 2, []))
                        instructions.append(Invoke("@get_8", 1, []))
                        instructions.append(Invoke("@cast_" + items[item2], 1, []))
                        instructions.append(Invoke("@free", 2, []))

            instructions.append(Invoke(name + "::memory_size", 0, [], "integer"))
            #instructions.append(Invoke(name + "::type", 0, [], ["Type"]))
            #instructions.append(Invoke("_memory_size", 1, ["&Type"], ["integer"]))
            instructions.append(Retrieve("instance", None))
            instructions.append(Invoke("@cast_any", 1, []))
            instructions.append(Invoke("@free", 2, []))

            instructions.append(Return(1))

            locals.append("instance")
                
            function = Function(get_consume_name, instructions, locals, [name + ("<" + ",".join(generics) + ">" if len(generics) > 0 else "")], [item_type], type_parameters)
            tokens.append(function)


        instructions = []
        locals = []

        for item, type_ in reversed(items.items()):
            instructions.append(Declare(item, type_))
            locals.append(item)

        instructions.append(Declare("instance", name_full))

        instructions.append(Constant(8 * len(items)))
        instructions.append(Invoke("@allocate", 1, ["integer"], ["any"]))
        instructions.append(Invoke("@cast_" + name_full, 1, []))
        instructions.append(Assign("instance"))
        generics = []

        for item in items:
            if len(items[item]) == 1:
                generics.append(items[item])

            instructions.append(Retrieve(item, None))
            #instructions.append(Invoke("@cast_integer", 1, []))
            instructions.append(Constant(8 * items_list.index(item)))
            instructions.append(Invoke("@cast_any", 1, []))
            instructions.append(Retrieve("instance", None))
            instructions.append(Invoke("@add", 2, ["&any", "&any"], ["any"]))
            instructions.append(Invoke("@set_8", 2, []))

        instructions.append(Retrieve("instance", None))
        instructions.append(Return(1))

        locals.append("instance")

        new_items = []
        for item in items.values():
            new_items.append(item.replace("&", ""))

        function = Function(name, instructions, locals, new_items, [name_full], type_parameters)
        tokens.append(function)

        ##################

        instructions = []
        instructions.append(Constant(len(items_list) * 8))
        instructions.append(Return(1))

        function = Function(name + "::memory_size", instructions, [], [], ["integer"], [])
        tokens.append(function)

        instructions = []
        instructions.append(Constant(len(items_list) * 8))
        instructions.append(Constant(name))
        instructions.append(Invoke("Type", 2, []))
        instructions.append(Return(1))

        function = Function(name + "::type", instructions, [], [], ["Type"], [])
        tokens.append(function)

        ###############

        instructions = []
        locals = []

        instructions.append(Declare("instance", "&" + name_full))

        for item in items:
            if not items[item] in primitives and not items[item][0] == "&" and not items[item][0] == "?":
                item_simplified = items[item][0 : items[item].index("<") if "<" in items[item] else len(items[item])]
                #instructions.append(Invoke(item_simplified + "::type", 0, [], ["Type"]))
                #instructions.append(Invoke("_memory_size", 1, ["&Type"], ["integer"]))
                instructions.append(Invoke(item_simplified + "::memory_size", 0, [], "integer"))
                instructions.append(Retrieve("instance", None))
                instructions.append(Constant(8 * items_list.index(item)))
                instructions.append(Invoke("@add", 2, ["&any", "&any"], ["any"]))
                instructions.append(Invoke("@get_8", 1, ["&any"], ["integer"]))
                instructions.append(Invoke("@cast_" + items[item], 1, []))
                instructions.append(Invoke("@free", 2, ["any", "integer"]))

        instructions.append(Return(0))

        locals.append("instance")


        function = Function(name + ".free", instructions, locals, ["&" + name_full], [], type_parameters)
        tokens.append(function)

        tokens.append(StructMarker(name, type_parameters))

        return tokens
    elif type == "Access":
        name = contents[7 : first_non_quote_index(contents, "{")]
        name = name.strip()
        type_parameters = []
        name_full = name.replace(" ", "")
        if "<" in name:
            for parameter in name[name.index("<") + 1 : name.rindex(">")].split(","):
                parameter = parameter.strip()
                type_parameters.append(parameter)

            name = name[0 : name.index("<")]

        tokens = []

        function_code = []

        body = contents[contents.index("{") + 1 : contents.rindex("}")]

        element = ""
        bracket_index = 0
        for character in body:
            if character == "\n" and bracket_index == 0:
                element = element.strip()
                if element:
                    element = element.strip()
                    function = parse(element, "Function", extra + tokens)[0]
                    if function.name and len(function.parameters) > 0 and is_type(name, function.parameters[0]) and not function.parameters[0] == "any":
                        function.name = "_." + function.name
                    else:
                        if function.name:
                            function.name = name + "::" + function.name
                        else:
                            function.name = name
                    tokens.append(function)
                    element = ""
            elif character == "{":
                bracket_index += 1
            elif character == "}":
                bracket_index -= 1

            if not character == "\n" or not bracket_index == 0:
                element += character

        return tokens
    elif type == "Enum":
        name = contents.split(" ")[1]
        items = {}
        items_list = []
        tokens = []

        body = contents[contents.index("{") + 1 : contents.index("}")]
        for item in body.split("\n"):
            if item:
                item = item.strip()

                get_name = name + "::" + item
                instructions = []
                locals = []

                instructions.append(Constant(len(items_list)))
                instructions.append(Invoke("@cast_any", 1, []))
                instructions.append(Invoke("@cast_" + name, 1, []))
                instructions.append(Return(1))

                function = Function(get_name, instructions, locals, [], [name], [])
                tokens.append(function)

                check_name = "_." + item
                instructions = []
                locals = []

                instructions.append(Declare("instance", "&" + name))
                instructions.append(Retrieve("instance", None))
                instructions.append(Constant(len(items_list)))
                instructions.append(Invoke("@equal", 2, []))
                instructions.append(Return(1))

                locals.append("instance")

                function = Function(check_name, instructions, locals, ["&" + name], ["boolean"], [])
                tokens.append(function)

                items_list.append(item)

        instructions = []
        instructions.append(Constant(8))
        instructions.append(Return(1))

        function = Function(name + "::memory_size", instructions, [], [], ["integer"], [])
        tokens.append(function)

        instructions = []
        instructions.append(Constant(8))
        instructions.append(Constant(name))
        instructions.append(Invoke("Type", 2, []))
        instructions.append(Return(1))

        function = Function(name + "::type", instructions, [], [], ["Type"], [])
        tokens.append(function)

        ###############

        instructions = []
        locals = []

        instructions.append(Declare("instance", "&" + name))

        instructions.append(Return(0))

        locals.append("instance")

        function = Function(name + ".free", instructions, locals, ["&" + name], [], [])
        tokens.append(function)

        tokens.append(EnumMarker(name))

        return tokens
    elif type == "Statement":
        return parse_statement(contents, extra)

def first_non_quote_index(string, wanted_character):
    in_quote = False
    for index, character in enumerate(string):
        if character == '"':
            in_quote = not in_quote
        elif character == wanted_character and not in_quote:
            return index
        
def parse_statement(contents, extra):
    contents = contents.strip()
    instructions = []

    global if_id

    if contents.startswith("let "):
        contents_variables = contents[4 : contents.index("=")]
        variables_split = contents_variables.split(",")

        names = []
        for variable in variables_split:
            variable = variable.strip()
            name = variable.split(" ")[0].replace(":", "")
            type_ = ""
            if len(variable.split(" ")) > 1:
                type_ = variable.split(" ")[1] if ":" in contents else ""
            instructions.append(Declare(name, type_))
            names.append(name)

        expression = contents[contents.index("=") + 1 : len(contents)]
        expression = expression.lstrip()
        instructions.extend(parse_statement(expression, extra + instructions))
        for name in names:
            instructions.append(Assign(name))
    elif contents.startswith("return ") or contents == "return":
        return_value_statement = contents[7 : len(contents)]
        if return_value_statement:
            parenthesis_index = 0
            built_return = ""
            comma_count = 0
            return_instructions = []
            for character in return_value_statement:
                if character == "(" or character == "<":
                    parenthesis_index += 1
                elif character == ")" or character == ">":
                    parenthesis_index -= 1
                elif character == "," and parenthesis_index == 0:
                    return_instructions = parse_statement(built_return, extra + instructions) + return_instructions
                    comma_count += 1
                    continue

            return_instructions = parse_statement(return_value_statement, extra + instructions) + return_instructions

            instructions.extend(return_instructions)
            instructions.append(Return(comma_count + 1))

        else:
            instructions.append(Return(0))
    elif contents.isnumeric():
        instructions.append(Constant(int(contents)))
    elif contents == "true" or contents == "false":
        instructions.append(Constant(contents == "true"))
    elif contents.startswith("\"") and contents.endswith("\"") and contents.count("\"") == 2:
        instructions.append(Constant(contents[1 : len(contents) - 1]))
    elif contents.startswith("if"):
        instructions.extend(parse_statement(contents[3 : first_non_quote_index(contents, "{")], extra + instructions))

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

        for character in contents[first_non_quote_index(contents, "{") + 1 : contents.rindex("}")]:
            if character == '\n' and current_indent == 0:
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
                        instructions2.extend(parse_statement(element[8:], extra + instructions))
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

        instructions.extend(parse_statement(contents[6 : contents.index("{")], extra + instructions))

        current_thing = ""
        current_indent = 0
        instructions2 = []

        instructions.append(StartWhile(id1, id2))

        for character in contents[contents.index("{") + 1 : contents.rindex("}")]:
            if character == '\n' and current_indent == 0:
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
    elif contents.startswith("{"):
        current_thing = ""
        current_indent = 0
        id_thing = if_id
        if_id += 1
        instructions.append(StartBlock(id_thing))
        for character in contents[contents.index("{") + 1 : contents.rindex("}")]:
            if character == '\n' and current_indent == 0:
                instructions.extend(parse(current_thing, getType(current_thing), extra + instructions))
                current_thing = ""
            else:
                current_thing += character

            if character == '{':
                current_indent += 1
            elif character == '}':
                current_indent -= 1
        instructions.append(EndBlock(id_thing))
    else:
        split = False
        if "," in contents:
            current_indent = 0
            current_thing = ""
            instructions2 = []
            in_quotes = False
            for character in contents:
                if character == "\"":
                    in_quotes = not in_quotes
                if character == "(" or character == "<":
                    current_indent += 1
                elif character == ")" or character == ">":
                    current_indent -= 1
                
                if character == "," and current_indent == 0 and not in_quotes:
                    split = True
                    instructions2 = parse(current_thing, getType(current_thing), extra + instructions + instructions2) + instructions2
                    current_thing = ""
                else:
                    current_thing += character

            if current_thing and split:
                instructions2 = parse(current_thing, getType(current_thing), extra + instructions + instructions2) + instructions2

            instructions.extend(instructions2)

        if not split:
            special_sign = ""
            special_index = -1
            special_index2 = -1
            special_index3 = -1
            current_parenthesis = 0
            last_character = ""
            for index, character in enumerate(contents):
                if character == "(":
                    if (last_character == ">" and (special_sign == "<" or special_sign == ">")) or special_sign == "[]":
                        special_sign = ""
                        special_index = -1
                    current_parenthesis += 1
                elif character == ")":
                    current_parenthesis -= 1
                elif character == "+" and current_parenthesis == 0 and (special_index == -1 or "." in special_sign or "[]" == special_sign):
                    special_sign = "+"
                    special_index = index
                elif character == "-" and current_parenthesis == 0 and (special_index == -1 or "." in special_sign or "[]" == special_sign):
                    special_sign = "-"
                    special_index = index
                elif character == "*" and current_parenthesis == 0 and (special_index == -1 or "." in special_sign or "[]" == special_sign):
                    special_sign = "*"
                    special_index = index
                elif character == "/" and current_parenthesis == 0 and (special_index == -1 or "." in special_sign or "[]" == special_sign):
                    special_sign = "/"
                    special_index = index
                elif character == "%" and current_parenthesis == 0 and (special_index == -1 or "." in special_sign or "[]" == special_sign):
                    special_sign = "%"
                    special_index = index
                elif character == "=" and last_character == "=" and current_parenthesis == 0:
                    special_sign = "=="
                    special_index = index - 1
                elif character == "=" and last_character == "!" and current_parenthesis == 0:
                    special_sign = "!="
                    special_index = index - 1
                elif character == "<" and current_parenthesis == 0 and (special_index == -1 or "." in special_sign or "[]" == special_sign):
                    special_sign = "<"
                    special_index = index
                elif character == ">" and current_parenthesis == 0 and (special_index == -1 or "." in special_sign or "[]" == special_sign):
                    special_sign = ">"
                    special_index = index
                elif character == "[" and current_parenthesis == 0 and (special_index == -1 or "." in special_sign or "[]" == special_sign):
                    special_sign = "[]"
                    special_index = index
                elif character == "]" and current_parenthesis == 0 and special_index2 == -1:
                    special_index2 = index
                elif character == "=" and current_parenthesis == 0 and special_sign == "[]":
                    if not last_character == "=":
                        special_sign = "[]="
                        special_index3 = index
                elif character == "." and current_parenthesis == 0 and (special_index == -1 or special_sign == ".") and not "(" in contents[index : (contents.rindex("=") if "=" in contents[index:] else len(contents))]:
                    special_sign = "."
                    special_index = index
                elif character == "=" and current_parenthesis == 0 and special_sign == ".":
                    if not last_character == "=":
                        special_sign = ".="
                        special_index2 = index
                
                last_character = character

            if "=" in contents and not contents[contents.index("=") + 1] == "=" and not contents[contents.index("=") - 1] == "!" and not special_sign == "[]=" and not special_sign == ".=":
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
                instructions.append(Invoke("_.+", 2, []))
            elif special_sign == "-":
                before = contents[0 : special_index].strip()
                after = contents[special_index + 1 : len(contents)].strip()
                instructions.extend(parse_statement(after, extra + instructions))
                instructions.extend(parse_statement(before, extra + instructions))
                instructions.append(Invoke("_.-", 2, []))
            elif special_sign == "*":
                before = contents[0 : special_index].strip()
                after = contents[special_index + 1 : len(contents)].strip()
                instructions.extend(parse_statement(before, extra + instructions))
                instructions.extend(parse_statement(after, extra + instructions))
                instructions.append(Invoke("_.*", 2, []))
            elif special_sign == "/":
                before = contents[0 : special_index].strip()
                after = contents[special_index + 1 : len(contents)].strip()
                instructions.extend(parse_statement(after, extra + instructions))
                instructions.extend(parse_statement(before, extra + instructions))
                instructions.append(Invoke("_./", 2, []))
            elif special_sign == "%":
                before = contents[0 : special_index].strip()
                after = contents[special_index + 1 : len(contents)].strip()
                instructions.extend(parse_statement(after, extra + instructions))
                instructions.extend(parse_statement(before, extra + instructions))
                instructions.append(Invoke("_.%", 2, []))
            elif special_sign == "==":
                before = contents[0 : special_index].strip()
                after = contents[special_index + 2 : len(contents)].strip()
                instructions.extend(parse_statement(after, extra + instructions))
                instructions.extend(parse_statement(before, extra + instructions))
                instructions.append(Invoke("_.==", 2, []))
            elif special_sign == "!=":
                before = contents[0 : special_index].strip()
                after = contents[special_index + 2 : len(contents)].strip()
                instructions.extend(parse_statement(after, extra + instructions))
                instructions.extend(parse_statement(before, extra + instructions))
                instructions.append(Invoke("_.!=", 2, []))
            elif special_sign == "<":
                before = contents[0 : special_index].strip()
                after = contents[special_index + 1 : len(contents)].strip()
                instructions.extend(parse_statement(after, extra + instructions))
                instructions.extend(parse_statement(before, extra + instructions))
                instructions.append(Invoke("_.<", 2, []))
            elif special_sign == ">":
                before = contents[0 : special_index].strip()
                after = contents[special_index + 1 : len(contents)].strip()
                instructions.extend(parse_statement(after, extra + instructions))
                instructions.extend(parse_statement(before, extra + instructions))
                instructions.append(Invoke("_.>", 2, []))
            elif special_sign == "[]":
                before = contents[0 : special_index].strip()
                after = contents[special_index + 1 : special_index2].strip()
                instructions.extend(parse_statement(after, extra + instructions))
                instructions.extend(parse_statement(before, extra + instructions))
                instructions.append(Invoke("_.[]", 2, []))
            elif special_sign == "[]=":
                before = contents[0 : special_index].strip()
                after = contents[special_index + 1 : special_index2].strip()
                after2 = contents[special_index3 + 1 : len(contents)].strip()
                instructions.extend(parse_statement(after2, extra + instructions))
                instructions.extend(parse_statement(after, extra + instructions))
                instructions.extend(parse_statement(before, extra + instructions))
                instructions.append(Invoke("_.[]=", 3, []))
            elif special_sign == ".":
                before = contents[0 : special_index].strip()
                after = contents[special_index + 1 :].strip()
                instructions.extend(parse_statement(before, extra + instructions))
                instructions.append(Invoke("_" + after, 1, []))
            elif special_sign == ".=":
                before = contents[0 : special_index].strip()
                after = contents[special_index + 1 : special_index2].strip()
                after2 = contents[special_index2 + 1 : len(contents)].strip()
                instructions.extend(parse_statement(after2, extra + instructions))
                instructions.extend(parse_statement(before, extra + instructions))
                instructions.append(Invoke("_" + after + "=", 2, []))
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
                type_parameters = []
                if "<" in name:
                    type_parameters = name[name.index("<") + 1 : name.index(">")].split(",")

                for i in range(0, len(type_parameters)):
                    type_parameters[i] = type_parameters[i].strip()

                if name:
                    arguments = contents[len(name) : ]
                    arguments = arguments[arguments.index("(") + 1 : len(arguments) - 1]

                    argument_count = 0
                    current_parenthesis = 0
                    in_quotations = False
                    for character in arguments:
                        if character == "," and current_parenthesis == 0 and not in_quotations:
                            argument_count += 1
                        elif character == "\"":
                            in_quotations = not in_quotations
                        elif character == "(":
                            current_parenthesis += 1
                        elif character == ")":
                            current_parenthesis -= 1

                    if arguments:
                        argument_count += 1

                    instructions.extend(parse_statement(arguments, extra + instructions))
                    
                    if "." in name:
                        parsed = parse_statement(name[0 : name.rindex(".")], extra + instructions)
                        instructions.extend(parsed)
                        name = "_." + name[name.rindex(".") + 1 : len(name)]

                    if "<" in name:
                        name = name[0 : name.index("<")]
                    instructions.append(Invoke(name, argument_count + (1 if name.startswith("_.") else 0), [], [], type_parameters))
                else:
                    instructions.extend(parse_statement(contents[1 : len(contents) - 1], extra +  instructions))
            else:
                if contents:
                    instructions.append(Retrieve(contents, None))
        
    return instructions
    
internals = [
    Function("@print_size", [], [], ["&any", "integer"], [], []),
    Function("@add", [], [], ["&any", "&any"], ["any"], []),
    Function("@subtract", [], [], ["&any", "&any"], ["any"], []),
    Function("@get_8", [], [], ["&any"], ["integer"], []),
    Function("@set_8", [], [], ["any", "integer"], [], []),
    Function("@allocate", [], [], ["integer"], ["any"], []),
    Function("@free", [], [], ["&any", "integer"], [], []),
    Function("@print_memory", [], [], [], [], []),
    Function("@error_size", [], [], ["&any", "integer"], [], []),
    Function("@read_size", [], [], ["&any", "integer"], [], []),
    Function("@get_1", [], [], ["&any"], ["integer"], []),
    Function("@equal", [], [], ["&any", "&any"], ["boolean"], []),
    Function("@copy", [], [], ["&any", "&any", "integer"], [], []),
    Function("@greater", [], [], ["integer", "integer"], ["boolean"], []),
    Function("@modulo", [], [], ["integer", "integer"], ["integer"], []),
    Function("@divide", [], [], ["integer", "integer"], ["integer"], []),
    Function("@set_1", [], [], ["any", "integer"], [], []),
    Function("@not", [], [], ["boolean"], ["boolean"], []),
    Function("@and", [], [], ["boolean", "boolean"], ["boolean"], []),
    Function("@multiply", [], [], ["integer", "integer"], ["integer"], []),
    Function("@less", [], [], ["integer", "integer"], ["boolean"], []),
    Function("@or", [], [], ["boolean", "boolean"], ["boolean"], []),
    Function("@exit", [], [], [], [], []),
    Function("@execute", [], [], ["&any", "&any", "boolean"], [], []),
    Function("@call_function", [], [], ["&any", "&any", "integer"], ["any"], []),
    Function("@read_file_size", [], [], ["&any", "&any", "integer"], [], []),
    Function("@get_file_size", [], [], ["&any"], ["integer"], [])
]

def create_generic_function(function2, mapped_generics, functions):
    new_function = copy.deepcopy(function2)

    new_function.generics_applied = []
    for generic in mapped_generics:
        for i in range(0, len(new_function.parameters)):
            new_function.parameters[i] = replace_type(new_function.parameters[i], generic, mapped_generics[generic], mapped_generics)

        for i in range(0, len(new_function.return_)):
            new_function.return_[i] = replace_type(new_function.return_[i], generic, mapped_generics[generic], mapped_generics)

        new_function.generics_applied.append(mapped_generics[generic])

    new_function.generics = []
    id = new_function.name + "_" + str(len(new_function.parameters))
    functions.setdefault(id, [])
    functions[id].append(new_function)
    #new_generic_functions[new_function] = copy.deepcopy(mapped_generics)

    return new_function

def apply_mapped_generics(new_function, mapped_generics):
    for generic in mapped_generics:
        for token in new_function.tokens:
            if isinstance(token, Declare):
                token.type = replace_type(token.type, generic, mapped_generics[generic], mapped_generics)
            elif isinstance(token, Retrieve):
                thing = token.name
                token.name = replace_type(token.name, generic, mapped_generics[generic], mapped_generics)
                #print(thing + " " + token.name)
                #print(mapped_generics)
            elif isinstance(token, Invoke):
                if token.name.startswith("@cast_"):
                    token.name = "@cast_" + replace_type(token.name[6:], generic, mapped_generics[generic], mapped_generics)
                elif "::type" in token.name:
                    index = token.name.index("::type")
                    token.name = replace_type(token.name[0 : index], generic, mapped_generics[generic], mapped_generics) + "::type"
                elif "::memory_size" in token.name:
                    index = token.name.index("::memory_size")
                    token.name = replace_type(token.name[0 : index], generic, mapped_generics[generic], mapped_generics) + "::memory_size"
                for i in range(0, len(token.parameters)):
                    token.parameters[i] = replace_type(token.parameters[i], generic, mapped_generics[generic], mapped_generics)
                    
                for i in range(0, len(token.type_parameters)):
                    token.type_parameters[i] = replace_type(token.type_parameters[i], generic, mapped_generics[generic], mapped_generics)

def process_program(program):
    return_value = 0
    
    functions = {}
    functions2 = {}
    program_types = ["integer", "boolean", "any"]
    program_structs = []
    program_enums = []

    for token in list(program.tokens):
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
            program_structs.append(token)
        elif isinstance(token, EnumMarker):
            program_types.append(token.name)
            program_enums.append(token.name)
    
    wanted_generic_functions["Array['any', 'integer']"] = [{"A": "String"}]

    # type checking
    for token in program.tokens:
        if isinstance(token, Function):
            if type_check(token, token.tokens, program_types, program_structs, functions, functions2, True) == 1:
                return_value = 1

    if return_value == 1:
        return 1

    added_generics = []

    if create_generic_functions(program, functions, added_generics, program_types, program_structs, functions2) == 1:
        return 1

    # auto freer
    for function in program.tokens:
        if isinstance(function, Function) and len(function.generics) == 0:
            owned_variables = []
            owned_variable_scopes = {}
            scopes = []
            variable_usages = {}
            variables = {}
            values = {}
            value_usages = {}

            stack = 0
            index_thing = 0

            loops = []
            variable_loops = {}
            loop_errors = {}

            for instruction in list(function.tokens):
                recently_added_usage = ""
                is_cast = False

                if isinstance(instruction, Constant):
                    stack += 1
                    id = "_" + str(index_thing)
                    type = ""
                    if isinstance(instruction.value, bool):
                        type = "boolean"
                    if isinstance(instruction.value, int):
                        type = "integer"
                    if isinstance(instruction.value, str):
                        type = "String"
                    if isinstance(instruction.value, tuple):
                        type = "Function"

                    function.tokens.insert(function.tokens.index(instruction) + 1, Duplicate())
                    function.tokens.insert(function.tokens.index(instruction) + 2, Declare(id, type))
                    function.tokens.insert(function.tokens.index(instruction) + 3, Assign(id))
                    function.locals.append(id)

                    values[id] = type

                    value_usages[stack] = id
                    
                    index_thing += 1
                elif isinstance(instruction, Declare):
                    variables[instruction.name] = instruction.type
                    if function.locals.index(instruction.name) < len(function.parameters):
                        if not instruction.name in owned_variables:
                            owned_variables.append(instruction.name)

                    if not len(scopes) == 0:
                        owned_variable_scopes[instruction.name] = scopes[len(scopes) - 1]
                    else:
                        owned_variable_scopes[instruction.name] = ""
                    
                    if function.locals.index(instruction.name) < len(function.parameters):
                        variable_loops[instruction.name] = ""
                elif isinstance(instruction, Assign):
                    if instruction.name in owned_variables and not variables[instruction.name] in primitives and not variables[instruction.name][0] == "&" and not variables[instruction.name][0] == "?":
                        index = function.tokens.index(instruction)
                        function.tokens.insert(index, Invoke(normalize(variables[instruction.name]) + "::memory_size", 0, [], ["integer"]))
                        function.tokens.insert(index + 1, Retrieve(instruction.name, None))
                        function.tokens.insert(index + 2, Invoke("@free", 2, ["&any", "integer"], []))

                    if not instruction.name in owned_variables:
                        owned_variables.append(instruction.name)

                    if len(loops) > 0:
                        variable_loops[instruction.name] = loops[len(loops) - 1]

                        current_loop = ""
                        if len(loops) > 0:
                            current_loop = loops[len(loops) - 1]

                        if instruction.name in loop_errors and loop_errors[instruction.name] == current_loop:
                            del loop_errors[instruction.name]
                    else:
                        variable_loops[instruction.name] = ""

                    for usage in dict(variable_usages):
                        if variable_usages[usage] == stack:
                            if not (variables[instruction.name][0] == "?" or variables[instruction.name][0] == "&" or variables[usage] in primitives):
                                owned_variables.remove(usage)

                                current_loop = ""
                                if len(loops) > 0:
                                    current_loop = loops[len(loops) - 1]

                                if not variable_loops[usage] == current_loop:
                                    loop_errors[usage] = current_loop

                            del variable_usages[usage]

                    if stack in value_usages:
                        del value_usages[stack]

                    stack -= 1
                elif isinstance(instruction, StartWhile):
                    stack -= 1
                    scopes.append("while_" + str(instruction.id1))
                    loops.append(str(instruction.id1))
                elif isinstance(instruction, EndWhile):
                    loops.pop()

                    id = "while_" + str(instruction.id1)
                    if len(scopes) > 0 and id == scopes[len(scopes) - 1]:
                        scopes.pop()

                        index = function.tokens.index(instruction)
                        for variable in owned_variables:
                            if not variables[variable] in primitives and not variables[variable][0] == "&" and not variables[variable][0] == "?" and not variables[variable] in program_enums:
                                name = function.name
                                if owned_variable_scopes[variable] == id:
                                    function.tokens.insert(index, Invoke(normalize(variables[variable]) + "::memory_size", 0, [], ["integer"]))
                                    function.tokens.insert(index + 1, Retrieve(variable, None))
                                    function.tokens.insert(index + 2, Invoke("@free", 2, ["any", "integer"], []))
                                    index += 3

                elif isinstance(instruction, CheckIf):
                    if instruction.checking:
                        stack -= 1

                    scopes.append("if_" + str(instruction.false_id))
                elif isinstance(instruction, EndIf):
                    id = "if_" + str(instruction.id)
                    if len(scopes) > 0 and id == scopes[len(scopes) - 1]:
                        scopes.pop()

                        index = function.tokens.index(instruction)
                        added = []
                        for variable in owned_variables:
                            if not variables[variable] in primitives and not variables[variable][0] == "&" and not variables[variable][0] == "?" and not variables[variable] in program_enums:
                                name = function.name
                                if variable in owned_variable_scopes and owned_variable_scopes[variable] == id:
                                    function.tokens.insert(index, Invoke(normalize(variables[variable]) + "::memory_size", 0, [], ["integer"]))
                                    function.tokens.insert(index + 1, Retrieve(variable, None))
                                    function.tokens.insert(index + 2, Invoke("@free", 2, ["any", "integer"], []))
                                    index += 3
                                    added.append(variable)
                                    owned_variables.remove(variable)
                    pass
                elif isinstance(instruction, Retrieve):
                    stack += 1

                    if instruction.name in variables:
                        variable_usages[instruction.name] = stack
                        recently_added_usage = instruction.name

                        if not instruction.name in owned_variables:
                            print("PROCESS: Variable " + instruction.name + " in " + function.name + " used while not owned.")
                            return 1

                        index_thing += 1
                elif isinstance(instruction, Invoke):
                    if instruction.name.startswith("@cast_"):
                        is_cast = True
                        
                    post_method_index = function.tokens.index(instruction) + 1

                    id = instruction.name + "_" + str(instruction.parameter_count)
                    cached_types = []

                    if id in functions:
                        named_functions = list(functions[id])
                        function2 = named_functions[0]

                        cached_types = cached_types[::-1]

                        for parameter in instruction.parameters:
                            for usage in dict(variable_usages):
                                if variable_usages[usage] == stack:
                                    if not (parameter[0] == "&" or parameter[0] == "?" or variables[usage] in primitives):
                                        owned_variables.remove(usage)

                                        current_loop = ""
                                        if len(loops) > 0:
                                            current_loop = loops[len(loops) - 1]

                                        if not variable_loops[usage] == current_loop:
                                            loop_errors[usage] = current_loop

                                    del variable_usages[usage]

                            if stack in value_usages and parameter[0] == "&" and not values[value_usages[stack]] in primitives and not values[value_usages[stack]] in program_enums:
                                function.tokens.insert(post_method_index, Invoke(normalize(values[value_usages[stack]]) + "::memory_size", 0, [], ["integer"]))
                                function.tokens.insert(post_method_index + 1, Retrieve(value_usages[stack], None))
                                function.tokens.insert(post_method_index + 2, Invoke("@free", 2, ["any", "integer"], []))
                                post_method_index += 3

                            if stack in value_usages:
                                del value_usages[stack]

                            stack -= 1

                        if len(instruction.return_) > 0:
                            for return_type in instruction.return_:
                                stack += 1

                                if not return_type[0] == "&" and not return_type[0] == "?":
                                    id = "_" + str(index_thing)
                                    type = return_type

                                    mapped_generics = {}
                                    for i in range(0, len(function2.parameters)):
                                        if i < len(cached_types) - 1:
                                            parameter = function2.parameters[i]
                                            input = cached_types[i]

                                            collect_mapped(mapped_generics, parameter, input)


                                    function.tokens.insert(function.tokens.index(instruction) + 1, Duplicate())
                                    function.tokens.insert(function.tokens.index(instruction) + 2, Declare(id, type))
                                    function.tokens.insert(function.tokens.index(instruction) + 3, Assign(id))
                                    function.locals.append(id)

                                    values[id] = type
                                    
                                    value_usages[stack] = id

                                    index_thing += 1

                elif isinstance(instruction, Return):
                    temp_vars = []
                    for usage in variable_usages:
                        if variable_usages[usage] == stack:
                            owned_variables.remove(usage)
                            temp_vars.append(usage)

                    new_list = []
                    index = function.tokens.index(instruction)

                    for variable in owned_variables:
                        if not variables[variable] in primitives and not variables[variable][0] == "&" and not variables[variable][0] == "?":
                            name = function.name
                            if variable in owned_variable_scopes and owned_variable_scopes[variable] == "":
                                function.tokens.insert(index, Invoke(normalize(variables[variable]) + "::memory_size", 0, [], ["integer"]))
                                function.tokens.insert(index + 1, Retrieve(variable, None))
                                function.tokens.insert(index + 2, Invoke("@free", 2, ["any", "integer"], []))
                                index += 3

                    for variable in temp_vars:
                        if not variable in owned_variables:
                            owned_variables.append(variable)

            for error in loop_errors:
                print("PROCESS: Variable " + error + " in " + function.name + " used while not owned (due to a loop).")
                return 1

    # insert free and free_custom (for custom structures)
    for function in program.tokens:
        if isinstance(function, Function):
            types = []
            variables = {}
            variables_realtime = {}
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
                    elif isinstance(instruction.value, tuple):
                        types.append("Function")
                elif isinstance(instruction, CheckIf):
                    if instruction.checking:
                        given_type = types.pop()
                elif isinstance(instruction, StartWhile):
                    given_type = types.pop()
                elif isinstance(instruction, Declare):
                    variables_realtime[instruction.name] = instruction
                    if function.locals.index(instruction.name) < len(function.parameters):
                        variables[instruction.name] = instruction
                elif isinstance(instruction, Duplicate):
                    types.append(types[len(types) - 1])
                elif isinstance(instruction, Assign):
                    given_type = types.pop()
                    if instruction.name in variables:
                        if variables[instruction.name].type == "":
                            variables[instruction.name].type = given_type

                    if instruction.name in variables_realtime:
                        variables[instruction.name] = variables_realtime[instruction.name]
                        del variables_realtime[instruction.name]
                elif isinstance(instruction, Retrieve):
                    if not instruction.name in variables:
                        types.append("unknown")
                    else:
                        types.append(variables[instruction.name].type)

                elif isinstance(instruction, Invoke):
                    if instruction.name.startswith("@cast_"):
                        types.pop()
                        types.append(instruction.name[6:])
                    elif instruction.name.startswith("@free"):
                        free_type = types.pop()
                        if len(types) > 0:
                            types.pop()

                        name = function.name

                        if not free_type in primitives:
                            index = function.tokens.index(instruction)
                            function.tokens.insert(index, Duplicate())
                            index += 1
                            if "_.free_custom_1" in functions:
                                for free_custom in functions["_.free_custom_1"]:
                                    if is_type(free_type, free_custom.parameters[0][1 : ]):
                                        function.tokens.insert(index, Duplicate())
                                        function.tokens.insert(index + 1, Invoke("_.free_custom", 1, [free_type], [], [] if not "<" in free_type else free_type[free_type.index("<") + 1 : free_type.rindex(">")].split(",")))
                                        j += 2
                                        index += 2
                                        break
                            function.tokens.insert(index, Invoke(free_type + ".free", 1, [free_type], []))
                            j += 2
                    elif len(instruction.return_) > 0:
                        id = instruction.name + "_" + str(instruction.parameter_count)
                        if id in functions:
                            cached_types = []
                            named_functions = list(functions[id])
                            function2 = named_functions[0]

                            for i in range(0, instruction.parameter_count):
                                if len(types) > 0:
                                    given_type = types.pop()
                                    cached_types.append(given_type)

                        for type in instruction.return_:
                            mapped_generics = {}
                            for i in range(0, len(function2.parameters)):
                                parameter = function2.parameters[i]
                                input = cached_types[i]

                                collect_mapped(mapped_generics, parameter, input)
                            for generic in mapped_generics:
                                type = replace_type(type, generic, mapped_generics[generic], mapped_generics)

                            if type[0] == "&" and (type[1:] == "boolean" or type[1:] == "integer"):
                                type = type[1:]

                            types.append(type)
                j += 1

    added_functions = []
    for function in program.tokens:
        if isinstance(function, Function):
            id = function.name + str(function.parameters).replace("&", "") + str(function.generics_applied)
            invocation_map[id] = []
            for instruction in function.tokens:
                if isinstance(instruction, Invoke):
                    invocation_map[id].append(instruction.name + str(instruction.parameters).replace("&", "") + str(instruction.type_parameters))
                if isinstance(instruction, Constant) and isinstance(instruction.value, tuple):
                    for function in program.tokens:
                        if isinstance(function, Function) and function.name == instruction.value[0]:
                            invocation_map[id].append(function.name + str(function.parameters).replace("&", "") + str(function.generics))



    for function in list(program.tokens):
        if isinstance(function, Function):
            if not is_used(function, program.tokens) or len(function.generics) > 0 or (function.name + str(function.parameters) + str(function.generics_applied) in added_functions):
                program.tokens.remove(function)
            else:
                added_functions.append(function.name + str(function.parameters) + str(function.generics_applied))
                #if function.name == "Type.free":
                    #for instruction in function.tokens:
                        #if isinstance(instruction, Invoke):
                            #print("Invoke: " + instruction.name + "(" + ",".join(instruction.parameters) + ")" + ",".join(instruction.return_))
                        #elif isinstance(instruction, Assign):
                            #print("Assign: " + instruction.name)
                        #elif isinstance(instruction, Retrieve):
                            #print("Retrieve: " + instruction.name)
                        #elif isinstance(instruction, Declare):
                            #print("Declare: " + instruction.name)
                        #elif isinstance(instruction, Duplicate):
                            #print("Duplicate")
                        #else:
                            #print(instruction)

    return return_value


def create_generic_functions(program, functions, added_generics, program_types, program_structs, functions2):
    return_value = 0
    for function2 in list(program.tokens):
        if isinstance(function2, Function):
            id1 = function2.name + str(function2.parameters)
            #print(id1)

            if id1 in wanted_generic_functions:
                generic_variants = wanted_generic_functions[id1]
                #print(id1 + " " + str(wanted_generic_functions[id1]))
                del wanted_generic_functions[id1]

                id = function2.name + "_" + str(len(function2.parameters))
                #limited_types = ["integer", "boolean", "any", "String", "Function"]
                for generic_variant in generic_variants:
                    #print(function2.name + " " + str(generic_variant))
                    mapped_generics = generic_variant 

                    if len(mapped_generics) > 0:
                        new_function = create_generic_function(function2, mapped_generics, functions)
                        apply_mapped_generics(new_function, mapped_generics)
                        program.tokens.append(new_function)
                        added_generics.append(new_function)
                        #print(new_function.applied_generics)
                        if type_check(new_function, new_function.tokens, program_types, program_structs, functions, functions2, True) == 1:
                            return_value = 1

                        if function2.name + ".free_1" in functions:
                            if len(mapped_generics) > 0:
                                new_function = copy.deepcopy(functions[function2.name + ".free_1"][0])
                                for generic in mapped_generics:
                                    for i in range(0, len(new_function.parameters)):
                                        new_function.parameters[i] = replace_type(new_function.parameters[i], generic, mapped_generics[generic], mapped_generics)
                                    for i in range(0, len(new_function.return_)):
                                        new_function.return_[i] = new_function.return_[i].replace(generic, mapped_generics[generic])

                                program.tokens.append(new_function)
                                new_function.name = new_function.name[0 : new_function.name.index(".")] + ("<" + ",".join(new_function.generics) + ">" if len(new_function.generics) > 0 else "") + ".free"
                                new_function.generics = []
                                for generic in mapped_generics:
                                    new_function.name = replace_type(new_function.name, generic, mapped_generics[generic], mapped_generics)
                                    new_function.generics.append(mapped_generics[generic])

                                new_function.name = new_function.name + ".free"

                                new_function.generics = []
                                apply_mapped_generics(new_function, mapped_generics)
                                added_generics.append(new_function)
                                if type_check(new_function, new_function.tokens, program_types, program_structs, functions, functions2, True) == 1:
                                    return_value = 1

                        if "_.free_custom_1" in functions:
                            flag = False
                            for free_custom in functions["_.free_custom_1"]:
                                if not flag and len(free_custom.generics) > 0 and is_type(function2.name, free_custom.parameters[0][1 : ]):
                                    if len(mapped_generics) > 0:
                                        flag = True
                                        new_function = copy.deepcopy(free_custom)
                                        for generic in mapped_generics:
                                            for i in range(0, len(new_function.parameters)):
                                                new_function.parameters[i] = replace_type(new_function.parameters[i], generic, mapped_generics[generic], mapped_generics)
                                            for i in range(0, len(new_function.return_)):
                                                new_function.return_[i] = replace_type(new_function.return_[i], generic, mapped_generics[generic], mapped_generics)

                                        program.tokens.append(new_function)
                                        new_function.generics_applied = []
                                        for generic in mapped_generics:
                                            new_function.name = replace_type(new_function.name, generic, mapped_generics[generic], mapped_generics)
                                            new_function.generics_applied.append(mapped_generics[generic])

                                        new_function.generics = []
                                        apply_mapped_generics(new_function, mapped_generics)
                                        added_generics.append(new_function)
                                        if type_check(new_function, new_function.tokens, program_types, program_structs, functions, functions2, True) == 1:
                                            return_value = 1

                                        functions[new_function.name + "_" + str(len(new_function.parameters))].append(new_function)

    if len(wanted_generic_functions) > 0:
        if create_generic_functions(program, functions, added_generics, program_types, program_structs, functions2) == 1:
            return_value == 1

    return return_value


invocation_map = {}

def is_used(function, functions):
    if function.name == "main" or (function.name == "String" and function.parameters[0] == "any") or (function.name == "Function" and function.parameters[0] == "any") or function.name == "Function.free" or (function.name == "Array" and function.parameters[0] == "any" and function.parameters[1] == "integer"):
        return True

    for other_function in functions:
        if isinstance(other_function, Function) and function.name + str(function.parameters).replace("&", "") + str(function.generics_applied) in invocation_map[other_function.name + str(other_function.parameters).replace("&", "") + str(other_function.generics_applied)] and not (other_function.name == function.name and other_function.parameters == function.parameters) and is_used(other_function, functions):
            return True

    return False

def normalize(name):
    return name[0 : name.index("<") if "<" in name else len(name)]

def replace_type(type, given, wanted, mapped_generics = {}):
    main = type[0 : type.index("<") if "<" in type else len(type)]
    generics = []
    if "<" in type:
        for generic in type[type.index("<") + 1 : type.index(">")].split(","):
            generics.append(generic)

    #if len(mapped_generics) > 0:
        #print("test")
    if main in mapped_generics or (len(main) > 1 and main[0] == "&" and main[1:] in mapped_generics):
        main = ("&" if main[0] == "&" else "") + wanted

    if len(main) > 0 and main[0] == "&" and main[1:] in primitives and not main[1:] == "any":
        main = main[1:]

    for i in range(0, len(generics)):
        generics[i] = replace_type(generics[i], given, wanted, mapped_generics)

    return main + ("<" + ",".join(generics) + ">" if len(generics) > 0 else "")

def type_check(function, instructions, program_types, program_structs, functions, functions2, alter):
    return_value = 0

    types = []
    variables = {}
    variable_scopes = {}
    scopes = [-1]

    if len(function.generics) > 0:
        return 0

    for token in list(program.tokens):
        if isinstance(token, Function):
            declared = []
            for instruction in token.tokens:
                if isinstance(instruction, Declare):
                    declared.append(instruction.name)
                elif isinstance(instruction, Retrieve):
                    if not instruction.name in declared:
                        if instruction.name in program_types:
                            token.tokens[token.tokens.index(instruction)] = Invoke(instruction.name + "::type", 0, [])
                        elif instruction.name in functions2:
                            token.tokens[token.tokens.index(instruction)] = Constant((instruction.name, functions2[instruction.name].parameters))
    
    for instruction in list(instructions):
        if isinstance(instruction, Constant):
            if isinstance(instruction.value, bool):
                types.append("boolean")
            elif isinstance(instruction.value, int):
                types.append("integer")
            elif isinstance(instruction.value, str):
                types.append("String")
            elif isinstance(instruction.value, tuple):
                types.append("Function")
        elif isinstance(instruction, CheckIf):
            scopes.append(instruction.false_id)
            if instruction.checking:
                if len(types) == 0:
                    print("PROCESS: If in " + function.name + " expects boolean, given nothing.")
                    return 1

                given_type = types.pop()
                if not is_type(given_type, "boolean"):
                    print("PROCESS: If in " + function.name + " expects boolean, given " + given_type + ".")
                    return 1
        elif isinstance(instruction, EndIf):
            if scopes[-1] == instruction.id:
                scopes.pop()
        elif isinstance(instruction, StartBlock):
            scopes.append(instruction.id)
        elif isinstance(instruction, EndBlock):
            if scopes[-1] == instruction.id:
                scopes.pop()
        elif isinstance(instruction, StartWhile):
            scopes.append(instruction.id1)
            if len(types) == 0:
                print("PROCESS: While in " + function.name + " expects boolean, given nothing.")
                return 1

            given_type = types.pop()
            if not is_type(given_type, "boolean"):
                print("PROCESS: While in " + function.name + " expects boolean, given " + given_type + ".")
                return 1
        elif isinstance(instruction, EndWhile):
            if scopes[-1] == instruction.id1:
                scopes.pop()
        elif isinstance(instruction, Declare):
            variables[instruction.name] = instruction
            variable_scopes[instruction.name] = scopes[-1]
            name = variables[instruction.name].type
            name_bare = name[0 : name.index("<") if "<" in name else len(name)]

            if len(name_bare) > 0 and name_bare[0] == "&":
                name_bare = name_bare[1:]

            given_type_parameters = [] if not "<" in name else name[name.index("<") + 1 : name.index(">")].split(",")
            for struct in program_structs:
                if struct.name == name_bare and not len(given_type_parameters) == len(struct.generics):
                    if not len(given_type_parameters) == len(struct.generics):
                        print("PROCESS: Type " + name_bare + " in " + function.name + " expects " + str(len(struct.generics)) + " type parameters, given " + str(len(given_type_parameters)) + ".")
                        return 1

            for type_parameter in given_type_parameters:
                if len(type_parameter) == 1:
                    print("PROCESS: Type " + name_bare + " in " + function.name + " uses undeclared generic " + type_parameter + ".")
                    return 1
                            
        elif isinstance(instruction, Assign):
            if len(types) == 0:
                print("PROCESS: Assign of " + instruction.name + " in " + function.name + " expects " + (variables[instruction.name].type if variables[instruction.name].type else "a value") + ", given nothing.")
                return 1
            
            given_type = types.pop()

            if not instruction.name in variables:
                print("PROCESS: Variable " + instruction.name + " in " + function.name + " not found.")
                return 1

            if variables[instruction.name].type == "":
                variables[instruction.name].type = given_type

            if not is_type(given_type, variables[instruction.name].type):
                print("PROCESS: Assign of " + instruction.name + " in " + function.name + " expects " + variables[instruction.name].type + ", given " + given_type + ".")
                return 1
        elif isinstance(instruction, Retrieve):
            if not instruction.name in variables or not variable_scopes[instruction.name] in scopes:
                print("PROCESS: Variable " + instruction.name + " in " + function.name + " not found.")
                return 1
            types.append(variables[instruction.name].type)
        elif isinstance(instruction, Duplicate):
            top = types.pop()
            types.append(top)
            types.append(top)
        elif isinstance(instruction, Invoke):
            if instruction.name.startswith("@cast_") and ((instruction.name[6 : instruction.name.index("<") if "<" in instruction.name else len(instruction.name)] in program_types) or (instruction.name[7 : instruction.name.index("<") if "<" in instruction.name else len(instruction.name)] in program_types)):
                name = instruction.name[6 : len(instruction.name)]

                if len(types) == 0:
                    print("PROCESS: Cast in " + function.name + " expects a value, given none.")
                    return 1

                given_type = types.pop()
                given_type_stripped = given_type.replace("&", "")
                name_stripped = name.replace("&", "")
                if ((given_type[0] == "&" and not name[0] == "&" and not name in primitives) or (not name_stripped == "any" and not given_type_stripped == "any")) and (given_type_stripped == name_stripped and given_type == name):
                    print("PROCESS: Attempted to cast in " + function.name + " from " + given_type + " to " + name + ".")
                    return 1
                
                given_type_parameters = instruction.type_parameters
                for struct in program_structs:
                    if (struct.name == name or struct.name == name[1:]) and not len(given_type_parameters) == len(struct.generics):
                        print("PROCESS: Type " + name + " in " + function.name + " expects " + str(len(struct.generics)) + " type parameters, given " + str(len(given_type_parameters)) + " (in cast).")
                        return 1
                types.append(instruction.name[6 : len(instruction.name)] + ("" if len(instruction.type_parameters) == 0 else "<" + ",".join(instruction.type_parameters)  + ">"))
            else:
                id = instruction.name + "_" + str(instruction.parameter_count)

                if not id in functions:
                    print("PROCESS: Function " + instruction.name + " with " + str(instruction.parameter_count) + " parameters in " + function.name + " not defined.")
                    return 1

                named_functions = list(functions[id])
                for function12 in list(named_functions):
                    if len(function12.generics_applied) > 0:
                        named_functions.remove(function12)

                function2 = named_functions[0]

                cached_types = []
                #print("-----")

                i = 0
                while i < instruction.parameter_count:
                    if len(types) == 0:
                        print("PROCESS: Invoke of " + instruction.name + " in " + function.name + " expects " + function2.parameters[i] + " as a parameter, given nothing.")
                        return 1

                    given_type = types.pop()
                    cached_types.append(given_type)

                    for function3 in list(named_functions):
                        if not is_type(given_type, function3.parameters[i], function3.generics):
                            named_functions.remove(function3)

                    if len(named_functions) == 0:
                        print("PROCESS: Invoke of " + instruction.name + " in " + function.name + " expects " + function2.parameters[i] + " as a parameter, given " + given_type + ".")
                        return 1


                    function2 = named_functions[0]

                    i += 1
                    
                cached_types = cached_types[::-1]

                #if function2.name == "_.[]=" and function.name == "main":
                    #print(str(named_functions) + " " + str(cached_types))

                if len(named_functions) > 1:
                    for function5 in list(named_functions):
                        if len(function5.generics) < len(instruction.type_parameters):
                            named_functions.remove(function5)
                        for i in range(0, len(function5.generics_applied)):
                            if len(instruction.type_parameters) > i:
                                if not function5.generics_applied[i] == instruction.type_parameters[i]:
                                    named_functions.remove(function5)

                if len(named_functions) > 1:
                    for i in range(0, instruction.parameter_count):
                        cached_types2 = list(cached_types)
                        given_type = cached_types2.pop()
                        for function3 in named_functions:
                            if ((not given_type == function3.parameters[i] and not given_type == function3.parameters[i][1::]) or len(function3.generics) > 0) and len(named_functions) > 1:
                                named_functions.remove(function3)

                function2 = named_functions[0]

                #if function.name == "main":
                    #print(function2.parameters)

                set_params = False
                if len(instruction.parameters) == 0:
                    set_params = True
                else:
                    for i in range(0, len(instruction.parameters)):
                        if not is_type(instruction.parameters[i], function2.parameters[i]) or "any" in function2.parameters[i]:
                            set_params = True

                if set_params:
                    instruction.parameters = list(function2.parameters)

                instruction.return_ = function2.return_

                cached_types = cached_types[::-1]
                mapped_previous = {}
                mapped = {}
                for i in range(0, len(function2.parameters)):
                    mapped_previous = dict(mapped)
                    mapped.update(get_mapped_type(cached_types[i], function2.parameters[i], function2.generics))
                    for item in mapped_previous:
                        if not mapped[item] == mapped_previous[item]:
                            print("PROCESS: Invoke of " + function2.name + " in " + function.name + " has conflicting type parameters.")

                for i in range(0, len(instruction.type_parameters)):
                    mapped[function2.generics[i]] = instruction.type_parameters[i]

                if len(function2.generics) > 0:
                    for i in range(0, len(instruction.parameters)):
                        for key in mapped:
                            instruction.parameters[i] = replace_type(instruction.parameters[i], key, mapped[key], mapped)

                    add_to_generic_functions(instruction.name, function2.parameters, mapped)

                    instruction.type_parameters = []
                    for generic in function2.generics:
                        if generic in mapped:
                            instruction.type_parameters.append(mapped[generic])

                if not len(function2.generics) == len(mapped):
                    print("PROCESS: Invoke of " + function2.name + " in " + function.name + " cannot resolve type parameters.")
                    return 1


                if len(function2.return_) > 0:
                    for type in function2.return_[::-1]:
                        for key in mapped:
                            type = replace_type(type, key, mapped[key], mapped)
                        types.append(type)

        elif isinstance(instruction, Return):
            for return_type in function.return_:
                if len(types) == 0:
                    print("PROCESS: Return in " + function.name + " expects " + return_type + ", given nothing.")
                    return 1

                given_type = types.pop()
                if not is_type(given_type, return_type):
                    print("PROCESS: Return in " + function.name + " expects " + return_type + ", given " + given_type + ".")
                    return 1

            if not len(types) == 0:
                print("PROCESS: Return in " + function.name + " has data in stack.")
                return 1

    if len(types) > 0:
        return types.pop()

wanted_generic_functions = {}

def add_to_generic_functions(name, generic_parameters, mapped_generics):
    id = name + str(generic_parameters)
    if not id in wanted_generic_functions:
        wanted_generic_functions[id] = [] 

    wanted_generic_functions[id].append(mapped_generics)

    
def collect_mapped(mapped_generics, parameter, input):
    parameter = parameter.replace("&", "")
    input = input.replace("&", "")

    parameter_main = parameter[0 : parameter.index("<") if "<" in parameter else len(parameter)]
    input_main = input[0 : input.index("<") if "<" in input else len(input)]

    if len(parameter_main) == 1:
        mapped_generics[parameter_main] = input_main

    if "<" in parameter and "<" in input:
        parameter_generics = parameter[parameter.index("<") + 1 : parameter.rindex(">")].split(",")
        input_generics = input[input.index("<") + 1 : input.rindex(">")].split(",")

        for i in range(0, len(parameter_generics)):
            collect_mapped(mapped_generics, parameter_generics[i], input_generics[i])

def is_type(given, wanted, generics = []):
    if wanted == "any" and not given[0] == "&":
        return True

    if wanted[0] == "?" and given == "any":
        return True

    if (wanted[0] == "&" or wanted[0] == "?") and (wanted[1 : len(wanted)] == given or wanted[1:] == "any"):
        return True

    if wanted in generics or ((wanted[0] == "&" or wanted[0] == "?") and wanted[1:] in generics):
        return True

    if "<" in wanted and "<" in given:
        main_wanted = wanted[0 : wanted.index("<")]
        main_given = given[0 : given.index("<")]

        good = True
        if not main_given == main_wanted and not main_given == main_wanted[1:]:
            good = False

        types_wanted = wanted[wanted.index("<") + 1 : wanted.rindex(">")].split(",")
        types_given = given[given.index("<") + 1 : given.rindex(">")].split(",")

        if len(types_wanted) == len(types_given):
            for i in range(0, len(types_wanted)):
                if not is_type(types_given[i], types_wanted[i], generics):
                    good = False
        else:
            good = False

        return good

    main_wanted = wanted[0 : wanted.index("<") if "<" in wanted else len(wanted)]
    main_given = given[0 : given.index("<") if "<" in given else len(given)]

    return main_given == main_wanted or ((main_wanted[0] == "&" or main_wanted[0] == "?") and main_given == main_wanted[1:]) or ((main_wanted[0] == "&" or main_wanted[0] == "?") and (main_given[0] == "&" or main_given[0] == "?") and main_given[1:] == main_wanted[1:])


def get_mapped_type(given, wanted, generics = []):
    mapped = {}

    if "<" in wanted and "<" in given:
        main_wanted = wanted[0 : wanted.index("<")]
        main_given = given[0 : given.index("<")]

        good = True
        if not main_given == main_wanted and not main_given == main_wanted[1:]:
            good = False

        types_wanted = wanted[wanted.index("<") + 1 : wanted.rindex(">")].split(",")
        types_given = given[given.index("<") + 1 : given.rindex(">")].split(",")

        for i in range(0, len(types_wanted)):
            mapped.update(get_mapped_type(types_given[i], types_wanted[i], generics))

    main_wanted = wanted[0 : wanted.index("<") if "<" in wanted else len(wanted)]
    main_given = given[0 : given.index("<") if "<" in given else len(given)]

    if main_wanted in generics or (main_wanted[0] == "&" and main_wanted[1:] in generics):
        mapped[main_wanted.replace("&", "")] = main_given.replace("&", "")

    return mapped

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

    print_size = AsmFunction("@print_size_any~integer_", [])
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

    error_size = AsmFunction("@error_size_any~integer_", [])
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
    _start.instructions.append("mov rax, 12")
    _start.instructions.append("mov rdi, 0")
    _start.instructions.append("syscall") # rax not holds current brk
    _start.instructions.append("mov rbx, rax")
    _start.instructions.append("mov rdi, rbx")
    _start.instructions.append("add rdi, 16384")
    _start.instructions.append("mov rax, 12")
    _start.instructions.append("syscall") # rax with brk, pointing to 16376 of free memory
    _start.instructions.append("mov qword [memory], rbx")
    _start.instructions.append("mov qword [rbx+8], 16384")
    _start.instructions.append("mov rax, [rbp+8]")
    _start.instructions.append("sub rax, 1")
    _start.instructions.append("mov rcx, rax")
    _start.instructions.append("mov rdx, 8")
    _start.instructions.append("mul rdx")
    _start.instructions.append("push rcx")
    _start.instructions.append("push rax")
    _start.instructions.append("call @allocate_integer_")
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
    _start.instructions.append("push r8")
    _start.instructions.append("push r10")
    _start.instructions.append("push rcx")
    _start.instructions.append("push rdx")
    _start.instructions.append("push rbx")
    _start.instructions.append("push r9")
    _start.instructions.append("call String_any_")
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
    _start.instructions.append("mov r11, r8")
    _start.instructions.append("push rcx")
    _start.instructions.append("push r11")
    _start.instructions.append("call Array_any~integer_String")
    _start.instructions.append("add rsp, 16")
    _start.instructions.append("push r8")
    #_start.instructions.append("call @print_memory__")
    _start.instructions.append("call main")
    #_start.instructions.append("call @print_memory__")
    _start.instructions.append("mov rax, 60")
    _start.instructions.append("xor rdi, rdi")
    _start.instructions.append("syscall")
    asm_program.functions.append(_start)

    add = AsmFunction("@add_any~any_", [])
    add.instructions.append("push rbp")
    add.instructions.append("mov rbp, rsp")
    add.instructions.append("mov r8, [rbp+16]")
    add.instructions.append("add r8, [rbp+24]")
    add.instructions.append("mov rsp, rbp")
    add.instructions.append("pop rbp")
    add.instructions.append("ret")
    asm_program.functions.append(add)

    multiply = AsmFunction("@multiply_integer~integer_", [])
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

    subtract = AsmFunction("@subtract_any~any_", [])
    subtract.instructions.append("push rbp")
    subtract.instructions.append("mov rbp, rsp")
    subtract.instructions.append("mov r8, [rbp+16]")
    subtract.instructions.append("sub r8, [rbp+24]")
    subtract.instructions.append("mov rsp, rbp")
    subtract.instructions.append("pop rbp")
    subtract.instructions.append("ret")
    asm_program.functions.append(subtract)

    divide = AsmFunction("@divide_integer~integer_", [])
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

    modulo = AsmFunction("@modulo_integer~integer_", [])
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

    allocate = AsmFunction("@allocate_integer_", [])
    allocate.instructions.append("push rbp")
    allocate.instructions.append("mov rbp, rsp")
    allocate.instructions.append("mov rbx, [rbp+16]") # rbx = allocated size
    allocate.instructions.append("mov r12, rbx")

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
    allocate.instructions.append("mov r9, memory")
    allocate.instructions.append("allocate_mark:") # used for jumping back if the memory block is not big enough
    
    allocate.instructions.append("cmp rcx, 0")
    allocate.instructions.append("jne no_alloc")
    allocate.instructions.append("push rax")
    allocate.instructions.append("push rbx")

    allocate.instructions.append("mov r11, 16384")
    allocate.instructions.append("cmp rbx, r11")
    allocate.instructions.append("jle no_special_case")
    allocate.instructions.append("mov r11, rbx")
    allocate.instructions.append("add r11, 16")

    allocate.instructions.append("no_special_case:")

    allocate.instructions.append("mov rax, 12")
    allocate.instructions.append("mov rdi, 0")
    allocate.instructions.append("push r11")
    allocate.instructions.append("syscall")
    allocate.instructions.append("pop r11")
    allocate.instructions.append("mov rbx, rax")

    allocate.instructions.append("mov rdi, rbx")
    allocate.instructions.append("add rdi, r11")
    allocate.instructions.append("mov rax, 12")
    allocate.instructions.append("push r11")
    allocate.instructions.append("syscall")
    allocate.instructions.append("pop r11")
    allocate.instructions.append("mov qword [r9], rbx")
    #allocate.instructions.append("sub r11, 16")
    allocate.instructions.append("mov qword [rbx+8], r11")
    allocate.instructions.append("mov rcx, rbx")

    allocate.instructions.append("pop rbx")
    allocate.instructions.append("pop rax")

    allocate.instructions.append("no_alloc:")
    
    #allocate.instructions.append("mov rax, memory")
    allocate.instructions.append("mov rax, rcx") # now rax stores beginning of new free memory

    allocate.instructions.append("mov r11, [rax+8]") # r11 stores the size of the free memory block
    allocate.instructions.append("mov r12, rbx")
    allocate.instructions.append("add r12, 16")

    allocate.instructions.append("cmp r12, r11")

    allocate.instructions.append("jle allocate_done")
    allocate.instructions.append("mov r9, rcx") # r9 stores the previous location used
    allocate.instructions.append("mov rcx, [rax]")

    allocate.instructions.append("jmp allocate_mark")
    allocate.instructions.append("allocate_done:")
    allocate.instructions.append("mov r10, rcx") # rcx = location
    allocate.instructions.append("add r10, rbx") # rbx = size, r10 = location + size
    #allocate.instructions.append("add r9, memory")
    allocate.instructions.append("sub r11, rbx") # r11 now with new length
    allocate.instructions.append("cmp r11, 16")
    allocate.instructions.append("jge not_zero")

    allocate.instructions.append("mov rdi, [rax]")
    allocate.instructions.append("mov [r9], rdi") # store next in previous location's next

    allocate.instructions.append("jmp done")
    allocate.instructions.append("not_zero:")

    allocate.instructions.append("mov [r9], r10") # store location + size in the previous location's next
    #allocate.instructions.append("add r10, memory")
    allocate.instructions.append("mov r9, [rax]")
    allocate.instructions.append("mov qword [r10], r9") # store at location + size = the next location
    allocate.instructions.append("mov [r10+8], r11") # store length in location + size + 8

    allocate.instructions.append("done:")
    
    allocate.instructions.append("mov r8, rcx") # move the index of the memory into r8
    #allocate.instructions.append("add r8, memory") # make the value an actually relevant memory value
    allocate.instructions.append("sub rbx, 16")
    allocate.instructions.append("mov rcx, 0")
    allocate.instructions.append("allocate_zero:")
    allocate.instructions.append("cmp rcx, rbx")
    allocate.instructions.append("je allocate_zero_done")
    allocate.instructions.append("mov r9, r8")
    allocate.instructions.append("add r9, rcx")
    allocate.instructions.append("mov qword [r9], 0")
    allocate.instructions.append("add rcx, 8")
    allocate.instructions.append("jmp allocate_zero")
    allocate.instructions.append("allocate_zero_done:")

    allocate.instructions.append("mov rsp, rbp")
    allocate.instructions.append("pop rbp")
    allocate.instructions.append("ret")
    asm_program.functions.append(allocate)

    free = AsmFunction("@free_any~integer_", [])
    free.instructions.append("push rbp")
    free.instructions.append("mov rbp, rsp")
    #free.instructions.append("mov rdi, [rbp+16]")
    #free.instructions.append("call print_integer_space")
    #free.instructions.append("mov rdi, [rbp+24]")
    #free.instructions.append("call @print_integer_integer_")

    free.instructions.append("mov rbx, [rbp+24]") # length
    free.instructions.append("cmp rbx, 0")
    free.instructions.append("jne _continue_free")
    #free.instructions.append("mov rdi, 999999")
    #free.instructions.append("call @print_integer_integer_")
    free.instructions.append("mov rsp, rbp")
    free.instructions.append("pop rbp")
    free.instructions.append("ret")
    free.instructions.append("_continue_free:")
    free.instructions.append("mov rax, [rbp+16]") # rax is the pointer to freed memory
    free.instructions.append("mov r9, rax") # r9 = freed_head
    free.instructions.append("mov rcx, [memory]") # rcx stores the pointed head (before free)
    free.instructions.append("mov [rax], rcx") # now we store the head as our next memory slot
    free.instructions.append("mov r11, rbx")
    
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
    #free.instructions.append("sub rax, memory")
    free.instructions.append("mov [memory], rax") # set new head to our location
    
    #free.instructions.append("add rax, memory")
    free.instructions.append("add rax, rbx") # rax = freed_tail
    free.instructions.append("mov rcx, memory") # rcx = previous_current_check
    free.instructions.append("mov rdx, [memory]") # rdx = current_check
    free.instructions.append("free_loop:")
    
    free.instructions.append("cmp rdx, 0")
    free.instructions.append("je free_done")
    free.instructions.append("mov rbx, rdx")
    #free.instructions.append("add rbx, memory")

    free.instructions.append("cmp rbx, rax") # if (current_check == freed_tail)

    free.instructions.append("jne free_done_if")

    free.instructions.append("mov r10, [rax+8]") # add length of the second segment to this segment's length
    free.instructions.append("add [r9+8], r10")

    free.instructions.append("push rdx")
    free.instructions.append("push rbx")
    free.instructions.append("push rcx")

    #free.instructions.append("add rcx, memory")
    #free.instructions.append("add rdx, memory")
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

    free.instructions.append("mov r11, memory")
    free.instructions.append("before_loop:")
    #free.instructions.append("add r11, memory")
    free.instructions.append("mov r12, [r11]")
    #free.instructions.append("sub r11, memory")
    #free.instructions.append("add r12, memory")
    
    free.instructions.append("cmp r12, r9")
    free.instructions.append("jne not_pointing")

    free.instructions.append("mov rcx, [r12]")
    free.instructions.append("mov [r11], rcx")

    free.instructions.append("not_pointing:")

    #free.instructions.append("add r11, memory")
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
    #free.instructions.append("add rdx, memory")
    free.instructions.append("mov rdx, [rdx]")
    free.instructions.append("jmp free_loop")

    free.instructions.append("free_done:")
    free.instructions.append("mov rsp, rbp")
    free.instructions.append("pop rbp")
    free.instructions.append("ret")
    asm_program.functions.append(free)

    print_memory = AsmFunction("@print_memory__", [])
    print_memory.instructions.append("push rbp")
    print_memory.instructions.append("mov rbp, rsp")
    print_memory.instructions.append("add rbp, 8")

    print_memory.instructions.append("mov rax, [memory]")

    print_memory.instructions.append("loop_thing:")

    #print_memory.instructions.append("add rax, memory")

    print_memory.instructions.append("push rbx")
    print_memory.instructions.append("push rcx")
    print_memory.instructions.append("push r9")
    print_memory.instructions.append("push rax")
    print_memory.instructions.append("push r11")
    print_memory.instructions.append("mov rdi, rax")
    #print_memory.instructions.append("sub rdi, memory")
    #print_memory.instructions.append("call print_integer_space")
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
    #print_memory.instructions.append("call print_integer")
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

    copy = AsmFunction("@copy_any~any~integer_", [])
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

    or_ = AsmFunction("@or_boolean~boolean_", [])
    or_.instructions.append("push rbp")
    or_.instructions.append("mov rbp, rsp")
    or_.instructions.append("mov r8, [rbp+16]")
    or_.instructions.append("or r8, [rbp+24]")
    or_.instructions.append("mov rsp, rbp")
    or_.instructions.append("pop rbp")
    or_.instructions.append("ret")
    asm_program.functions.append(or_)

    and_ = AsmFunction("@and_boolean~boolean_", [])
    and_.instructions.append("push rbp")
    and_.instructions.append("mov rbp, rsp")
    and_.instructions.append("mov r8, [rbp+16]")
    and_.instructions.append("and r8, [rbp+24]")
    and_.instructions.append("mov rsp, rbp")
    and_.instructions.append("pop rbp")
    and_.instructions.append("ret")
    asm_program.functions.append(and_)

    not_ = AsmFunction("@not_boolean_", [])
    not_.instructions.append("push rbp")
    not_.instructions.append("mov rbp, rsp")
    not_.instructions.append("mov r8, [rbp+16]")
    not_.instructions.append("xor r8, 1")
    not_.instructions.append("mov rsp, rbp")
    not_.instructions.append("pop rbp")
    not_.instructions.append("ret")
    asm_program.functions.append(not_)

    equal = AsmFunction("@equal_any~any_", [])
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

    less = AsmFunction("@less_integer~integer_", [])
    less.instructions.append("push rbp")
    less.instructions.append("mov rbp, rsp")
    less.instructions.append("mov r8, [rbp+16]")
    less.instructions.append("cmp r8, [rbp+24]")
    less.instructions.append("jae less_not_less")
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

    greater = AsmFunction("@greater_integer~integer_", [])
    greater.instructions.append("push rbp")
    greater.instructions.append("mov rbp, rsp")
    greater.instructions.append("mov r8, [rbp+16]")
    greater.instructions.append("cmp r8, qword [rbp+24]")
    greater.instructions.append("jbe greater_not_greater")
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

    set_1 = AsmFunction("@set_1_any~any_", [])
    set_1.instructions.append("push rbp")
    set_1.instructions.append("mov rbp, rsp")
    set_1.instructions.append("mov r8, [rbp+24]")
    set_1.instructions.append("mov r9, [rbp+16]")
    set_1.instructions.append("mov [r9], r8b")
    set_1.instructions.append("mov rsp, rbp")
    set_1.instructions.append("pop rbp")
    set_1.instructions.append("ret")
    asm_program.functions.append(set_1)

    set_8 = AsmFunction("@set_8_any~any_", [])
    set_8.instructions.append("push rbp")
    set_8.instructions.append("mov rbp, rsp")
    set_8.instructions.append("mov r8, [rbp+24]")
    set_8.instructions.append("mov r9, [rbp+16]")
    set_8.instructions.append("mov [r9], r8")
    set_8.instructions.append("mov rsp, rbp")
    set_8.instructions.append("pop rbp")
    set_8.instructions.append("ret")
    asm_program.functions.append(set_8)

    get = AsmFunction("@get_1_any_", [])
    get.instructions.append("push rbp")
    get.instructions.append("mov rbp, rsp")
    get.instructions.append("mov r9, [rbp+16]")
    get.instructions.append("mov r8, 0")
    get.instructions.append("mov r8b, [r9]")
    get.instructions.append("mov rsp, rbp")
    get.instructions.append("pop rbp")
    get.instructions.append("ret")
    asm_program.functions.append(get)

    get = AsmFunction("@get_8_any_", [])
    get.instructions.append("push rbp")
    get.instructions.append("mov rbp, rsp")
    get.instructions.append("mov r9, [rbp+16]")
    get.instructions.append("mov r8, [r9]")
    get.instructions.append("mov rsp, rbp")
    get.instructions.append("pop rbp")
    get.instructions.append("ret")
    asm_program.functions.append(get)

    read_size = AsmFunction("@read_size_any~integer_", [])
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

    exit = AsmFunction("@exit__", [])
    exit.instructions.append("mov rax, 60")
    exit.instructions.append("xor rdi, rdi")
    exit.instructions.append("syscall")
    asm_program.functions.append(exit)

    execute = AsmFunction("@execute_any~any~boolean_", [])
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

    call_function = AsmFunction("@call_function_any~any~integer_", [])
    call_function.instructions.append("push rbp")
    call_function.instructions.append("mov rbp, rsp")
    call_function.instructions.append("mov r9, [rbp+16]")
    call_function.instructions.append("mov rax, 8")
    call_function.instructions.append("xor rdx, rdx")
    call_function.instructions.append("mul qword [rbp+32]")
    call_function.instructions.append("add rax, [rbp+24]")
    call_function.instructions.append("mov rdx, [rbp+24]")
    call_function.instructions.append("_call_function_not_done:")
    call_function.instructions.append("cmp rdx, rax")
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

    read_file = AsmFunction("@read_file_size_any~any~integer_", [])
    read_file.instructions.append("push rbp")
    read_file.instructions.append("mov rbp, rsp")
    read_file.instructions.append("mov rdi, [rbp+16]")
    read_file.instructions.append("mov rsi, [rbp+24]")
    read_file.instructions.append("mov rdx, [rbp+32]")
    read_file.instructions.append("mov rax, 0")
    read_file.instructions.append("syscall")
    read_file.instructions.append("mov rsp, rbp")
    read_file.instructions.append("pop rbp")
    read_file.instructions.append("ret")
    asm_program.functions.append(read_file)

    open_file = AsmFunction("@open_file_any_", [])
    open_file.instructions.append("push rbp")
    open_file.instructions.append("mov rbp, rsp")
    open_file.instructions.append("mov rdi, [rbp+16]")
    open_file.instructions.append("xor rsi, rsi")
    open_file.instructions.append("xor rdx, rdx")
    open_file.instructions.append("mov rax, 2")
    open_file.instructions.append("syscall")
    open_file.instructions.append("mov r8, rax")
    open_file.instructions.append("mov rsp, rbp")
    open_file.instructions.append("pop rbp")
    open_file.instructions.append("ret")
    asm_program.functions.append(open_file)

    close_file = AsmFunction("@close_file_any_", [])
    close_file.instructions.append("push rbp")
    close_file.instructions.append("mov rbp, rsp")
    close_file.instructions.append("mov rdi, [rbp+16]")
    close_file.instructions.append("mov rax, 3")
    close_file.instructions.append("syscall")
    close_file.instructions.append("mov rsp, rbp")
    close_file.instructions.append("pop rbp")
    close_file.instructions.append("ret")
    asm_program.functions.append(close_file)

    get_file_size = AsmFunction("@get_file_size_any_", [])
    get_file_size.instructions.append("push rbp")
    get_file_size.instructions.append("mov rbp, rsp")
    get_file_size.instructions.append("push 144")
    get_file_size.instructions.append("call @allocate_integer_")
    get_file_size.instructions.append("mov r9, r8")
    get_file_size.instructions.append("mov rdi, [rbp+16]")
    get_file_size.instructions.append("mov rsi, r9")
    get_file_size.instructions.append("mov rax, 5")
    get_file_size.instructions.append("syscall")
    get_file_size.instructions.append("mov r8, [r9+48]")
    get_file_size.instructions.append("push 144")
    get_file_size.instructions.append("push r9")
    get_file_size.instructions.append("call @free_any~integer_")
    get_file_size.instructions.append("mov rsp, rbp")
    get_file_size.instructions.append("pop rbp")
    get_file_size.instructions.append("ret")
    asm_program.functions.append(get_file_size)

    random = AsmFunction("@random_integer_", [])
    random.instructions.append("push rbp")
    random.instructions.append("mov rbp, rsp")
    random.instructions.append("push qword [rbp+16]")
    random.instructions.append("call @allocate_integer_")
    random.instructions.append("mov rdx, r8")
    random.instructions.append("push rdx")
    random.instructions.append("push qword [rbp+16]")
    random.instructions.append("push rdx")
    random.instructions.append("push random")
    random.instructions.append("call @read_file_size_any~any~integer_")
    random.instructions.append("add rsp, 24")
    random.instructions.append("pop rdx")
    random.instructions.append("mov r8, rdx")
    random.instructions.append("mov rsp, rbp")
    random.instructions.append("pop rbp")
    random.instructions.append("ret")
    asm_program.functions.append(random)
    
    functions = ["_start", "@print_memory__", "@read_file_size_any~any~integer_"]
    for token in program.tokens:
        if isinstance(token, Function):
            for instruction in token.tokens:
                if isinstance(instruction, Invoke):
                    functions.append(instruction.name + "_" + "~".join(instruction.parameters).replace("&", "") + "_")
                    
    for function in list(asm_program.functions):
        if not function.name in functions:
            asm_program.functions.remove(function)

    index_thing = 0
    
    def get_asm_name(name):
        bad = "+=%/*<>!-[],:"
        new_name = ""
        for letter in name:
            if letter in bad:
                new_name += str(ord(letter))
            elif letter == "&":
                pass
            else:
                new_name += letter
        return new_name

    program_types = []
    for token in program.tokens:
        if isinstance(token, StructMarker) or isinstance(token, EnumMarker):
            program_types.append(token.name)

    if_id_binary = 0
    for token in program.tokens:
        if isinstance(token, Function) and len(token.tokens) > 0:
            #print(token.name + " " + str(token.tokens))
            if_id_binary += if_id
            asm_function = AsmFunction("main" if token.name == "main" else get_asm_name(token.name + "_" + "~".join(token.parameters).replace("&", "") + "_" + "~".join(token.generics_applied)), [])
            
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

                        asm_function.instructions.append("push 1")
                        asm_function.instructions.append("push " + str(0 if not put_string else len(put_string.split(","))))
                        asm_function.instructions.append("push qword " + name)
                        asm_function.instructions.append("call String_any~integer~boolean_")
                        asm_function.instructions.append("add rsp, 24")
                        asm_function.instructions.append("push r8")

                        if not put_string:
                            put_string = "0x0"

                        asm_program.data.append(AsmData(name, put_string))
                    elif isinstance(instruction.value, tuple):
                        asm_function.instructions.append("push " + instruction.value[0] + "_" + "~".join(instruction.value[1]).replace("&", "") + "_")
                        asm_function.instructions.append("call Function_any_")
                        asm_function.instructions.append("add rsp, 8")
                        asm_function.instructions.append("push r8")
                elif isinstance(instruction, Invoke) and not instruction.name.startswith("@cast_"):
                    asm_function.instructions.append("call " + get_asm_name(instruction.name + "_" + "~".join(instruction.parameters).replace("&", "") + "_" + "~".join(instruction.type_parameters)))
                    asm_function.instructions.append("add rsp, " + str(instruction.parameter_count * 8))
                    for i in range(len(instruction.return_) - 1, -1, -1):
                        asm_function.instructions.append("push r" + str(8 + i))
                elif isinstance(instruction, Duplicate):
                    asm_function.instructions.append("pop r8")
                    asm_function.instructions.append("push r8")
                    asm_function.instructions.append("push r8")
                elif isinstance(instruction, Assign):
                    asm_function.instructions.append("pop r8")
                    index = token.locals.index(instruction.name)
                    if index <= len(token.parameters) - 1:
                        index -= 2
                    asm_function.instructions.append("mov [rbp" + "{:+d}".format(-index * 8 - 8 + 8 * len(token.parameters)) + "], r8")
                elif isinstance(instruction, Retrieve):
                    index = token.locals.index(instruction.name)
                    if index <= len(token.parameters) - 1:
                        index -= 2
                    asm_function.instructions.append("push qword [rbp" + "{:+d}".format(-index * 8 - 8 + 8 * len(token.parameters)) + "]")
                elif isinstance(instruction, Return):
                    for i in range(0, instruction.value_count):
                        asm_function.instructions.append("pop r" + str(8 + i))

                    asm_function.instructions.append("mov rsp, rbp")
                    asm_function.instructions.append("pop rbp")
                    asm_function.instructions.append("ret")
                elif isinstance(instruction, PreCheckIf):
                    asm_function.instructions.append("if_" + str(instruction.id + if_id_binary) + ":") 
                elif isinstance(instruction, CheckIf):
                    if instruction.checking:
                        asm_function.instructions.append("pop r8")
                        asm_function.instructions.append("cmp r8, 1")
                        asm_function.instructions.append("jne if_" + str(instruction.false_id + if_id_binary))
                elif isinstance(instruction, EndIf):
                    asm_function.instructions.append("if_" + str(instruction.id + if_id_binary) + ":")
                elif isinstance(instruction, EndIfBlock):
                    asm_function.instructions.append("jmp if_" + str(instruction.id + if_id_binary))
                elif isinstance(instruction, PreStartWhile):
                    asm_function.instructions.append("while_" + str(instruction.id1 + if_id_binary) + ":")
                elif isinstance(instruction, StartWhile):
                    asm_function.instructions.append("pop r8")
                    asm_function.instructions.append("cmp r8, 1")
                    asm_function.instructions.append("jne while_" + str(instruction.id2 + if_id_binary))
                elif isinstance(instruction, EndWhile):
                    asm_function.instructions.append("jmp while_" + str(instruction.id1 + if_id_binary))
                    asm_function.instructions.append("while_" + str(instruction.id2 + if_id_binary) + ":")
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
        
        function.instructions.insert(2, "sub rsp, " + str(stack_index_max * 8 * 16))
    
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
    @print_integer_integer_:
    pop     rsi
    pop     rdi
    push    rdi
    push    rsi
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

    file.write("random: db \"/dev/random\"\n")

    file.write(inspect.cleandoc("""
        section .bss
        memory: resb 8
    """))

    file.close()

file_name_base = sys.argv[1][0 : sys.argv[1].index(".")]
program = parse_file(sys.argv[1], True)
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
        arguments = sys.argv[sys.argv.index("-r") + 1 :: ]
        #os.system("./build/" + file_name_base + " " + arguments)
        arguments.insert(0, "./build/" + file_name_base)
        thing = subprocess.run(arguments)
        if thing.returncode != 0:
            print("Exit Code: " + str(thing.returncode))
elif system == "Darwin":
    #format = "macho64"
    pass
