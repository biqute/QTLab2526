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


    def save_txt (self, file_to_save
                  #, commento="colonne x e y"
                  ) :
        
        try :

            np.savetxt(f"../data/{file_to_save}.txt", self.vect, fmt="%.18g", newline="\n", delimiter="\t"
                       #, header=commento
                       )
            return True
        
        except Exception as e :

            print(f"Errore durante il salvataggio: {e}")
            return False
        

    def fast_plot(self, x=None, y=None, 
                Title="Title", 
                x_title="x Title [x_units]", 
                y_title="y Title [y_units]",
                #point_tipe = 'o',
                label_name="Data",
                save_as=None):

        if x is None:
            x = self.x

        if y is None:
            y = self.y

        if len(x) == 0 or len(y) == 0:
            print("Nessun dato disponibile per il plot.")
            return

        # Disegno
        fig, ax = plt.subplots()
        ax.set_title(Title)
        ax.set_xlabel(x_title)
        ax.set_ylabel(y_title)
        ax.plot(x, y, 
                #marker = point_tipe, 
                label = label_name)
        
        plt.show()

        if save_as is not None:
            save_as += ".pdf"
            fig.savefig(f"../data0_plots/{save_as}", bbox_inches="tight")
            print(f"Grafico salvato in ../data0_plots/{save_as}")

    #@staticmethod
    def read_txt (self, file_to_read, spacing="\t") :
        try:
            if spacing is None:
                spacing = "\t"
            data = np.loadtxt(f"../data/{file_to_read}.txt", delimiter=spacing)
            num_cols = data.shape[1]
            
            x = data[:, 0]
            y = data[:, 1]
            #self.x = data[:, 0]
            #self.y = data[:, 1]
            
            if num_cols >= 3:
                #self.z = data[:, 2]
                z = data[:, 2]
                print(f"Lette 3 colonne (x, y, z) da ../data/{file_to_read}.txt")
                return x, y, z
            else:
                print(f"Lette 2 colonne (x, y) da ../data/{file_to_read}.txt")
                return x, y

        except Exception as e :
            print(f"Errore durante la lettura: {e}")
            return None, None, None # Restituisci tuple per il unpacking sicuro
        
    #def big_plot(file_to_read)
    #    
    #    data = read_txt(file_to_read)
    #    f = data[:, 0]              # Frequenza
    #    real = data[:, 1]
    #    imag = data[:, 2]
    #    phase = np.atan(imag/real)

        
        
