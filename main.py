'''
    Enzo Cattiaux - {mettete i vostri nomi qui}
    xx.xx xx/xx/2023
    versione 2.x
    Convertitore grafcet -> arduino
'''

from os import listdir as os_listdir # lista dei file nella cartella di lavoro
from os.path import isfile as os_path_isfile # controlla se il file esiste
from sys import exit as sys_exit # esce dal programma
from sys import argv as sys_argv # input imessa dall'utente dal temrinale
from time import strftime # usato per ricavare la data corrente
from dataclasses import dataclass # simile alle strutture su c++


@dataclass
class Variable:
    name: str
    type: int


@dataclass
class State:
    name: str
    actions: list[str]
    transitions: list[str]


# restituisce le variabili del grafcet e i stati (VS)
def getVS(filename) -> tuple[Variable, int, int]: 
    # controllo che il file è presente
    if not os_path_isfile(filename):
        print(f"File '{filename}' not found")
        print(f"Files in current directory: {os_listdir()}")
        sys_exit(1)
    
    # ------
    # comincio lettura 
    # ------

    # copio i contenuti del file
    # (il context manager chiude automaticamente il file)
    with open(filename, 'r') as f:
        # divido il contenuto in blocchi (ogni linea vuota -> '\n\n')
        blocks = f.read().split("\n\n")
    
    # ---
    # variabili grafcet
    # ---

    # aggiunge alla lista 'variables' il nome e il tipo delle variabili
    # guardando le linee del primo blocco(block[0] -> split('\n')),
    # ingorando i primi 3 caratteri (line[3:])
    # e splittando i caratteri (split(', '))
    variables = [Variable(var, type)
                 for (type, line) in enumerate(blocks[0].split('\n'))
                 for var in line[3:].split(', ') if var != '']
    # 'list comprehension'
    '''
        variables = []
        for type, line in enumerate(block[0].split('\n')):
            for var in line[3:].split(', '):
                variables.append(Variable(var, type))
    '''

    # ---
    # stati
    # ---

    # aggiunge a states il nome, le azioni sui pin,
    # e le transizioni da svolgere
    # guardando ogni blocco e controllando
    # per ogni linea se contiene un 'if' (transizione)
    # o se è presente un '|' in seconda posizione (azione)
    states = []
    for block in blocks[1:]:
        lines = block.split('\n')
        state = State(name=lines[0][:-1],
                      actions=list(filter(lambda s: s[1] == '|',
                                          lines[1:])),
                      transitions=list(filter(lambda s: s[:2] == 'if',
                                              lines[1:])))
        # --- 'built-in filter()' - 'anonymous function lambda',
        '''
        state = State(name=lines[0], actions=[], transitions=[])
        for line in lines[1:]:
            if line[1] == '|':
                state.actions.append(line)
            if line[:2] == 'if':
                state.transitions.append(line)
        '''
        states.append(state)
    return variables, states


