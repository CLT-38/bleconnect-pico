from machine import Pin
import ubluetooth
import time
import sys

led = Pin("LED", Pin.OUT)
print("Bonjour depuis la Pico")

# Définitions pour le service Nordic UART (NUS)
_NUS_SERVICE_UUID = ubluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_NUS_RX_CHAR_UUID = ubluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")

# Adresse MAC de l'appareil cible (le joystick)
# L'adresse doit être en bytes, et non en string.
# f4:12:fa:6e:cf:59
_TARGET_ADDR = bytes([0xf4, 0x12, 0xfa, 0x6e, 0xcf, 0x59])
_TARGET_ADDR_STR = "f4:12:fa:6e:cf:59"

# Classe pour gérer la connexion et la communication BLE
class BLEManager:
    def __init__(self):
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.irq_handler)
        
        self.target_found = False
        self.conn_handle = None
        self.rx_value_handle = None
        self.write_done = False
        self.service_found = False

    # Gestionnaire d'interruptions pour les événements BLE
    def irq_handler(self, event, data):
        # Événement 5: _IRQ_SCAN_RESULT -> un appareil a été trouvé
        if event == 5:
            addr_type, addr, adv_type, rssi, adv_data = data
            
            # --- DEBUG: Afficher tous les appareils vus pendant le scan ---
            addr_str_debug = ":".join(f"{b:02x}" for b in addr)
            print(f"--- DEBUG VU: {addr_str_debug} (type d'adresse: {addr_type})")
            # --- FIN DEBUG ---

            if addr == _TARGET_ADDR:
                print(f"Appareil cible trouvé ! Addr: {_TARGET_ADDR_STR}")
                self.target_found = True
                # Arrêter le scan pour initier la connexion
                self.ble.gap_scan(None)
                self.ble.gap_connect(addr_type, addr)

        # Événement 6: _IRQ_SCAN_DONE -> le scan est terminé
        elif event == 6:
            if not self.target_found:
                print("Scan terminé, appareil cible non trouvé.")

        # Événement 7: _IRQ_PERIPHERAL_CONNECT -> connexion établie
        elif event == 7:
            conn_handle, addr_type, addr = data
            print(f"Connecté avec succès à {_TARGET_ADDR_STR}, handle: {conn_handle}")
            self.conn_handle = conn_handle
            # Découvrir les services de l'appareil connecté
            self.ble.gattc_discover_services(self.conn_handle)

        # Événement 8: _IRQ_PERIPHERAL_DISCONNECT -> déconnexion
        elif event == 8:
            conn_handle, _, _ = data
            print(f"Déconnecté, handle: {conn_handle}")
            self.conn_handle = None
            # La déconnexion met fin au programme dans la boucle principale

        # Événement 9: _IRQ_GATTC_SERVICE_RESULT -> résultat de la découverte de service
        elif event == 9:
            conn_handle, start_handle, end_handle, uuid = data
            if conn_handle == self.conn_handle and uuid == _NUS_SERVICE_UUID:
                print("Service NUS trouvé.")
                # Mettre le drapeau à True au lieu de lancer la découverte ici
                self.service_found = True

        # Événement 11: _IRQ_GATTC_CHARACTERISTIC_RESULT -> résultat de la découverte de caractéristique
        elif event == 11:
            conn_handle, def_handle, value_handle, properties, uuid = data
            if conn_handle == self.conn_handle and uuid == _NUS_RX_CHAR_UUID:
                print("Caractéristique RX trouvée.")
                self.rx_value_handle = value_handle

        # Événement 17: _IRQ_GATTC_WRITE_DONE -> l'écriture est terminée
        elif event == 17:
            conn_handle, value_handle, status = data
            if status == 0:
                print("Écriture réussie.")
            else:
                print(f"Échec de l'écriture, status: {status}")
            self.write_done = True

    def scan(self, duration_s=10):
        """Démarre le scan pour un appareil spécifique."""
        print(f"Scan pour l'appareil {_TARGET_ADDR_STR} pendant {duration_s} secondes...")
        self.target_found = False
        self.ble.gap_scan(duration_s * 1000, 30000, 30000, False)
        time.sleep(duration_s)
        if not self.target_found:
            self.ble.gap_scan(None) # Arrêter explicitement si non trouvé

    def send_command(self, command):
        """Envoie une commande à la caractéristique RX."""
        if self.conn_handle is not None and self.rx_value_handle is not None:
            print(f"Envoi de la commande : {command}")
            
            # Convertir la commande en un seul byte
            data_to_send = bytes([command])
            
            # Écrire sans attente de réponse. Le '1' à la fin active ce mode.
            # Cela supprime la nécessité d'attendre un _IRQ_GATTC_WRITE_DONE.
            self.ble.gattc_write(self.conn_handle, self.rx_value_handle, data_to_send, 1)
            
        else:
            print("Impossible d'envoyer : non connecté ou caractéristique RX non trouvée.")

    def disconnect(self):
        """Demande la déconnexion."""
        if self.conn_handle is not None:
            self.ble.gap_disconnect(self.conn_handle)

    def discover_characteristics(self):
        """Lance la découverte des caractéristiques pour le service NUS."""
        if self.conn_handle is not None:
            print("Découverte des caractéristiques...")
            # L'UUID du service est nécessaire pour la découverte des caractéristiques
            self.ble.gattc_discover_characteristics(self.conn_handle, 1, 0xFFFF)


