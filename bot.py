import os
import sqlite3
import logging
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from discord import app_commands

# ============================================================
# CONFIGURATION
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN", "token sera ajouté apres").strip()
CHANNEL_ID = int(os.getenv("QUIZ_CHANNEL_ID", "1565327428413296710"))

TIMEZONE = ZoneInfo("Europe/Paris")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "cyberquiz.db")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("CyberQuiz")

# ============================================================
# QUESTIONS
# correct_index : 0 = A, 1 = B, 2 = C, 3 = D
# ============================================================

QUESTIONS = [
    {
        "id": "CYB001",
        "category": "Réseaux",
        "difficulty": "facile",
        "question": "Quel est le rôle principal du DNS ?",
        "options": [
            "Chiffrer les fichiers",
            "Résoudre les noms de domaine",
            "Bloquer les virus",
            "Créer des utilisateurs"
        ],
        "correct_index": 1,
        "explanation": "Le DNS permet notamment de traduire un nom de domaine en adresse IP."
    },
    {
        "id": "CYB002",
        "category": "Réseaux",
        "difficulty": "facile",
        "question": "Quel protocole est conçu pour sécuriser le Web avec TLS ?",
        "options": ["FTP", "Telnet", "HTTPS", "HTTP"],
        "correct_index": 2,
        "explanation": "HTTPS protège les échanges Web grâce à TLS."
    },
    {
        "id": "CYB003",
        "category": "Réseaux",
        "difficulty": "facile",
        "question": "Combien de couches compte le modèle OSI ?",
        "options": ["4", "5", "6", "7"],
        "correct_index": 3,
        "explanation": "Le modèle OSI comprend sept couches."
    },
    {
        "id": "CYB004",
        "category": "Réseaux",
        "difficulty": "moyen",
        "question": "Quel protocole attribue automatiquement des adresses IP ?",
        "options": ["DHCP", "SMTP", "SSH", "SNMP"],
        "correct_index": 0,
        "explanation": "DHCP permet notamment d'attribuer automatiquement une configuration IP."
    },
    {
        "id": "CYB005",
        "category": "Réseaux",
        "difficulty": "moyen",
        "question": "Quel est le rôle principal d'un pare-feu ?",
        "options": [
            "Augmenter la RAM",
            "Filtrer le trafic réseau",
            "Compresser les fichiers",
            "Créer des certificats"
        ],
        "correct_index": 1,
        "explanation": "Un pare-feu applique des règles pour autoriser ou bloquer des communications."
    },
    {
        "id": "CYB006",
        "category": "Linux",
        "difficulty": "facile",
        "question": "Quelle commande affiche le répertoire courant sous Linux ?",
        "options": ["ls", "cd", "pwd", "mkdir"],
        "correct_index": 2,
        "explanation": "pwd affiche le chemin du répertoire de travail courant."
    },
    {
        "id": "CYB007",
        "category": "Linux",
        "difficulty": "facile",
        "question": "Quelle commande liste les fichiers d'un répertoire ?",
        "options": ["ls", "rm", "pwd", "whoami"],
        "correct_index": 0,
        "explanation": "ls affiche les fichiers et répertoires, selon les options utilisées."
    },
    {
        "id": "CYB008",
        "category": "Linux",
        "difficulty": "moyen",
        "question": "Quelle commande affiche l'identité de l'utilisateur courant ?",
        "options": ["uname", "whoami", "chmod", "grep"],
        "correct_index": 1,
        "explanation": "whoami affiche le nom de l'utilisateur effectif."
    },
    {
        "id": "CYB009",
        "category": "Linux",
        "difficulty": "moyen",
        "question": "À quoi sert principalement chmod ?",
        "options": [
            "Afficher la mémoire",
            "Changer le nom d'un fichier",
            "Modifier les permissions",
            "Résoudre un nom DNS"
        ],
        "correct_index": 2,
        "explanation": "chmod permet de modifier les permissions d'accès aux fichiers et répertoires."
    },
    {
        "id": "CYB010",
        "category": "Python",
        "difficulty": "facile",
        "question": "Quel mot-clé définit une fonction Python ?",
        "options": ["func", "define", "function", "def"],
        "correct_index": 3,
        "explanation": "En Python, le mot-clé def sert à définir une fonction."
    },
    {
        "id": "CYB011",
        "category": "Python",
        "difficulty": "facile",
        "question": "Quel type Python représente une suite ordonnée modifiable ?",
        "options": ["list", "tuple", "bool", "int"],
        "correct_index": 0,
        "explanation": "Une liste Python est ordonnée et peut être modifiée."
    },
    {
        "id": "CYB012",
        "category": "Cryptographie",
        "difficulty": "facile",
        "question": "Quel est l'objectif principal du chiffrement ?",
        "options": [
            "Supprimer les sauvegardes",
            "Rendre les données illisibles sans la clé appropriée",
            "Augmenter la vitesse du réseau",
            "Remplacer les mots de passe"
        ],
        "correct_index": 1,
        "explanation": "Le chiffrement protège la confidentialité des données."
    },
    {
        "id": "CYB013",
        "category": "Cryptographie",
        "difficulty": "moyen",
        "question": "Une fonction de hachage cryptographique sert notamment à :",
        "options": [
            "Créer un tunnel VPN",
            "Attribuer une adresse IP",
            "Produire une empreinte des données",
            "Filtrer les ports réseau"
        ],
        "correct_index": 2,
        "explanation": "Une fonction de hachage calcule une empreinte de taille définie selon l'algorithme."
    },
    {
        "id": "CYB014",
        "category": "Sécurité Web",
        "difficulty": "moyen",
        "question": "Quel risque est associé à une injection SQL ?",
        "options": [
            "Une panne du clavier",
            "Une baisse de résolution d'écran",
            "Une perte de signal Wi-Fi uniquement",
            "Une manipulation non autorisée des requêtes de base de données"
        ],
        "correct_index": 3,
        "explanation": "Une injection SQL peut modifier le sens d'une requête si les entrées sont mal traitées."
    },
    {
        "id": "CYB015",
        "category": "Sécurité Web",
        "difficulty": "moyen",
        "question": "Que signifie XSS en sécurité Web ?",
        "options": [
            "Cross-Site Scripting",
            "Extended Secure System",
            "External Server Storage",
            "Cross-System Security"
        ],
        "correct_index": 0,
        "explanation": "Le XSS consiste à faire exécuter du contenu script injecté dans un contexte Web vulnérable."
    },
    {
        "id": "CYB016",
        "category": "Pentest éthique",
        "difficulty": "facile",
        "question": "Quelle condition est indispensable avant un pentest ?",
        "options": [
            "Désactiver toutes les sauvegardes",
            "Obtenir une autorisation explicite",
            "Publier les mots de passe",
            "Désactiver le pare-feu de tous les systèmes"
        ],
        "correct_index": 1,
        "explanation": "Un test d'intrusion doit être réalisé dans un périmètre autorisé."
    },
    {
        "id": "CYB017",
        "category": "Pentest éthique",
        "difficulty": "moyen",
        "question": "Pourquoi définir un périmètre de test ?",
        "options": [
            "Pour éviter toute documentation",
            "Pour garantir un accès administrateur",
            "Pour préciser les systèmes et actions autorisés",
            "Pour supprimer les journaux"
        ],
        "correct_index": 2,
        "explanation": "Le périmètre définit les cibles, limites et conditions du test."
    },
    {
        "id": "CYB018",
        "category": "Authentification",
        "difficulty": "facile",
        "question": "Quel est l'avantage principal de la MFA ?",
        "options": [
            "Elle supprime le besoin de mises à jour",
            "Elle rend tout hameçonnage impossible",
            "Elle remplace toutes les sauvegardes",
            "Elle ajoute plusieurs facteurs de vérification"
        ],
        "correct_index": 3,
        "explanation": "L'authentification multifacteur combine plusieurs facteurs pour renforcer la protection d'un compte."
    },
    {
        "id": "CYB019",
        "category": "Défense",
        "difficulty": "moyen",
        "question": "Pourquoi conserver des journaux système ?",
        "options": [
            "Pour faciliter la détection et l'analyse d'incidents",
            "Pour accélérer physiquement le processeur",
            "Pour remplacer les correctifs",
            "Pour désactiver l'authentification"
        ],
        "correct_index": 0,
        "explanation": "Les journaux aident à reconstituer les événements et à identifier des activités suspectes."
    },
    {
        "id": "CYB020",
        "category": "Sécurité",
        "difficulty": "facile",
        "question": "Quelle pratique améliore la sécurité des logiciels ?",
        "options": [
            "Ignorer les alertes",
            "Installer les mises à jour de sécurité",
            "Réutiliser le même mot de passe partout",
            "Désactiver les sauvegardes"
        ],
        "correct_index": 1,
        "explanation": "Les mises à jour corrigent notamment des vulnérabilités connues."
    },

    # ============================================================
    # QUESTIONS AJOUTÉES (CYB021 → CYB120)
    # ============================================================

    # ---------- RÉSEAUX ----------
    {
        "id": "CYB021",
        "category": "Réseaux",
        "difficulty": "moyen",
        "question": "Quel est le port par défaut du protocole SSH ?",
        "options": ["21", "22", "23", "25"],
        "correct_index": 1,
        "explanation": "SSH utilise le port TCP 22 par défaut."
    },
    {
        "id": "CYB022",
        "category": "Réseaux",
        "difficulty": "moyen",
        "question": "Quel mécanisme traduit les adresses IP privées en adresse publique ?",
        "options": ["NAT", "DNS", "ARP", "ICMP"],
        "correct_index": 0,
        "explanation": "Le NAT (Network Address Translation) permet à plusieurs machines d'un réseau privé de partager une adresse IP publique."
    },
    {
        "id": "CYB023",
        "category": "Réseaux",
        "difficulty": "moyen",
        "question": "Quel protocole résout une adresse IP en adresse MAC sur un réseau local ?",
        "options": ["DHCP", "ARP", "DNS", "RARP"],
        "correct_index": 1,
        "explanation": "ARP (Address Resolution Protocol) associe une adresse IP à une adresse MAC sur le réseau local."
    },
    {
        "id": "CYB024",
        "category": "Réseaux",
        "difficulty": "facile",
        "question": "Quelle plage d'adresses IP correspond au réseau privé de classe A ?",
        "options": ["192.168.0.0/16", "172.16.0.0/12", "10.0.0.0/8", "127.0.0.0/8"],
        "correct_index": 2,
        "explanation": "La plage 10.0.0.0/8 est réservée aux réseaux privés de classe A."
    },
    {
        "id": "CYB025",
        "category": "Réseaux",
        "difficulty": "moyen",
        "question": "Quel protocole est utilisé pour la résolution d'adresses dans un réseau IPv6 ?",
        "options": ["ARP", "NDP", "DHCP", "RARP"],
        "correct_index": 1,
        "explanation": "NDP (Neighbor Discovery Protocol) remplace ARP en IPv6."
    },
    {
        "id": "CYB026",
        "category": "Réseaux",
        "difficulty": "moyen",
        "question": "Quel outil permet de tester la connectivité d'un hôte distant via ICMP ?",
        "options": ["ping", "tracert", "netstat", "nslookup"],
        "correct_index": 0,
        "explanation": "ping envoie des paquets ICMP Echo Request pour tester la connectivité."
    },
    {
        "id": "CYB027",
        "category": "Réseaux",
        "difficulty": "moyen",
        "question": "Que signifie l'acronyme VLAN ?",
        "options": ["Virtual Local Area Network", "Variable Link Access Network", "Virtual Link Access Node", "Verified Local Area Node"],
        "correct_index": 0,
        "explanation": "Un VLAN est un réseau local virtuel permettant de segmenter un réseau physique."
    },
    {
        "id": "CYB028",
        "category": "Réseaux",
        "difficulty": "difficile",
        "question": "Quelle est la taille d'un en-tête IPv4 minimal (en octets) ?",
        "options": ["16", "20", "24", "32"],
        "correct_index": 1,
        "explanation": "L'en-tête IPv4 minimal fait 20 octets, extensible à 60 octets avec les options."
    },
    {
        "id": "CYB029",
        "category": "Réseaux",
        "difficulty": "moyen",
        "question": "Quel protocole est utilisé pour la messagerie électronique en envoi ?",
        "options": ["POP3", "IMAP", "SMTP", "HTTP"],
        "correct_index": 2,
        "explanation": "SMTP (Simple Mail Transfer Protocol) est utilisé pour envoyer les e-mails."
    },
    {
        "id": "CYB030",
        "category": "Réseaux",
        "difficulty": "moyen",
        "question": "Quel protocole permet de synchroniser les e-mails sans les supprimer du serveur ?",
        "options": ["POP3", "IMAP", "SMTP", "FTP"],
        "correct_index": 1,
        "explanation": "IMAP conserve les e-mails sur le serveur et synchronise l'état entre clients."
    },

    # ---------- LINUX ----------
    {
        "id": "CYB031",
        "category": "Linux",
        "difficulty": "facile",
        "question": "Quelle commande affiche les processus en cours d'exécution ?",
        "options": ["ps", "ls", "df", "du"],
        "correct_index": 0,
        "explanation": "ps (process status) liste les processus actifs ; on l'utilise souvent avec aux ou -ef."
    },
    {
        "id": "CYB032",
        "category": "Linux",
        "difficulty": "facile",
        "question": "Quelle commande change le répertoire courant ?",
        "options": ["ls", "pwd", "cd", "mv"],
        "correct_index": 2,
        "explanation": "cd (change directory) permet de se déplacer dans l'arborescence."
    },
    {
        "id": "CYB033",
        "category": "Linux",
        "difficulty": "moyen",
        "question": "Quelle commande permet de rechercher un motif dans un fichier ?",
        "options": ["find", "grep", "locate", "which"],
        "correct_index": 1,
        "explanation": "grep recherche un motif (expression régulière) dans du texte ou des fichiers."
    },
    {
        "id": "CYB034",
        "category": "Linux",
        "difficulty": "moyen",
        "question": "Que fait la commande chmod 755 fichier ?",
        "options": [
            "Donne tous les droits à tout le monde",
            "Donne rwx au propriétaire, r-x au groupe et aux autres",
            "Rend le fichier exécutable uniquement par root",
            "Supprime le fichier"
        ],
        "correct_index": 1,
        "explanation": "7 = rwx pour le propriétaire, 5 = r-x pour le groupe et les autres."
    },
    {
        "id": "CYB035",
        "category": "Linux",
        "difficulty": "moyen",
        "question": "Quelle commande affiche les droits sudo de l'utilisateur courant ?",
        "options": ["sudo -l", "sudo -v", "sudo -k", "sudo -u"],
        "correct_index": 0,
        "explanation": "sudo -l liste les commandes que l'utilisateur est autorisé à exécuter via sudo."
    },
    {
        "id": "CYB036",
        "category": "Linux",
        "difficulty": "moyen",
        "question": "Quel fichier contient la liste des utilisateurs sous Linux ?",
        "options": ["/etc/group", "/etc/passwd", "/etc/shadow", "/etc/sudoers"],
        "correct_index": 1,
        "explanation": "/etc/passwd contient les informations publiques des comptes utilisateurs."
    },
    {
        "id": "CYB037",
        "category": "Linux",
        "difficulty": "moyen",
        "question": "Où sont stockés les mots de passe hachés sous Linux ?",
        "options": ["/etc/passwd", "/etc/group", "/etc/shadow", "/etc/secure"],
        "correct_index": 2,
        "explanation": "/etc/shadow est lisible uniquement par root et contient les hachages de mots de passe."
    },
    {
        "id": "CYB038",
        "category": "Linux",
        "difficulty": "difficile",
        "question": "Que signifie le bit setuid (s) sur un exécutable ?",
        "options": [
            "L'exécutable s'exécute avec les droits du propriétaire",
            "L'exécutable est supprimé après exécution",
            "L'exécutable est en lecture seule",
            "L'exécutable est ignoré par le système"
        ],
        "correct_index": 0,
        "explanation": "Le bit setuid fait exécuter le programme avec les droits de son propriétaire (souvent root)."
    },
    {
        "id": "CYB039",
        "category": "Linux",
        "difficulty": "moyen",
        "question": "Quelle commande affiche l'utilisation de l'espace disque par système de fichiers ?",
        "options": ["du", "df", "ls", "free"],
        "correct_index": 1,
        "explanation": "df (disk free) affiche l'espace utilisé et disponible par système de fichiers."
    },
    {
        "id": "CYB040",
        "category": "Linux",
        "difficulty": "moyen",
        "question": "Quel répertoire contient traditionnellement les fichiers de configuration système ?",
        "options": ["/var", "/tmp", "/etc", "/opt"],
        "correct_index": 2,
        "explanation": "/etc regroupe les fichiers de configuration du système et des services."
    },

    # ---------- PYTHON ----------
    {
        "id": "CYB041",
        "category": "Python",
        "difficulty": "facile",
        "question": "Quel type Python est immuable et ordonné ?",
        "options": ["list", "dict", "tuple", "set"],
        "correct_index": 2,
        "explanation": "Un tuple est ordonné et immuable, contrairement à une liste."
    },
    {
        "id": "CYB042",
        "category": "Python",
        "difficulty": "facile",
        "question": "Quelle structure Python associe des clés à des valeurs ?",
        "options": ["list", "tuple", "set", "dict"],
        "correct_index": 3,
        "explanation": "Un dictionnaire (dict) associe des clés uniques à des valeurs."
    },
    {
        "id": "CYB043",
        "category": "Python",
        "difficulty": "moyen",
        "question": "Que fait l'instruction with open('fichier') as f: ?",
        "options": [
            "Ouvre le fichier sans le fermer",
            "Ouvre le fichier et le ferme automatiquement à la fin du bloc",
            "Crée un dossier",
            "Supprime le fichier"
        ],
        "correct_index": 1,
        "explanation": "Le contexte with garantit la fermeture du fichier à la sortie du bloc."
    },
    {
        "id": "CYB044",
        "category": "Python",
        "difficulty": "moyen",
        "question": "Quel module Python standard permet de lancer des commandes système ?",
        "options": ["os", "subprocess", "sys", "shutil"],
        "correct_index": 1,
        "explanation": "subprocess est le module recommandé pour exécuter des processus externes."
    },
    {
        "id": "CYB045",
        "category": "Python",
        "difficulty": "moyen",
        "question": "Que fait l'instruction try/except en Python ?",
        "options": [
            "Déclare une fonction",
            "Gère les exceptions",
            "Boucle sur une liste",
            "Importe un module"
        ],
        "correct_index": 1,
        "explanation": "try/except permet d'intercepter et de gérer les exceptions."
    },
    {
        "id": "CYB046",
        "category": "Python",
        "difficulty": "moyen",
        "question": "Quelle est la sortie de print(type(3/2)) en Python 3 ?",
        "options": ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'complex'>"],
        "correct_index": 1,
        "explanation": "En Python 3, la division / renvoie toujours un float."
    },
    {
        "id": "CYB047",
        "category": "Python",
        "difficulty": "moyen",
        "question": "Quel opérateur teste l'identité d'un objet en Python ?",
        "options": ["==", "is", "in", "!="],
        "correct_index": 1,
        "explanation": "is compare l'identité (même objet en mémoire), == compare la valeur."
    },
    {
        "id": "CYB048",
        "category": "Python",
        "difficulty": "difficile",
        "question": "Que fait le décorateur @staticmethod ?",
        "options": [
            "Transforme une méthode en fonction sans accès à self ni cls",
            "Rend la méthode privée",
            "Exécute la méthode à l'import",
            "Rend la méthode asynchrone"
        ],
        "correct_index": 0,
        "explanation": "Une méthode statique n'a pas accès à l'instance (self) ni à la classe (cls)."
    },
    {
        "id": "CYB049",
        "category": "Python",
        "difficulty": "moyen",
        "question": "Quelle bibliothèque Python standard permet de hacher des données ?",
        "options": ["hashlib", "hash", "hmac", "os"],
        "correct_index": 0,
        "explanation": "hashlib fournit MD5, SHA-1, SHA-256, etc. pour le hachage cryptographique."
    },
    {
        "id": "CYB050",
        "category": "Python",
        "difficulty": "moyen",
        "question": "Quel module standard gère les sockets réseau en Python ?",
        "options": ["socket", "http", "urllib", "requests"],
        "correct_index": 0,
        "explanation": "socket est le module bas niveau pour créer et manipuler des sockets réseau."
    },

    # ---------- CRYPTOGRAPHIE ----------
    {
        "id": "CYB051",
        "category": "Cryptographie",
        "difficulty": "moyen",
        "question": "Quel algorithme est un chiffrement symétrique ?",
        "options": ["RSA", "AES", "ECDSA", "Diffie-Hellman"],
        "correct_index": 1,
        "explanation": "AES est symétrique (même clé pour chiffrer/déchiffrer), contrairement à RSA qui est asymétrique."
    },
    {
        "id": "CYB052",
        "category": "Cryptographie",
        "difficulty": "moyen",
        "question": "Quel algorithme de hachage est considéré comme obsolète et non sécurisé ?",
        "options": ["SHA-256", "SHA-3", "MD5", "BLAKE2"],
        "correct_index": 2,
        "explanation": "MD5 est cassé (collisions faciles) et ne doit plus être utilisé pour la sécurité."
    },
    {
        "id": "CYB053",
        "category": "Cryptographie",
        "difficulty": "moyen",
        "question": "Quel protocole permet l'échange de clés sur un canal non sécurisé ?",
        "options": ["Diffie-Hellman", "AES", "SHA-256", "HMAC"],
        "correct_index": 0,
        "explanation": "Diffie-Hellman permet à deux parties de négocier une clé commune sans la transmettre."
    },
    {
        "id": "CYB054",
        "category": "Cryptographie",
        "difficulty": "moyen",
        "question": "Que protège un certificat X.509 ?",
        "options": [
            "La confidentialité d'un mot de passe",
            "L'authenticité d'une clé publique",
            "La vitesse du réseau",
            "La taille des fichiers"
        ],
        "correct_index": 1,
        "explanation": "Un certificat X.509 lie une clé publique à une identité, signé par une autorité de certification."
    },
    {
        "id": "CYB055",
        "category": "Cryptographie",
        "difficulty": "moyen",
        "question": "À quoi sert un HMAC ?",
        "options": [
            "Chiffrer un fichier",
            "Vérifier l'intégrité et l'authenticité d'un message",
            "Générer une paire de clés",
            "Créer un tunnel VPN"
        ],
        "correct_index": 1,
        "explanation": "HMAC combine une fonction de hachage et une clé secrète pour authentifier un message."
    },
    {
        "id": "CYB056",
        "category": "Cryptographie",
        "difficulty": "difficile",
        "question": "Quel est le principal avantage de la cryptographie asymétrique ?",
        "options": [
            "Elle est plus rapide que la symétrique",
            "Elle permet l'échange de clés sans secret partagé préalable",
            "Elle ne nécessite aucune clé",
            "Elle empêche toute attaque par force brute"
        ],
        "correct_index": 1,
        "explanation": "L'asymétrie permet de communiquer sans partager de secret au préalable (clé publique/privée)."
    },
    {
        "id": "CYB057",
        "category": "Cryptographie",
        "difficulty": "moyen",
        "question": "Quelle longueur de clé RSA est aujourd'hui considérée comme minimale pour la sécurité ?",
        "options": ["512 bits", "1024 bits", "2048 bits", "128 bits"],
        "correct_index": 2,
        "explanation": "2048 bits est le minimum recommandé actuellement ; 4096 bits pour une sécurité accrue."
    },
    {
        "id": "CYB058",
        "category": "Cryptographie",
        "difficulty": "moyen",
        "question": "Que signifie l'acronyme PKI ?",
        "options": [
            "Public Key Infrastructure",
            "Private Key Interface",
            "Public Key Integrity",
            "Private Key Infrastructure"
        ],
        "correct_index": 0,
        "explanation": "PKI désigne l'infrastructure de gestion des clés publiques et des certificats."
    },
    {
        "id": "CYB059",
        "category": "Cryptographie",
        "difficulty": "difficile",
        "question": "Quel mode opératoire AES assure à la fois confidentialité et authenticité ?",
        "options": ["ECB", "CBC", "GCM", "CFB"],
        "correct_index": 2,
        "explanation": "AES-GCM combine chiffrement et authentification (AEAD)."
    },
    {
        "id": "CYB060",
        "category": "Cryptographie",
        "difficulty": "moyen",
        "question": "Quelle attaque exploite la réutilisation d'un même nonce/IV ?",
        "options": [
            "Attaque par force brute",
            "Attaque par réutilisation de nonce",
            "Attaque par dictionnaire",
            "Attaque par déni de service"
        ],
        "correct_index": 1,
        "explanation": "Réutiliser un nonce/IV peut casser la confidentialité (ex : keystream réutilisé en stream cipher)."
    },

    # ---------- SÉCURITÉ WEB ----------
    {
        "id": "CYB061",
        "category": "Sécurité Web",
        "difficulty": "moyen",
        "question": "Quelle attaque exploite la confiance d'un site envers le navigateur de l'utilisateur ?",
        "options": ["CSRF", "SQLi", "XSS", "LFI"],
        "correct_index": 0,
        "explanation": "Le CSRF pousse la victime à exécuter une action authentifiée à son insu."
    },
    {
        "id": "CYB062",
        "category": "Sécurité Web",
        "difficulty": "moyen",
        "question": "Quel en-tête HTTP limite l'exécution de scripts à des sources de confiance ?",
        "options": [
            "Content-Security-Policy",
            "X-Frame-Options",
            "Strict-Transport-Security",
            "Referrer-Policy"
        ],
        "correct_index": 0,
        "explanation": "La CSP (Content-Security-Policy) restreint les sources de scripts, styles, etc."
    },
    {
        "id": "CYB063",
        "category": "Sécurité Web",
        "difficulty": "moyen",
        "question": "Quelle attaque vise à injecter du code dans une base de données ?",
        "options": ["XSS", "CSRF", "SQL Injection", "SSRF"],
        "correct_index": 2,
        "explanation": "L'injection SQL exploite une entrée non échappée pour manipuler la requête."
    },
    {
        "id": "CYB064",
        "category": "Sécurité Web",
        "difficulty": "moyen",
        "question": "Que signifie SSRF ?",
        "options": [
            "Server-Side Request Forgery",
            "Secure Socket Relay Forward",
            "Server Side Remote Firewall",
            "Symmetric Shared Random File"
        ],
        "correct_index": 0,
        "explanation": "SSRF pousse le serveur à effectuer des requêtes vers des ressources internes ou externes non prévues."
    },
    {
        "id": "CYB065",
        "category": "Sécurité Web",
        "difficulty": "moyen",
        "question": "Quel en-tête HTTP force l'utilisation de HTTPS ?",
        "options": [
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "Access-Control-Allow-Origin"
        ],
        "correct_index": 1,
        "explanation": "HSTS (Strict-Transport-Security) impose HTTPS pour les connexions futures."
    },
    {
        "id": "CYB066",
        "category": "Sécurité Web",
        "difficulty": "moyen",
        "question": "Que protège l'attribut HttpOnly sur un cookie ?",
        "options": [
            "Contre l'accès au cookie par JavaScript",
            "Contre l'envoi du cookie sur HTTP",
            "Contre le vol du cookie par sniffing",
            "Contre les attaques par force brute"
        ],
        "correct_index": 0,
        "explanation": "HttpOnly empêche l'accès au cookie via document.cookie en JavaScript."
    },
    {
        "id": "CYB067",
        "category": "Sécurité Web",
        "difficulty": "moyen",
        "question": "Quelle vulnérabilité permet de lire des fichiers arbitraires sur le serveur ?",
        "options": ["LFI", "XSS", "CSRF", "SSRF"],
        "correct_index": 0,
        "explanation": "LFI (Local File Inclusion) permet d'inclure des fichiers locaux non prévus."
    },
    {
        "id": "CYB068",
        "category": "Sécurité Web",
        "difficulty": "moyen",
        "question": "Quelle attaque consiste à intercepter et modifier les échanges entre deux parties ?",
        "options": ["Man-in-the-Middle", "Phishing", "Brute force", "DDoS"],
        "correct_index": 0,
        "explanation": "Le MITM place l'attaquant entre les deux parties pour intercepter ou modifier le trafic."
    },
    {
        "id": "CYB069",
        "category": "Sécurité Web",
        "difficulty": "moyen",
        "question": "Quel est le rôle de l'en-tête CORS ?",
        "options": [
            "Contrôler les requêtes cross-origin",
            "Chiffrer les cookies",
            "Bloquer les virus",
            "Compresser les réponses"
        ],
        "correct_index": 0,
        "explanation": "CORS (Cross-Origin Resource Sharing) définit les règles d'accès aux ressources entre origines."
    },
    {
        "id": "CYB070",
        "category": "Sécurité Web",
        "difficulty": "difficile",
        "question": "Quelle attaque exploite la désérialisation non sécurisée de données ?",
        "options": [
            "Insecure Deserialization",
            "XSS stocké",
            "CSRF",
            "Clickjacking"
        ],
        "correct_index": 0,
        "explanation": "La désérialisation non sécurisée peut mener à l'exécution de code arbitraire."
    },

    # ---------- PENTEST ÉTHIQUE ----------
    {
        "id": "CYB071",
        "category": "Pentest éthique",
        "difficulty": "facile",
        "question": "Que signifie l'acronyme PTES ?",
        "options": [
            "Penetration Testing Execution Standard",
            "Public Test Evaluation System",
            "Protocol Test Execution Suite",
            "Private Threat Evaluation Standard"
        ],
        "correct_index": 0,
        "explanation": "PTES est un standard décrivant les phases d'un test d'intrusion."
    },
    {
        "id": "CYB072",
        "category": "Pentest éthique",
        "difficulty": "moyen",
        "question": "Quelle est la première phase d'un pentest ?",
        "options": ["Exploitation", "Reconnaissance", "Post-exploitation", "Rapport"],
        "correct_index": 1,
        "explanation": "La reconnaissance (passive ou active) précède toute exploitation."
    },
    {
        "id": "CYB073",
        "category": "Pentest éthique",
        "difficulty": "moyen",
        "question": "Quel outil est couramment utilisé pour scanner les ports ?",
        "options": ["Nmap", "Wireshark", "Metasploit", "Burp Suite"],
        "correct_index": 0,
        "explanation": "Nmap est l'outil de référence pour le scan de ports et la découverte réseau."
    },
    {
        "id": "CYB074",
        "category": "Pentest éthique",
        "difficulty": "moyen",
        "question": "Que signifie un test en 'boîte noire' ?",
        "options": [
            "Le testeur connaît tout du système",
            "Le testeur n'a aucune information préalable",
            "Le test est réalisé sans autorisation",
            "Le test est réalisé en production"
        ],
        "correct_index": 1,
        "explanation": "En boîte noire, le testeur n'a aucune information sur la cible."
    },
    {
        "id": "CYB075",
        "category": "Pentest éthique",
        "difficulty": "moyen",
        "question": "Quel document définit le périmètre et les conditions d'un pentest ?",
        "options": [
            "Rapport de test",
            "Contrat / lettre d'engagement",
            "Note de synthèse",
            "Plan de remédiation"
        ],
        "correct_index": 1,
        "explanation": "La lettre d'engagement (rules of engagement) encadre juridiquement le test."
    },
    {
        "id": "CYB076",
        "category": "Pentest éthique",
        "difficulty": "moyen",
        "question": "Quel outil est spécialisé dans l'exploitation de vulnérabilités ?",
        "options": ["Nmap", "Metasploit", "Wireshark", "John the Ripper"],
        "correct_index": 1,
        "explanation": "Metasploit Framework permet de développer et lancer des exploits."
    },
    {
        "id": "CYB077",
        "category": "Pentest éthique",
        "difficulty": "moyen",
        "question": "Que signifie une phase de post-exploitation ?",
        "options": [
            "La découverte des services",
            "L'exploitation initiale",
            "Le maintien de l'accès et l'élévation de privilèges",
            "La rédaction du rapport"
        ],
        "correct_index": 2,
        "explanation": "La post-exploitation consiste à maintenir l'accès, pivoter et élever les privilèges."
    },
    {
        "id": "CYB078",
        "category": "Pentest éthique",
        "difficulty": "moyen",
        "question": "Quel outil est un proxy d'interception pour tester les applications web ?",
        "options": ["Burp Suite", "Nmap", "Wireshark", "Aircrack-ng"],
        "correct_index": 0,
        "explanation": "Burp Suite est un proxy d'interception dédié aux tests web."
    },
    {
        "id": "CYB079",
        "category": "Pentest éthique",
        "difficulty": "difficile",
        "question": "Que signifie un test en 'boîte grise' ?",
        "options": [
            "Le testeur connaît tout",
            "Le testeur n'a aucune information",
            "Le testeur a des informations partielles",
            "Le test est réalisé sans autorisation"
        ],
        "correct_index": 2,
        "explanation": "En boîte grise, le testeur dispose d'informations partielles sur la cible."
    },
    {
        "id": "CYB080",
        "category": "Pentest éthique",
        "difficulty": "moyen",
        "question": "Quelle est la finalité d'un rapport de pentest ?",
        "options": [
            "Publier les vulnérabilités",
            "Documenter les failles et proposer des remédiations",
            "Tester la vitesse du réseau",
            "Former les utilisateurs"
        ],
        "correct_index": 1,
        "explanation": "Le rapport documente les vulnérabilités trouvées et propose des remédiations priorisées."
    },

    # ---------- AUTHENTIFICATION ----------
    {
        "id": "CYB081",
        "category": "Authentification",
        "difficulty": "facile",
        "question": "Quel facteur d'authentification est basé sur ce que l'on possède ?",
        "options": [
            "Mot de passe",
            "Empreinte digitale",
            "Token matériel",
            "Question secrète"
        ],
        "correct_index": 2,
        "explanation": "Un token matériel (ex : YubiKey) est un facteur de possession."
    },
    {
        "id": "CYB082",
        "category": "Authentification",
        "difficulty": "moyen",
        "question": "Que signifie l'acronyme FIDO2 ?",
        "options": [
            "Fast Identity Online 2",
            "Federated Identity Data Object 2",
            "File Integrity Detection Online 2",
            "Forward Identity Object 2"
        ],
        "correct_index": 0,
        "explanation": "FIDO2 est un standard d'authentification sans mot de passe (WebAuthn + CTAP)."
    },
    {
        "id": "CYB083",
        "category": "Authentification",
        "difficulty": "moyen",
        "question": "Quelle attaque vise à deviner un mot de passe par essais successifs ?",
        "options": ["Phishing", "Brute force", "MITM", "CSRF"],
        "correct_index": 1,
        "explanation": "Le brute force teste systématiquement toutes les combinaisons possibles."
    },
    {
        "id": "CYB084",
        "category": "Authentification",
        "difficulty": "moyen",
        "question": "Que fait un gestionnaire de mots de passe ?",
        "options": [
            "Génère et stocke des mots de passe de façon chiffrée",
            "Bloque les virus",
            "Remplace l'authentification multifacteur",
            "Supprime les cookies"
        ],
        "correct_index": 0,
        "explanation": "Un gestionnaire chiffre et centralise les mots de passe pour éviter leur réutilisation."
    },
    {
        "id": "CYB085",
        "category": "Authentification",
        "difficulty": "moyen",
        "question": "Quel protocole est souvent utilisé pour l'authentification centralisée en entreprise ?",
        "options": ["LDAP", "SMTP", "FTP", "ICMP"],
        "correct_index": 0,
        "explanation": "LDAP est un annuaire utilisé pour l'authentification et les autorisations."
    },
    {
        "id": "CYB086",
        "category": "Authentification",
        "difficulty": "moyen",
        "question": "Que signifie OAuth 2.0 ?",
        "options": [
            "Un protocole d'autorisation déléguée",
            "Un algorithme de chiffrement",
            "Un pare-feu applicatif",
            "Un protocole de routage"
        ],
        "correct_index": 0,
        "explanation": "OAuth 2.0 est un cadre d'autorisation déléguée (pas un protocole d'authentification à proprement parler)."
    },
    {
        "id": "CYB087",
        "category": "Authentification",
        "difficulty": "moyen",
        "question": "Que signifie SSO ?",
        "options": [
            "Single Sign-On",
            "Secure Socket Object",
            "System Security Officer",
            "Shared Service Object"
        ],
        "correct_index": 0,
        "explanation": "Le SSO permet à un utilisateur de s'authentifier une seule fois pour accéder à plusieurs services."
    },
    {
        "id": "CYB088",
        "category": "Authentification",
        "difficulty": "moyen",
        "question": "Quel type de facteur est la reconnaissance faciale ?",
        "options": [
            "Ce que je sais",
            "Ce que je possède",
            "Ce que je suis (biométrie)",
            "Ce que je fais"
        ],
        "correct_index": 2,
        "explanation": "La biométrie repose sur des caractéristiques physiques ou comportementales."
    },
    {
        "id": "CYB089",
        "category": "Authentification",
        "difficulty": "difficile",
        "question": "Quelle attaque consiste à intercepter un cookie de session pour usurper l'identité ?",
        "options": [
            "Session hijacking",
            "Clickjacking",
            "Phishing",
            "Smurf attack"
        ],
        "correct_index": 0,
        "explanation": "Le session hijacking vole ou devine un identifiant de session pour prendre la main sur une session authentifiée."
    },
    {
        "id": "CYB090",
        "category": "Authentification",
        "difficulty": "moyen",
        "question": "Quel est le rôle d'un TOTP ?",
        "options": [
            "Générer un code à usage unique basé sur le temps",
            "Chiffrer un fichier",
            "Router les paquets",
            "Bloquer les ports"
        ],
        "correct_index": 0,
        "explanation": "TOTP (Time-based One-Time Password) génère un code à durée limitée pour la MFA."
    },

    # ---------- DÉFENSE / SOC ----------
    {
        "id": "CYB091",
        "category": "Défense",
        "difficulty": "moyen",
        "question": "Que signifie l'acronyme SIEM ?",
        "options": [
            "Security Information and Event Management",
            "System Integrity and Event Monitor",
            "Secure Incident Emergency Management",
            "Server Information and Event Module"
        ],
        "correct_index": 0,
        "explanation": "Un SIEM collecte et corrèle les journaux pour détecter les incidents."
    },
    {
        "id": "CYB092",
        "category": "Défense",
        "difficulty": "moyen",
        "question": "Quel est le rôle d'un IDS ?",
        "options": [
            "Bloquer activement les attaques",
            "Détecter les activités suspectes",
            "Chiffrer le trafic",
            "Attribuer les adresses IP"
        ],
        "correct_index": 1,
        "explanation": "Un IDS (Intrusion Detection System) détecte et alerte, sans bloquer par défaut (contrairement à l'IPS)."
    },
    {
        "id": "CYB093",
        "category": "Défense",
        "difficulty": "moyen",
        "question": "Quelle est la différence entre un IDS et un IPS ?",
        "options": [
            "Aucune, ce sont des synonymes",
            "L'IPS bloque activement, l'IDS se contente de détecter",
            "L'IDS chiffre le trafic",
            "L'IPS est un antivirus"
        ],
        "correct_index": 1,
        "explanation": "L'IPS (Intrusion Prevention System) bloque, alors que l'IDS alerte."
    },
    {
        "id": "CYB094",
        "category": "Défense",
        "difficulty": "moyen",
        "question": "Que signifie la défense en profondeur ?",
        "options": [
            "Utiliser plusieurs couches de sécurité indépendantes",
            "Avoir un seul pare-feu très puissant",
            "Désactiver tous les services inutiles",
            "Chiffrer uniquement les mots de passe"
        ],
        "correct_index": 0,
        "explanation": "La défense en profondeur superpose plusieurs mesures pour qu'une seule faille ne compromette pas tout."
    },
    {
        "id": "CYB095",
        "category": "Défense",
        "difficulty": "moyen",
        "question": "Que signifie l'acronyme EDR ?",
        "options": [
            "Endpoint Detection and Response",
            "Enterprise Data Recovery",
            "Encrypted Data Routing",
            "External Data Repository"
        ],
        "correct_index": 0,
        "explanation": "EDR désigne les solutions de détection et réponse sur les postes de travail."
    },
    {
        "id": "CYB096",
        "category": "Défense",
        "difficulty": "moyen",
        "question": "Quel est le principe du moindre privilège ?",
        "options": [
            "Accorder tous les droits aux administrateurs",
            "Accorder uniquement les droits nécessaires à chaque tâche",
            "Désactiver les comptes inactifs",
            "Chiffrer les mots de passe"
        ],
        "correct_index": 1,
        "explanation": "Le moindre privilège limite les droits au strict nécessaire pour réduire la surface d'attaque."
    },
    {
        "id": "CYB097",
        "category": "Défense",
        "difficulty": "moyen",
        "question": "Que fait un honeypot ?",
        "options": [
            "Attire et observe les attaquants",
            "Bloque tous les paquets",
            "Chiffre les données",
            "Sauvegarde les fichiers"
        ],
        "correct_index": 0,
        "explanation": "Un honeypot est un leurre destiné à attirer et analyser les attaques."
    },
    {
        "id": "CYB098",
        "category": "Défense",
        "difficulty": "moyen",
        "question": "Quelle est la première étape de la réponse à incident ?",
        "options": [
            "Éradication",
            "Détection et identification",
            "Restauration",
            "Leçons apprises"
        ],
        "correct_index": 1,
        "explanation": "La réponse à incident commence par la détection et l'identification de l'incident."
    },
    {
        "id": "CYB099",
        "category": "Défense",
        "difficulty": "moyen",
        "question": "Que signifie l'acronyme SOC ?",
        "options": [
            "Security Operations Center",
            "System Operations Code",
            "Secure Online Console",
            "Server Object Container"
        ],
        "correct_index": 0,
        "explanation": "Un SOC est un centre opérationnel de sécurité qui surveille et répond aux incidents."
    },
    {
        "id": "CYB100",
        "category": "Défense",
        "difficulty": "difficile",
        "question": "Qu'est-ce que le MITRE ATT&CK ?",
        "options": [
            "Une base de connaissances des tactiques et techniques adverses",
            "Un pare-feu open source",
            "Un algorithme de chiffrement",
            "Un protocole de routage"
        ],
        "correct_index": 0,
        "explanation": "MITRE ATT&CK est une base de connaissances des TTP des attaquants."
    },

    # ---------- SÉCURITÉ GÉNÉRALE / MALWARE ----------
    {
        "id": "CYB101",
        "category": "Sécurité",
        "difficulty": "facile",
        "question": "Qu'est-ce qu'un ransomware ?",
        "options": [
            "Un logiciel qui chiffre les données et exige une rançon",
            "Un antivirus",
            "Un protocole réseau",
            "Un type de pare-feu"
        ],
        "correct_index": 0,
        "explanation": "Un ransomware chiffre les données de la victime et demande un paiement pour la clé."
    },
    {
        "id": "CYB102",
        "category": "Sécurité",
        "difficulty": "moyen",
        "question": "Qu'est-ce qu'un cheval de Troie ?",
        "options": [
            "Un logiciel malveillant se faisant passer pour un programme légitime",
            "Un virus qui se réplique seul",
            "Un ver réseau",
            "Un outil d'analyse"
        ],
        "correct_index": 0,
        "explanation": "Un trojan se cache dans un logiciel d'apparence légitime pour exécuter des actions malveillantes."
    },
    {
        "id": "CYB103",
        "category": "Sécurité",
        "difficulty": "moyen",
        "question": "Quelle est la différence entre un virus et un ver ?",
        "options": [
            "Aucune",
            "Le ver se propage seul via le réseau, le virus a besoin d'un hôte",
            "Le virus est toujours inoffensif",
            "Le ver ne se propage pas"
        ],
        "correct_index": 1,
        "explanation": "Un ver se propage automatiquement via le réseau, un virus nécessite un hôte pour s'exécuter."
    },
    {
        "id": "CYB104",
        "category": "Sécurité",
        "difficulty": "moyen",
        "question": "Que signifie l'acronyme APT ?",
        "options": [
            "Advanced Persistent Threat",
            "Automatic Packet Transfer",
            "Advanced Protocol Test",
            "Application Performance Tool"
        ],
        "correct_index": 0,
        "explanation": "Une APT est un acteur menaçant sophistiqué et persistant."
    },
    {
        "id": "CYB105",
        "category": "Sécurité",
        "difficulty": "moyen",
        "question": "Qu'est-ce qu'une attaque par déni de service (DoS) ?",
        "options": [
            "Voler des données",
            "Rendre un service indisponible",
            "Chiffrer les fichiers",
            "Usurper une identité"
        ],
        "correct_index": 1,
        "explanation": "Le DoS vise à rendre un service indisponible en saturant ses ressources."
    },
    {
        "id": "CYB106",
        "category": "Sécurité",
        "difficulty": "moyen",
        "question": "Quel type de malware se cache dans le noyau du système ?",
        "options": ["Rootkit", "Adware", "Spyware", "Ransomware"],
        "correct_index": 0,
        "explanation": "Un rootkit s'installe en profondeur (souvent au niveau noyau) pour masquer sa présence."
    },
    {
        "id": "CYB107",
        "category": "Sécurité",
        "difficulty": "moyen",
        "question": "Qu'est-ce qu'un keylogger ?",
        "options": [
            "Un outil qui enregistre les frappes clavier",
            "Un antivirus",
            "Un pare-feu",
            "Un protocole de chiffrement"
        ],
        "correct_index": 0,
        "explanation": "Un keylogger capture les frappes clavier pour voler des informations sensibles."
    },
    {
        "id": "CYB108",
        "category": "Sécurité",
        "difficulty": "moyen",
        "question": "Qu'est-ce que le phishing ?",
        "options": [
            "Une technique d'hameçonnage par tromperie",
            "Une attaque réseau par saturation",
            "Un chiffrement des fichiers",
            "Un scan de ports"
        ],
        "correct_index": 0,
        "explanation": "Le phishing (hameçonnage) trompe la victime pour lui faire divulguer des informations."
    },
    {
        "id": "CYB109",
        "category": "Sécurité",
        "difficulty": "moyen",
        "question": "Que signifie l'acronyme CVE ?",
        "options": [
            "Common Vulnerabilities and Exposures",
            "Cyber Vulnerability Exploit",
            "Common Virus Engine",
            "Critical Vulnerability Entry"
        ],
        "correct_index": 0,
        "explanation": "Une CVE est un identifiant public pour une vulnérabilité connue."
    },
    {
        "id": "CYB110",
        "category": "Sécurité",
        "difficulty": "moyen",
        "question": "Que mesure un score CVSS ?",
        "options": [
            "La gravité d'une vulnérabilité",
            "La vitesse du réseau",
            "La taille d'un fichier",
            "Le nombre d'utilisateurs"
        ],
        "correct_index": 0,
        "explanation": "CVSS (Common Vulnerability Scoring System) évalue la gravité d'une vulnérabilité (0 à 10)."
    },

    # ---------- CLOUD / DIVERS ----------
    {
        "id": "CYB111",
        "category": "Cloud",
        "difficulty": "moyen",
        "question": "Quel modèle cloud fournit une infrastructure à la demande ?",
        "options": ["IaaS", "PaaS", "SaaS", "FaaS"],
        "correct_index": 0,
        "explanation": "IaaS (Infrastructure as a Service) fournit des ressources d'infrastructure virtualisées."
    },
    {
        "id": "CYB112",
        "category": "Cloud",
        "difficulty": "moyen",
        "question": "Que signifie une mauvaise configuration de bucket S3 ?",
        "options": [
            "Un risque d'exposition de données",
            "Une accélération du stockage",
            "Un chiffrement automatique",
            "Une amélioration de la disponibilité"
        ],
        "correct_index": 0,
        "explanation": "Un bucket public mal configuré peut exposer des données sensibles."
    },
    {
        "id": "CYB113",
        "category": "Cloud",
        "difficulty": "moyen",
        "question": "Que signifie le principe de responsabilité partagée dans le cloud ?",
        "options": [
            "Le fournisseur est responsable de tout",
            "Le client est responsable de tout",
            "Les responsabilités sont réparties entre fournisseur et client",
            "Personne n'est responsable"
        ],
        "correct_index": 2,
        "explanation": "Le fournisseur sécurise l'infrastructure, le client sécurise ses données et configurations."
    },
    {
        "id": "CYB114",
        "category": "Cloud",
        "difficulty": "moyen",
        "question": "Quel service AWS permet la gestion des identités et des accès ?",
        "options": ["IAM", "S3", "EC2", "VPC"],
        "correct_index": 0,
        "explanation": "AWS IAM gère les utilisateurs, rôles et politiques d'accès."
    },
    {
        "id": "CYB115",
        "category": "Cloud",
        "difficulty": "moyen",
        "question": "Que signifie le chiffrement au repos ?",
        "options": [
            "Chiffrement des données stockées",
            "Chiffrement des données en transit",
            "Chiffrement des mots de passe",
            "Chiffrement du noyau"
        ],
        "correct_index": 0,
        "explanation": "Le chiffrement au repos protège les données stockées (disques, sauvegardes, buckets…)."
    },
    {
        "id": "CYB116",
        "category": "Réseaux",
        "difficulty": "moyen",
        "question": "Quel protocole est utilisé pour la synchronisation horaire ?",
        "options": ["NTP", "SNMP", "SMTP", "DNS"],
        "correct_index": 0,
        "explanation": "NTP (Network Time Protocol) synchronise les horloges des systèmes."
    },
    {
        "id": "CYB117",
        "category": "Réseaux",
        "difficulty": "moyen",
        "question": "Que signifie une attaque par empoisonnement ARP ?",
        "options": [
            "Corrompre la table ARP pour rediriger le trafic",
            "Saturer un serveur",
            "Voler un mot de passe",
            "Chiffrer un fichier"
        ],
        "correct_index": 0,
        "explanation": "L'ARP spoofing permet une attaque MITM en associant une IP à une MAC malveillante."
    },
    {
        "id": "CYB118",
        "category": "Sécurité Web",
        "difficulty": "moyen",
        "question": "Que signifie une attaque par clickjacking ?",
        "options": [
            "Tromper l'utilisateur pour qu'il clique sur un élément invisible",
            "Voler des cookies",
            "Saturer un serveur",
            "Chiffrer des fichiers"
        ],
        "correct_index": 0,
        "explanation": "Le clickjacking superpose des éléments invisibles pour détourner les clics de l'utilisateur."
    },
    {
        "id": "CYB119",
        "category": "Défense",
        "difficulty": "moyen",
        "question": "Quel est l'intérêt d'une politique de sauvegarde 3-2-1 ?",
        "options": [
            "Avoir 3 copies, sur 2 supports différents, dont 1 hors site",
            "Avoir 3 serveurs, 2 pare-feux, 1 antivirus",
            "Avoir 3 mots de passe, 2 facteurs, 1 utilisateur",
            "Avoir 3 VLAN, 2 routeurs, 1 switch"
        ],
        "correct_index": 0,
        "explanation": "La règle 3-2-1 garantit la résilience des sauvegardes face aux sinistres."
    },
    {
        "id": "CYB120",
        "category": "Sécurité",
        "difficulty": "facile",
        "question": "Quelle est la meilleure pratique pour un mot de passe ?",
        "options": [
            "Le réutiliser partout",
            "Le partager avec ses collègues",
            "Utiliser une phrase de passe longue et unique",
            "Le noter sur un post-it"
        ],
        "correct_index": 2,
        "explanation": "Une phrase de passe longue et unique par service est recommandée, idéalement via un gestionnaire."
    }
]