def writeArduinoFile(filename, variables, states):
    # scrivo i contenuti del file
    # avviso l'utente se ho creato un file nuovo o se lo ho sobrascritto
    print(f"file {filename} was " + ("overwritten" if os_path_isfile(filename)
                                     else "created"))

    # apro il file e metto l'intestazione
    with open(filename, 'w') as f:
        f.write("/*\n\tCodice generato con convertitore grafcet -> arduino\n"
                "\tprogrammato con python da Enzo Cattiaux\n"
                "\tversione programma 2.0 (03.02.2023)\n\t"
                + strftime("%d %B %Y %H:%M:%S") +
                "\n*/\n")

        # ---
        # global
        # ---
        # se sono presenti variabili dichiaro i pin (se sono di input o output)
        # e i loro stati
        if len(variables) >= 1:
            f.write("\n//Inserire i pin dei componenti\n")
            [f.write(f"const int pin_{variable.name} = ;\n")
             for variable in variables
             if variable.type in [0, 1]]
            '''
            for variable in variables:
                if variable.type != 0 and variable.type != 1: continue
                f.write(f"const int pin_{variable.name} = ;\n")
            '''
            f.write("\nbool "
                    + ", ".join([variable.name for variable in variables]) +
                    ";\n")
            '''
            f.write("\nbool ")
            for variable in variables:
                f.write(variable.name)
                f.write(", ") if variable != variables[-1] else file.write(";\n")
            '''

        # dichiaro le variabili di sistema e i stati
        f.write("int stato, oldStato;\n"
                "unsigned long T=millis();\n"
                "const int "
                + ", ".join([f"{state.name} = {i}"
                             for i, state in enumerate(states)]) +
                ";\n")
        '''
        f.write("int stato, oldStato;\n"
                "unsigned long T=millis();\n"
                "const int ")
        for i, variable in variables:
            f.write(f{variable} = {i})
            f.write(", ") if variable != variables[-1] else file.write(";\n")
        '''

        # ---
        # setup
        # ---
        # dichiaro la modalita dei pin delle variabili (input o output)
        f.write("\nvoid setup(){\n")
        [f.write(f"\tpinMode(pin_{variable.name}, "
                 + ("INPUT" if variable.type == 0 else "OUTPUT") +
                 ");\n")
         for variable in variables]
        '''
        for variabile in variables:
            if variabile.type == 0 or variabile.type == 1:
                f.write(f"\tpinMode(pin_{variabile.name}")
                f.write(", INPUT);\n") if variabile.type == 0 else f.write(", OUTPUT);\n")
        '''

        # ---
        # loop
        # ---
        f.write("\n\tstato = ;\t//inserire lo stato iniziale\n"
                "\toldStato = stato;\n}\n"
                "\nvoid loop(){\n")      

        # immagine lettura variabili
        [f.write(f"\t{variable.name} = digitalRead(pin_{variable.name});\n")
         for variable in variables if variable.type == 0]
        '''
        for variable in variables:
            if variable.type == 0:
                f.write(f"\t{variable.name} ="
                         "digitalRead(pin_{variable.name});\n")
        '''

        f.write("\n\tswitch(stato){\n")

        # conversione transizioni che contengono tempo (T<5s -> T<5*1000)
        TIME_CONV = {"y": "M*12", "M": "w*4", "w": "d*7", "d": "h*24",
                     "h": "m*60", "m": "s*60", "s": "ms*1000", "ms": ""}
        NUMBERS = [str(i) for i in range(10)]
        def convertTime(string) -> str:
            string = string.replace("T>", "millis()-T>")\
                           .replace("T<", "millis()-T<")
            # loop dove controlla ogni carattere se potrebbe essere un
            # espressione di tempo (ms, s, ecc), se lo è controlla che il
            # carattere precedente sia un numero e che quello che segue sia o
            # una parentesi chiusa o una moltiplicazione
            # continua finche non sono stati fatti tutti i casi e aumenta di
            # uno il posto della stringa così da non ripetere la stessa
            # substringa
            for key, value in TIME_CONV.items():
                c = 0
                while key in string[c:]:
                    c = string[c:].index(key) + c
                    if string[c-1] in NUMBERS and\
                       string[c+len(key)] in [')', '*']:
                        string = string[:c]\
                               + string[c:c+len(key)].replace(key, value)\
                               + string[c+len(key):]
                        c = 0
                    c += 1
            '''
            if "T<" in string: indx_start = string.index("T<") + 2
            else: indx_start = string.index("T>") + 2
            for key, value in TIME_CONV.items():
                indx_end = string.index(")", indx_start)
                if key in string[indx_start:indx_end]:
                    string = string[:indx_start]\
                    + string[indx_start:indx_end].replace(key, value)\
                    + string[indx_end:]
            return string
            '''
            return string

        # per ogni stato mette un caso e scrive le transizioni corrispodenti
        # inoltre richiama la funzione che converte il tempo
        for state in states:
            f.write(f"\t\tcase {state.name}:\n")
            for transition in state.transitions:
                if "T>" in transition or "T<" in transition:
                    transition = convertTime(transition)
                f.write(f"\t\t\t{transition};\n")
            f.write("\t\t\tbreak;\n")
        f.write("\t}\n\n")

        # cambia li stati delle variabili per ogni stato
        # imposta high or low in base alla azione da eseguire
        # se lo stato non ha azioni, saltalo
        for state in states:
            if len(state.actions) < 1:
                continue
            f.write(f"\tif(stato == {state.name})" + "{\n")
            for action in state.actions:
                f.write(f"\t\t{action[2:]} = "
                        + ("HIGH" if action[0] != "R" else "LOW") +
                        ";\n")
            f.write("\t}\n")

        f.write("\n\tif(oldStato != stato){\n"
                "\t\tT = millis();\n")
        # posso semplicemente impostare le variable di tipo N a LOW, tanto
        # verrano rimesse ad HIGH il ciclo seguente
        [f.write(f"\t\t{action[2:]} = LOW;\n")
         for state in states
         for action in state.actions
         if action[0] == 'N']
        '''
        for state in states:
            for action in state.actions:
                if action[0] == "N":
                    f.write(f"\t\t{action[2:]} = LOW;\n")
        '''
        
        f.write("\t\toldStato = stato;\n"
                "\t}\n\n")

        # immagine variable, output
        [f.write(f"\tdigitalWrite(pin_{variable.name}, {variable.name});\n")
         for variable in variables
         if variable.type == 1]
        '''
        for variable in variables:
            if variable.type == 1:
                f.write(f"\tdigitalWrite(pin_{variable.name}, {variable.name});\n")
        '''
        # fine scrittura
        f.write('}')
    print("Succesfully printed file")


def terminalInput() -> tuple[str, str]:
    # sys_argv[1]: nome file grafcet,
    # sys_argv[2]: nome file output (se non incluso copia nome file grafcet)
    if len(sys_argv) <= 1:
        print("Incorrect usage, must include grafcet file name")
        sys_exit(".py 'grafcet' *'file_output'")
    if len(sys_argv) <= 2:
        return sys_argv[1], sys_argv[1].replace(".txt", ".ino")
    return sys_argv[1], sys_argv[2]


def main():
    input_file, output_file = terminalInput()
    variables, states = getVS(input_file) 
    writeArduinoFile(output_file, variables, states)


if __name__ == "__main__":
    main()