# Point d'entrée principal du script
def main():
    ble_manager = BLEManager()
    
    print("Début de la recherche de l'appareil cible...")
    # Boucler jusqu'à ce que l'appareil soit trouvé et connecté
    while ble_manager.conn_handle is None:
        led.toggle() # Indique que la recherche est active
        ble_manager.scan(5) # Lancer un scan court de 5 secondes
        
        # Si le scan se termine et que la cible n'a pas été trouvée,
        # on fait une petite pause avant de relancer le scan.
        if not ble_manager.target_found:
            print("Cible non trouvée, nouveau scan dans 3 secondes...")
            time.sleep(3)
        else:
            # La cible a été trouvée, l'IRQ a lancé la connexion.
            # On attend un peu que la connexion s'établisse.
            connect_timeout = time.time() + 10
            while ble_manager.conn_handle is None and time.time() < connect_timeout:
                time.sleep(0.1)
            
            if ble_manager.conn_handle is None:
                print("La connexion a échoué après avoir trouvé l'appareil.")
                # On réinitialise pour retenter un cycle complet
                ble_manager.target_found = False


    # Attendre que le service soit trouvé (géré par IRQ)
    service_timeout = time.time() + 10
    while not ble_manager.service_found and time.time() < service_timeout:
        time.sleep(0.1)

    if not ble_manager.service_found:
        print("Échec de la découverte du service NUS.")
        ble_manager.disconnect()
        sys.exit()

    # Le service est trouvé, on peut lancer la découverte des caractéristiques
    ble_manager.discover_characteristics()

    # Attendre que la caractéristique RX soit trouvée (gérée par IRQ)
    char_timeout = time.time() + 10
    while ble_manager.rx_value_handle is None:
        if time.time() > char_timeout:
            print("Échec de la découverte de la caractéristique RX.")
            ble_manager.disconnect()
            sys.exit()
        led.toggle()
        time.sleep(0.2)

    print("\nPrêt à envoyer la séquence de commandes.")

    # Petite pause pour stabiliser la connexion avant d'envoyer des données
    time.sleep(2)    
    
    # Envoyer la séquence de commandes
    commands = [1, 2, 8]
    
    ble_manager.send_command(commands[0])
    time.sleep(2)
    
    ble_manager.send_command(commands[1])
    time.sleep(2)

    ble_manager.send_command(commands[2])
    time.sleep(2)
    
    print("\nSéquence de commandes terminée. Déconnexion.")
    ble_manager.disconnect()

    # Attendre que la déconnexion soit effective
    disconnect_timeout = time.time() + 5
    while ble_manager.conn_handle is not None:
        if time.time() > disconnect_timeout:
            break
        led.toggle()
        time.sleep(0.2)
        
    led.off()
    print("Programme terminé.")

# Exécuter le programme principal
main()