# ============================================================
# BASE DE DONNÉES SQLITE
# ============================================================

def db_connect():
    db = sqlite3.connect(DB_PATH, timeout=15)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with db_connect() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER NOT NULL DEFAULT 0,
                correct INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL DEFAULT 0,
                streak INTEGER NOT NULL DEFAULT 0,
                last_date TEXT
            );

            CREATE TABLE IF NOT EXISTS quizzes (
                quiz_date TEXT PRIMARY KEY,
                question_id TEXT NOT NULL,
                message_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS answers (
                user_id INTEGER NOT NULL,
                quiz_date TEXT NOT NULL,
                choice INTEGER NOT NULL,
                correct INTEGER NOT NULL,
                PRIMARY KEY (user_id, quiz_date)
            );
        """)


def level_for_xp(xp):
    return xp // 100 + 1


def xp_for_question(difficulty):
    return {
        "facile": 10,
        "moyen": 20,
        "difficile": 30,
        "expert": 40,
    }.get(difficulty.lower(), 10)


def get_question_for_message(message_id):
    """Retourne (question, quiz_key) à partir de l'id du message du quiz."""
    with db_connect() as db:
        row = db.execute(
            "SELECT question_id, quiz_date FROM quizzes WHERE message_id = ?",
            (message_id,)
        ).fetchone()

    if row is None:
        return None, None

    question = next(
        (q for q in QUESTIONS if q["id"] == row["question_id"]),
        None
    )
    return question, row["quiz_date"]


def save_answer(user_id, quiz_key, choice, question):
    correct = int(choice == question["correct_index"])
    gained = xp_for_question(question["difficulty"]) if correct else 0

    with db_connect() as db:
        inserted = db.execute("""
            INSERT OR IGNORE INTO answers
                (user_id, quiz_date, choice, correct)
            VALUES (?, ?, ?, ?)
        """, (user_id, quiz_key, choice, correct))

        if inserted.rowcount == 0:
            return None

        db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,)
        )

        user = db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        # quiz_key peut être "2026-10-29" ou "2026-10-29#2"
        base_date = quiz_key.split("#")[0]
        yesterday = (
            date.fromisoformat(base_date) - timedelta(days=1)
        ).isoformat()

        streak = (
            user["streak"] + 1
            if user["last_date"] == yesterday
            else 1
        )

        db.execute("""
            UPDATE users
            SET xp = xp + ?,
                correct = correct + ?,
                total = total + 1,
                streak = ?,
                last_date = ?
            WHERE user_id = ?
        """, (gained, correct, streak, base_date, user_id))

    return {
        "correct": bool(correct),
        "xp": gained,
        "streak": streak,
    }


