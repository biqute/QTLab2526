import numpy as np
import matplotlib.pyplot as plt
#from iminuit import Minuit
#from iminuit.cost import LeastSquares  #Perchè???
import os

class Data :

    def __init__ (self, x = None, y = None, z = None) :
        if x is None or y is None :
            # Se mancano i dati base (x, y), crea un oggetto vuoto
            self.x = np.array([])
            self.y = np.array([])
            self.z = np.array([])
            self.vect = np.array([])
            if x is not None or y is not None or z is not None:
                 print("Attenzione: x e y sono necessari. Oggetto Data creato vuoto.")
            return

        if len(x) != len(y):
            raise ValueError("I vettori x e y devono avere la stessa lunghezza.")

        self.x = np.array(x)
        self.y = np.array(y)
        
        if z is not None:
            # Caso a 3 colonne (es. Freq, Real, Imag)
            if len(x) != len(z):
                raise ValueError("Se fornito, z deve avere la stessa lunghezza di x e y.")
            self.z = np.array(z)
            self.vect = np.column_stack((self.x, self.y, self.z))
        else:
            # Caso a 2 colonne (z è None)
            self.z = np.array([]) # Array vuoto, non None
            self.vect = np.column_stack((self.x, self.y))


    def save_txt (self, nome, commento="colonne x e y") :
        
        try :

            np.savetxt(f"../data/{nome}.txt", self.vect, fmt="%.18g", newline="\n", delimiter="\t", header=commento)
            return True
        
        except Exception as e :

            print(f"Errore durante il salvataggio: {e}")
            return False
        

    def plot (self, x= None, y= None, Title="Spectrum", Nome_x="Frequency [Hz]", Nome_y="Amplitude [dBm]") :

        if x is None:
            x = self.x

        if y is None:
            y = self.y

        fig, ax = plt.subplots ( nrows=1, ncols=1)
        plt.title(f"{Title}")
        plt.xlabel(f"{Nome_x}")
        plt.ylabel(f"{Nome_y}")
        plt.plot(x, y)
        plt.show()
    
    
    @staticmethod
    def read_txt (nome) :
        try:
            data = np.loadtxt(f"../data/{nome}.txt", delimiter="\t")
            
            # Controlla quante colonne ci sono
            if data.ndim == 1: # Caso sfortunato di una sola riga
                data = data.reshape(1, -1)
                
            num_cols = data.shape[1]
            
            x = data[:, 0]
            y = data[:, 1]
            
            if num_cols >= 3:
                z = data[:, 2]
                print(f"Lette 3 colonne (x, y, z) da ../data/{nome}.txt")
                return x, y, z
            else:
                print(f"Lette 2 colonne (x, y) da ../data/{nome}.txt")
                return x, y

        except Exception as e :
            print(f"Errore durante la lettura: {e}")
            return None, None, None # Restituisci tuple per il unpacking sicuro
        
