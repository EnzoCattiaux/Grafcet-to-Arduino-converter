import sys
import time
from os import path


class Variables:
    def __init__(self, name, mode):
        self.name = name
        self.mode = mode

    def __repr__(self):
        return str(self.mode)+": "+str(self.name)


class Transitions:
    def __init__(self, conditions, next_step):
        self.conditions = conditions
        self.next_step = next_step

    @staticmethod
    def handle_time_condition(condition):
        if Transitions.is_time(condition):
            condition = condition.replace("ms", "*1")
            condition = condition.replace("s", "*1000")
            condition = condition.replace("m", "*60*1000")
            condition = condition.replace("h", "*60*60*1000")
            condition = condition.replace("d", "*24*60*60*1000")
            condition = condition.replace("M", "*30*24*60*60*1000")
            condition = condition.replace("y", "*24*30*24*60*60*1000")

            list_temp = []
            list_temp[:] = condition
            idx = condition.find("T")
            list_temp.insert(idx, "millis()-")
            condition = "".join(list_temp)
        return condition

    @staticmethod
    def is_time(condition):
        condition = condition.replace("(", "")
        if condition[0] == "T":
            if condition[1] == ">" or condition[1] == "<":
                return True
        return False

    def __repr__(self):
        return str(self.conditions)+"|"+str(self.next_step)


class Stato:
    def __init__(self, name, actions, transitions):
        self.name = name
        self.actions = actions
        self.transitions = []
        self.true_transitions(transitions)

    def true_transitions(self, transitions):
        for transition in transitions:
            condition = transition
            start_condition = condition.index("(") + 1
            end_condition = condition.rindex(")")
            condition = condition[start_condition:end_condition]

            next_step = transition[end_condition + 1:]
            start_next_step = next_step.find("stato = ") + 8
            next_step = next_step[start_next_step:]

            self.transitions.append(Transitions(condition.split(" "), next_step))

    def __repr__(self):
        return "[" + str(self.name) + "]" + str(self.actions) + str(self.transitions)


class OutputChanges:
    def __init__(self, name, changes, steps):
        self.changes = []
        self.steps = []
        self.name = name
        self.changes.append(changes)
        self.steps.append(steps)

    def organize(self):
        i = 0
        while i < len(self.steps):
            i2 = i + 1
            while i2 < len(self.steps):
                if self.steps[i] == self.steps[i2]:
                    self.steps.pop(i2)
                    self.changes.pop(i2)
                    i = -1
                    break
                i2 += 1
            i += 1

    def __repr__(self):
        str_changes = ""
        str_steps = ""
        for change in self.changes:
            str_changes += "|" + change
        for step in self.steps:
            str_steps += "|" + step
        return str(self.name) + str_changes + str_steps

    def __add__(self, others):
        self.changes += others.changes
        self.steps += others.steps
        self.organize()

        others.changes = self.changes
        others.steps = self.steps
        others.organize()


def readfile(name_file_grafcet):
    if path.isfile(name_file_grafcet) is False:
        print(f"file '{name_file_grafcet}' not found")
        # print(f"python: can't open file '{path.dirname(__file__)}\{name_file_grafcet}'"
        #       f": [Errno 2] No such file or directory")
        sys.exit()

    with open(name_file_grafcet, "r") as file:
        lines = file.read().split("\n")
        file.close()

    var = []                                          # lista delle variabili
    for i in range(3):                                # per le prime tre righe
        temp_lines = lines[i].split(", ")             # creao una linea temporanea in cui divido la linea per la virgola
        temp_lines[0] = temp_lines[0][3:]             # nel primo dato elimino i primi tre caratteri ("I: ","O: ","M: ")
        if temp_lines[0] != "":                       # se la linea non è vuota aggiungo alla lista le variabili
            for i2 in range(len(temp_lines)):
                var.append(Variables(temp_lines[i2], i))    # i sta per il tipo di variabile (0->inp, 1->out, 2->mer)

    steps = []
    name = []
    actions = []
    transitions = []
    for i, line in enumerate(lines):
        if i > 2:
            if line == "":
                steps.append(Stato(name, actions, transitions)) if i > 3 else None
                name = lines[i+1][:-1]
                actions = []
                transitions = []
            elif line[:2] == "if":
                transitions.append(line)
            elif line[1] == "|":
                actions.append(line)
    steps.append(Stato(name, actions, transitions))

    for step in steps:
        for transition in step.transitions:
            for i2, condition in enumerate(transition.conditions):
                if i2 % 2 == 0:
                    transition.conditions[i2] = Transitions.handle_time_condition(condition)

    actions = organize_actions(steps)
    return var, steps, actions


def organize_actions(steps):
    all_actions = []
    for step in steps:
        for step.action in step.actions:
            all_actions.append(OutputChanges(step.action[2:], step.action[0], step.name))

    for i, action in enumerate(all_actions):
        for i2, action2 in enumerate(all_actions):
            if i+1 <= i2 and action.name == action2.name:
                action + action2

    i = 0
    while i < len(all_actions):
        i2 = i + 1
        while i2 < len(all_actions):
            if all_actions[i].name == all_actions[i2].name:
                all_actions.pop(i2)
                i = -1
                break
            i2 += 1
        i += 1
    return all_actions