# ============================================================
# INTERFACE DISCORD
# ============================================================

class AnswerButton(discord.ui.Button):
    def __init__(self, index):
        super().__init__(
            label=["A", "B", "C", "D"][index],
            style=discord.ButtonStyle.primary,
            custom_id=f"cyberquiz:answer:{index}"
        )
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        # On identifie le quiz via le message sur lequel l'utilisateur clique
        question, quiz_key = get_question_for_message(interaction.message.id)

        if question is None:
            await interaction.response.send_message(
                "Aucun quiz actif pour ce message.",
                ephemeral=True
            )
            return

        result = save_answer(
            interaction.user.id,
            quiz_key,
            self.index,
            question
        )

        if result is None:
            await interaction.response.send_message(
                "Tu as déjà répondu à ce quiz.",
                ephemeral=True
            )
            return

        correct_answer = question["options"][question["correct_index"]]

        if result["correct"]:
            title = f"Bonne réponse ! +{result['xp']} XP"
        else:
            title = "Mauvaise réponse"

        await interaction.response.send_message(
            f"**{title}**\n"
            f"Réponse correcte : {correct_answer}\n\n"
            f"{question['explanation']}\n\n"
            f"Série de participation : {result['streak']} jour(s).",
            ephemeral=True
        )


class AnswerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for i in range(4):
            self.add_item(AnswerButton(i))


