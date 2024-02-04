'''
    Enzo Cattiaux
    18.28 03/02/2023
    version 2.0
    Converter grafcet -> arduino
'''

from os import listdir as os_listdir
from os.path import isfile as os_path_isfile
from sys import exit as sys_exit
from sys import argv as sys_argv
from time import strftime
from dataclasses import dataclass


@dataclass
class Variable:
    name: str
    type: int


@dataclass
class State:
    name: str
    actions: list[str]
    transitions: list[str]


# returns the variables of the grafcet and the states (VS)
def getVS(filename) -> tuple[Variable, int, int]: 
    # check if the file is present
    if not os_path_isfile(filename):
        print(f"File '{filename}' not found")
        print(f"Files in current directory: {os_listdir()}")
        sys_exit(1)
    
    # start reading the file

    # copy the contents of the file
    # (the context manager automatically closes the file)
    with open(filename, 'r') as f:
        # split the content into blocks (each empty line -> '\n\n')
        blocks = f.read().split("\n\n")
    
    # grafcet variables

    # add to the 'variables' list the name and type of the variables
    # looking at the lines of the first block (block[0] -> split('\n')),
    # ignoring the first 3 characters (line[3:])
    # and splitting the characters (split(', '))
    variables = [Variable(var, type)
                 for (type, line) in enumerate(blocks[0].split('\n'))
                 for var in line[3:].split(', ') if var != '']

    # states

    # adds to states the name, the actions on the pins,
    # and the transitions to be carried out
    # looking at each block and checking
    # each line if it contains an 'if' (transition)
    # or if there is a '|' in the second position (action)
    states = []
    for block in blocks[1:]:
        lines = block.split('\n')
        state = State(name=lines[0][:-1],
                      actions=list(filter(lambda s: s[1] == '|',
                                          lines[1:])),
                      transitions=list(filter(lambda s: s[:2] == 'if',
                                              lines[1:])))
        states.append(state)
    return variables, states


def writeArduinoFile(filename, variables, states):
    # Writing the contents of the file
    # Informing the user if a new file was created or if it was overwritten
    print(f"file {filename} was " + ("overwritten" if os_path_isfile(filename) else "created"))

    # Opening the file and adding the header
    with open(filename, 'w') as f:
        f.write("/*\n\tCode generated with grafcet to arduino converter\n"
                "\tprogrammed in python by Enzo Cattiaux\n"
                "\tprogram version 2.0 (03.02.2023)\n\t"
                + strftime("%d %B %Y %H:%M:%S") +
                "\n*/\n")

        # Declaring pins and their states if variables are present
        if len(variables) >= 1:
            f.write("\n//Insert the component pins\n")
            for variable in variables:
                if variable.type in [0, 1]:
                    f.write(f"const int pin_{variable.name} = ;\n")
            f.write("\nbool " + ", ".join([variable.name for variable in variables]) + ";\n")

        # Declaring system variables and states
        f.write("int stato, oldStato;\n"
                "unsigned long T=millis();\n"
                "const int " + ", ".join([f"{state.name} = {i}" for i, state in enumerate(states)]) + ";\n")

        # Setting up pin modes for variables
        f.write("\nvoid setup(){\n")
        for variable in variables:
            f.write(f"\tpinMode(pin_{variable.name}, " + ("INPUT" if variable.type == 0 else "OUTPUT") + ");\n")

        # Loop
        f.write("\n\tstato = ;\t//insert the initial state\n"
                "\toldStato = stato;\n}\n"
                "\nvoid loop(){\n")

        # Reading input variables
        for variable in variables:
            if variable.type == 0:
                f.write(f"\t{variable.name} = digitalRead(pin_{variable.name});\n")

        f.write("\n\tswitch(stato){\n")

        # Converting transitions that contain time (e.g., T<5s -> T<5*1000)
        TIME_CONV = {"y": "M*12", "M": "w*4", "w": "d*7", "d": "h*24",
                     "h": "m*60", "m": "s*60", "s": "ms*1000", "ms": ""}
        NUMBERS = [str(i) for i in range(10)]
        def convertTime(string) -> str:
            string = string.replace("T>", "millis()-T>").replace("T<", "millis()-T<")
            for key, value in TIME_CONV.items():
                c = 0
                while key in string[c:]:
                    c = string[c:].index(key) + c
                    if string[c-1] in NUMBERS and string[c+len(key)] in [')', '*']:
                        string = string[:c] + string[c:c+len(key)].replace(key, value) + string[c+len(key):]
                        c = 0
                    c += 1
            return string

        # Writing transitions for each state and calling the time conversion function
        for state in states:
            f.write(f"\t\tcase {state.name}:\n")
            for transition in state.transitions:
                if "T>" in transition or "T<" in transition:
                    transition = convertTime(transition)
                f.write(f"\t\t\t{transition};\n")
            f.write("\t\t\tbreak;\n")
        f.write("\t}\n\n")

        # Changing the states of the variables for each state
        for state in states:
            if len(state.actions) < 1:
                continue
            f.write(f"\tif(stato == {state.name})" + "{\n")
            for action in state.actions:
                f.write(f"\t\t{action[2:]} = " + ("HIGH" if action[0] != "R" else "LOW") + ";\n")
            f.write("\t}\n")

        # Handling state changes
        f.write("\n\tif(oldStato != stato){\n"
                "\t\tT = millis();\n")
        for state in states:
            for action in state.actions:
                if action[0] == 'N':
                    f.write(f"\t\t{action[2:]} = LOW;\n")
        f.write("\t\toldStato = stato;\n"
                "\t}\n\n")

        # Updating output variables
        for variable in variables:
            if variable.type == 1:
                f.write(f"\tdigitalWrite(pin_{variable.name}, {variable.name});\n")

        # End of writing
        f.write('}')
    print("Successfully printed file")


def terminalInput() -> tuple[str, str]:
    # Checking the number of arguments provided
    if len(sys_argv) <= 1:
        print("Incorrect usage, must include Grafcet file name")
        sys_exit(".py 'grafcet' *'file_output'")
    
    # If only the Grafcet file name is provided, use it to create the output file name
    if len(sys_argv) <= 2:
        return sys_argv[1], sys_argv[1].replace(".txt", ".ino")

    # If both Grafcet and output file names are provided, return them
    return sys_argv[1], sys_argv[2]


def main():
    input_file, output_file = terminalInput()
    variables, states = getVS(input_file) 
    writeArduinoFile(output_file, variables, states)


if __name__ == "__main__":
    main()