def printfile(vsa_filein, name_file_output):
    var, steps, actions = vsa_filein

    owc = "overwritten" if path.isfile(name_file_output) else "created"
    print(f"file '{name_file_output}' was {owc}")

    with open(name_file_output, "w") as file:
        date = time.strftime("%d %B %Y %H:%M:%S")
        file.write("/*\n\tCodice generato con convertitore grafcet -> arduino\n"
                   "\tprogrammato con python da Enzo Cattiaux\n"
                   "\tversione programma 1.0 (10.03.2022)\n"
                   f"\t{date}\n*/\n")             # global scope --------------------------------------------------

        # ---------------------------
        # "#define"
        # ---------------------------
        if len(var) > 0:
            file.write("\n//inserire i pin dei componenti\n")
            for variable in var:
                if variable.mode == 0 or variable.mode == 1:
                    file.write(f"#define pin_{variable.name}\n")

        # ---------------------------
        # variabili booleane
        # ---------------------------
            file.write("\nbool ")
            for variable in var:
                file.write(variable.name)
                file.write(", ") if variable != var[-1] else file.write(";\n")

        # ---------------------------
        # stati
        # ---------------------------
        file.write("int stato, oldStato;\n"
                   "unsigned long T=millis();\n"
                   "const int ")
        for i, step in enumerate(steps):
            file.write(f"{step.name}={str(i)}")
            file.write(", ") if i + 1 < len(steps) else file.write(";\n")

        file.write("\nvoid setup(){\n")     # void setup --------------------------------------------------

        # ---------------------------
        # "pinMode()"
        # ---------------------------
        for variabile in var:
            if variabile.mode == 0 or variabile.mode == 1:
                file.write(f"\tpinMode(pin_{variabile.name}")
                file.write(", INPUT);\n") if variabile.mode == 0 else file.write(", OUTPUT);\n")

        file.write("\n\tstato = ;\t//inserire lo stato iniziale\n\toldStato = stato;\n}\n"
                   "\nvoid loop(){\n")      # void loop --------------------------------------------------

        # ---------------------------
        # "digitalRead()"
        # ---------------------------
        for variable in var:
            file.write(f"\t{variable.name} = digitalRead(pin_{variable.name});\n") if variable.mode == 0 else None

        # ---------------------------
        # "switch()"
        # ---------------------------
        file.write("\n\tswitch(stato){\n")
        for step in steps:
            file.write(f"\t\tcase {step.name}: //{step.name}\n")
            for i, transition in enumerate(step.transitions):
                file.write("\t\t\tif(")
                file.write(" ".join(transition.conditions))
                file.write(f") stato = {transition.next_step};\n")
            file.write("\t\t\tbreak;\n")
        file.write("\t}\n\n")

        # ---------------------------
        # "actions"
        # ---------------------------
        for action in actions:
            if action.changes.count("S") + action.changes.count("N") > 0:
                cont = 0
                file.write(f"\tif(")
                for (step, change) in zip(action.steps, action.changes):
                    if change == "S" or change == "N":
                        file.write(" || ") if cont > 0 else file.write("")
                        file.write(f"stato == {step}")
                        cont += 1
                file.write(f") {action.name} = HIGH;\n")
            if action.changes.count("R") > 0:
                cont = 0
                file.write("\tif(")
                for (step, change) in zip(action.steps, action.changes):
                    if change == "R":
                        file.write(" || ") if cont > 0 else file.write("")
                        file.write(f"stato == {step}")
                        cont += 1
                file.write(f") {action.name} = LOW;\n")
            file.write("\n")

        # ---------------------------
        # stati
        # ---------------------------
        file.write("\tif(oldStato != stato){\n"
                   "\t\tT = millis();\n"
                   )

        for action in actions:
            if action.changes.count("N") > 0:
                i = 0
                file.write(f"\t\tif(")
                for (step, change) in zip(action.steps, action.changes):
                    if change == "N":
                        file.write(" || ") if i > 0 else file.write("")
                        file.write(f"oldStato == {step}")
                        i += 1
                file.write(f") {action.name} = LOW;\n")

        '''
        for step in steps:
            for action in actions:
                for stepAction, change in zip(action.steps, action.changes):
                    if change == "N" and stepAction == step.name:
                        file.write(f"\t\tif(oldStato == {step.name}) {action.name} = LOW;\n")
        '''

        file.write("\t\toldStato = stato;\n"
                   "\t}\n")

        # ---------------------------
        # "digitalWrite()"
        # ---------------------------
        file.write("\n")
        for variable in var:
            if variable.mode == 1:
                file.write(f"\tdigitalWrite(pin_{variable.name}, {variable.name});\n")

        file.write("}")


def main(files):
    printfile(readfile(files[0]), files[1])


def terminal_input():
    if len(sys.argv) > 1:
        grafname = sys.argv[1]
    else:
        sys.exit("main.py 'grafcet.txt' *'file_output'")
    sys.exit("file grafcet must be '.txt'") if grafname.find(".txt") == -1 else None
    outname = grafname.replace(".txt", ".ino") if len(sys.argv) <= 2 else sys.argv[2]
    return grafname, outname


if __name__ == "__main__":
    start = time.perf_counter()
    main(terminal_input())

    print(f"time of execution: {str(round((time.perf_counter()-start), 10))} seconds")