# ============================================================
# BOT
# ============================================================

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


async def publish_quiz(force: bool = False):
    """Publie le quiz du jour.

    - force=False : ne publie rien si un quiz existe déjà pour aujourd'hui.
    - force=True  : publie un nouveau quiz même si un quiz existe déjà,
                    en générant une clé unique (ex : "2026-10-29#2").
    """
    today = datetime.now(TIMEZONE).date().isoformat()

    if force:
        with db_connect() as db:
            count = db.execute(
                "SELECT COUNT(*) AS n FROM quizzes WHERE quiz_date LIKE ?",
                (f"{today}%",)
            ).fetchone()["n"]
        quiz_key = f"{today}#{count + 1}"
        offset = count
    else:
        with db_connect() as db:
            exists = db.execute(
                "SELECT 1 FROM quizzes WHERE quiz_date = ?",
                (today,)
            ).fetchone()
        if exists:
            return False
        quiz_key = today
        offset = 0

    if not QUESTIONS:
        log.error("La banque de questions est vide.")
        return False

    if CHANNEL_ID == 0:
        log.error("Configure CHANNEL_ID dans le code.")
        return False

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(CHANNEL_ID)
        except discord.Forbidden as exc:
            raise RuntimeError(
                f"Accès refusé au salon {CHANNEL_ID}. Vérifie que le bot est "
                "sur le bon serveur et possède les permissions Voir le salon, "
                "Envoyer des messages et Intégrer des liens."
            ) from exc
        except discord.NotFound as exc:
            raise RuntimeError(
                f"Le salon {CHANNEL_ID} est introuvable. Vérifie QUIZ_CHANNEL_ID "
                "et copie l'identifiant du salon textuel, pas celui du serveur."
            ) from exc
        except discord.HTTPException as exc:
            raise RuntimeError(
                f"Discord n'a pas pu récupérer le salon {CHANNEL_ID} "
                f"(HTTP {exc.status}). Réessaie plus tard."
            ) from exc

    if not hasattr(channel, "send"):
        raise RuntimeError(
            f"L'identifiant {CHANNEL_ID} ne correspond pas à un salon "
            "dans lequel le bot peut envoyer un message."
        )

    day_number = datetime.now(TIMEZONE).date().toordinal()
    question = QUESTIONS[(day_number - 1 + offset) % len(QUESTIONS)]

    embed = discord.Embed(
        title="CyberQuiz quotidien",
        description=question["question"],
        color=discord.Color.green()
    )
    embed.add_field(name="Catégorie", value=question["category"], inline=True)
    embed.add_field(
        name="Difficulté",
        value=question["difficulty"].capitalize(),
        inline=True
    )

    for index, option in enumerate(question["options"]):
        embed.add_field(
            name=["A", "B", "C", "D"][index],
            value=option,
            inline=False
        )

    embed.set_footer(text="Une réponse par membre • Bonne chance !")

    message = await channel.send(embed=embed, view=AnswerView())

    with db_connect() as db:
        db.execute("""
            INSERT OR IGNORE INTO quizzes
                (quiz_date, question_id, message_id)
            VALUES (?, ?, ?)
        """, (quiz_key, question["id"], message.id))

    log.info("Quiz publié pour %s (clé %s)", today, quiz_key)
    return True


