# Pico BLE Remote Pilot

Ce projet transforme un Raspberry Pi Pico W en un client Bluetooth Low Energy (BLE) capable de se connecter à un périphérique spécifique (comme un robot) et de lui envoyer une séquence de commandes.

## Matériel requis
- Un Raspberry Pi Pico W (le modèle **W** est indispensable pour le Bluetooth)
- Un périphérique BLE à piloter (par exemple, un joystick, un robot). Le script est pré-configuré pour l'adresse `f4:12:fa:6e:cf:59`.
- Un PC
- Un câble USB (micro-B vers type A)
- Le robot roulant (Arduino)

## Logiciel requis
- Le [firmware MicroPython pour Pico W](https://micropython.org/download/RPI_PICO_W/) installé sur le Raspberry Pico.
- Le logiciel [Thonny](https://thonny.org/) installé sur le PC.
- Le code de ce projet : [bleconnecteetpilote-pico.py](bleconnecteetpilote-pico.py).

## Configuration
Avant d'exécuter le script, vous devez configurer l'adresse MAC de votre appareil BLE cible.

1.  Ouvrez le fichier [bleconnecteetpilote-pico.py](bleconnecteetpilote-pico.py).
2.  Trouvez la ligne `_TARGET_ADDR = bytes([0xf4, 0x12, 0xfa, 0x6e, 0xcf, 0x59])`.
3.  Remplacez l'adresse par celle de votre appareil. Par exemple, si l'adresse de votre appareil est `aa:bb:cc:dd:ee:ff`, vous devrez la modifier comme suit :
    ```python
    _TARGET_ADDR = bytes([0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff])
    _TARGET_ADDR_STR = "aa:bb:cc:dd:ee:ff"
    ```

## Connexion
Reliez le PC (port USB-A) et le Pico W (port micro-USB) avec le câble.

## Préparation dans Thonny
1.  Ouvrez Thonny.
2.  Allez dans le menu "Outils" -> "Options...".
3.  Dans l'onglet "Interpréteur", sélectionnez `MicroPython (Raspberry Pi Pico)` comme interpréteur.
4.  Juste en dessous, sélectionnez le port série correspondant à votre Pico (par ex. `COM3` sur Windows, `/dev/ttyACM0` sur Linux).
5.  Cliquez sur "OK". La console en bas devrait afficher une invite MicroPython (`>>>`).

## Télécharger et exécuter le code
1.  Ouvrez le fichier [bleconnecteetpilote-pico.py](bleconnecteetpilote-pico.py) dans l'éditeur de Thonny.
2.  Cliquez sur le bouton vert avec une flèche (ou appuyez sur F5) pour envoyer et exécuter le programme sur le Pico.

## Vérifier la bonne exécution
1.  Regardez la LED embarquée sur le Pico : elle doit se mettre à clignoter, indiquant que le script recherche l'appareil.
2.  Observez la console dans Thonny. Vous devriez voir une sortie qui montre les étapes de la connexion, l'envoi des commandes et la déconnexion :

```
Bonjour depuis la Pico
Début de la recherche de l'appareil cible...
Scan pour l'appareil f4:12:fa:6e:cf:59 pendant 5 secondes...
Appareil cible trouvé ! Addr: f4:12:fa:6e:cf:59
Connecté avec succès à f4:12:fa:6e:cf:59, handle: 0
Service NUS trouvé.
Découverte des caractéristiques...
Caractéristique RX trouvée.

Prêt à envoyer la séquence de commandes.
Envoi de la commande : 1
Écriture réussie.
Envoi de la commande : 2
Écriture réussie.
Envoi de la commande : 8
Écriture réussie.

Séquence de commandes terminée. Déconnexion.
Déconnecté, handle: 0
Programme terminé.
```

Le programme s'arrête après avoir exécuté la séquence de commandes et s'être déconnecté.

Le robot roulant va effectuer plusieurs mouvements.

