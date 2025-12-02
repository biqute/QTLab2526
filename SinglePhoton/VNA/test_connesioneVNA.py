import sys
import time
from VNA.VNA_class import VNA  # Assumendo che la classe sia definita in un file chiamato 'vna.py'

# Indirizzo IP del VNA
vna_ip_address = "193.206.156.99"  # Sostituisci con l'indirizzo IP del tuo VNA

def check_vna_connection(vna_ip):
    try:
        print(f"Provo a connettermi al VNA con IP {vna_ip}...")
        vna = VNA(vna_ip)
        
        # Ottieni ID senza write_expect
        idn = vna.query_expect("*IDN?", "Impossibile ottenere l'ID del VNA.")
        
        print(f"Connessione riuscita! ID del dispositivo: {idn.strip()}")
        
    except Exception as e:
        print(f"Errore durante la connessione al VNA: {e}")
        
if __name__ == "__main__":
    # Verifica la connessione al VNA
    check_vna_connection(vna_ip_address)