@tasks.loop(minutes=1)
async def daily_scheduler():
    now = datetime.now(TIMEZONE)
    if now.hour >= 10:
        try:
            await publish_quiz(force=False)
        except Exception:
            log.exception("Impossible de publier le quiz")


@daily_scheduler.before_loop
async def before_scheduler():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    log.info("Connecté en tant que %s", bot.user)

    if not daily_scheduler.is_running():
        daily_scheduler.start()

    try:
        await bot.tree.sync()
        log.info("Commandes slash synchronisées.")
    except discord.DiscordException:
        log.exception("Échec de synchronisation des commandes")


# ============================================================
# COMMANDES SLASH
# ============================================================

@bot.tree.command(name="quiz", description="Publier le quiz du jour")
@app_commands.default_permissions(manage_guild=True)
async def quiz_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        published = await publish_quiz(force=False)
        if published:
            await interaction.followup.send(
                "✅ Le quiz du jour a été publié.", ephemeral=True
            )
        else:
            await interaction.followup.send(
                "ℹ️ Un quiz existe déjà pour aujourd'hui. "
                "Utilise `/quiz_force` pour en publier un autre.",
                ephemeral=True
            )
    except Exception as exc:
        log.exception("Erreur de publication manuelle")
        await interaction.followup.send(
            f"❌ Impossible de publier le quiz : {exc}", ephemeral=True
        )


@bot.tree.command(
    name="quiz_force",
    description="Publier un quiz immédiatement, même si un quiz a déjà été publié aujourd'hui"
)
@app_commands.default_permissions(manage_guild=True)
async def quiz_force_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        published = await publish_quiz(force=True)
        if published:
            await interaction.followup.send(
                "✅ Un nouveau quiz a été publié (mode forcé).",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "⚠️ La publication a échoué (voir les logs).",
                ephemeral=True
            )
    except Exception as exc:
        log.exception("Erreur de publication forcée")
        await interaction.followup.send(
            f"❌ Impossible de publier le quiz : {exc}", ephemeral=True
        )


@bot.tree.command(name="profil", description="Voir tes statistiques CyberQuiz")
async def profil(interaction: discord.Interaction):
    with db_connect() as db:
        user = db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (interaction.user.id,)
        ).fetchone()

    if user is None:
        await interaction.response.send_message(
            "Aucune statistique pour le moment. Participe au prochain quiz !",
            ephemeral=True
        )
        return

    accuracy = (
        user["correct"] / user["total"] * 100
        if user["total"] else 0
    )

    embed = discord.Embed(
        title=f"Profil de {interaction.user.display_name}",
        color=discord.Color.green()
    )
    embed.add_field(name="XP", value=str(user["xp"]))
    embed.add_field(name="Niveau", value=str(level_for_xp(user["xp"])))
    embed.add_field(
        name="Bonnes réponses",
        value=f"{user['correct']}/{user['total']}"
    )
    embed.add_field(name="Réussite", value=f"{accuracy:.1f}%")
    embed.add_field(name="Série", value=f"{user['streak']} jour(s)")

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="classement", description="Afficher le top 10 des membres")
async def classement(interaction: discord.Interaction):
    with db_connect() as db:
        rows = db.execute("""
            SELECT user_id, xp
            FROM users
            ORDER BY xp DESC, correct DESC
            LIMIT 10
        """).fetchall()

    if not rows:
        await interaction.response.send_message(
            "Le classement est vide pour le moment."
        )
        return

    lines = []
    for rank, row in enumerate(rows, start=1):
        member = (
            interaction.guild.get_member(row["user_id"])
            if interaction.guild else None
        )
        name = member.display_name if member else f"Membre {row['user_id']}"
        lines.append(
            f"**{rank}.** {name} — {row['xp']} XP "
            f"(niveau {level_for_xp(row['xp'])})"
        )

    embed = discord.Embed(
        title="Classement CyberQuiz",
        description="\n".join(lines),
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed)


# ============================================================
# DÉMARRAGE
# ============================================================

if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit(
            "Token manquant : configure la variable d'environnement "
            "DISCORD_TOKEN dans le panneau d'hébergement. Ne colle pas le "
            "token directement dans le code."
        )

    if CHANNEL_ID == 0:
        raise SystemExit(
            "Configure CHANNEL_ID avec l'identifiant du salon Discord."
        )

    init_db()
    bot.add_view(AnswerView())
    bot.run(TOKEN)
