
# Gestion du système et des fichiers
import os
import sys
import subprocess

# Manipulation des données XML (Sorties de SUMO)
import xml.etree.ElementTree as ET

# Analyse de données
import pandas as pd
import numpy as np

# Visualisation et Graphiques
import matplotlib.pyplot as plt
import seaborn as sns

def launch_simulation(sumo_config, tripinfo_out="tripinfo.xml", summary_out="summary.xml", lane_out="lane_output.xml"):
    """
    Lance la simulation SUMO en vérifiant tous les fichiers de sortie.
    """
    # 1. On vérifie si TOUS les fichiers existent déjà
    if os.path.exists(tripinfo_out) and os.path.exists(lane_out):
        print(f"Les outputs existent déjà. Simulation sautée.")
        return

    if not os.path.exists(sumo_config):
        raise FileNotFoundError(f"Le fichier '{sumo_config}' est introuvable.")

    print(f"Lancement de la simulation...")

    command = [
        "sumo", 
        "-c", sumo_config,
        "--tripinfo-output", tripinfo_out,
        "--summary-output", summary_out,
        # On peut forcer le nom du fichier lane-output ici aussi si on veut être sûr
        "--device.emissions.probability", "1",
        "--quit-on-end", "true",
        "--no-step-log", "true"
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ Simulation terminée. Fichiers créés : {tripinfo_out}, {summary_out}, {lane_out}")
        
    except subprocess.CalledProcessError as e:
        print("--- ERREUR SUMO ---")
        print(e.stderr)
        raise e




def analyze_tripinfo(filename='tripinfo.xml'):

    if not os.path.exists(filename):
        print(f"Erreur : Le fichier '{filename}' n'existe pas. As-tu bien lancé la simulation avant ?")
    else:
        try:
            tree = ET.parse(filename)
            root = tree.getroot()

            trip_data = []
            # On cherche les balises 'tripinfo'
            for trip in root.findall('tripinfo'):
                trip_data.append({
                    'id': trip.get('id'),
                    'duration': float(trip.get('duration')),
                    'waitingTime': float(trip.get('waitingTime')),
                    'timeLoss': float(trip.get('timeLoss'))
                })

            if not trip_data:
                print("⚠ Le fichier est là, mais il est vide. Aucun véhicule n'est arrivé à destination.")
            else:
                df = pd.DataFrame(trip_data)

                # Calculs
                print(f"Analyse de {len(df)} véhicules terminée.")
                print(f"Average Duration: {df['duration'].mean():.2f}s")
                print(f"Average Waiting Time: {df['waitingTime'].mean():.2f}s")
                print(f"Average Time Loss: {df['timeLoss'].mean():.2f}s")

                # Visualisation
                plt.figure(figsize=(10, 6))
                plt.hist(df['waitingTime'], bins=30, color='skyblue', edgecolor='black')
                plt.xlabel('Waiting Time (seconds)')
                plt.ylabel('Number of Vehicles')
                plt.title('Distribution of Vehicle Waiting Times - Groupe 3')
                plt.show()

        except ET.ParseError:
            print("Erreur : Le fichier XML est mal formé (simulation non terminée ou crashée).")

def analyze_emissions(filename='tripinfo.xml'):
    if not os.path.exists(filename):
        print(f"Erreur : Le fichier '{filename}' est introuvable.")
        return

    tree = ET.parse(filename)
    root = tree.getroot()
    data = []

    for trip in root.findall('tripinfo'):
        # On récupère les données de la balise enfant <emissions>
        emissions = trip.find('emissions')
        if emissions is not None:
            data.append({
                'id': trip.get('id'),
                'co2': float(emissions.get('CO2_abs')) / 1000, # Conversion en grammes
                'fuel': float(emissions.get('fuel_abs')) / 1000 # Conversion en mL
            })

    if data:
        df = pd.DataFrame(data)
        print(f"--- Rapport Écologique ---")
        print(f"Émission totale de CO2: {df['co2'].sum():.2f} g")
        print(f"Consommation moyenne de carburant: {df['fuel'].mean():.2f} mL/véhicule")

        plt.figure(figsize=(8, 5))
        sns.boxplot(y=df['co2'], color='green')
        plt.title('Distribution des émissions de CO2 par véhicule')
        plt.ylabel('CO2 (grammes)')
        plt.show()


def analyze_queues(filename='lane_output.xml', target_ids=None):
    if not os.path.exists(filename):
        print(f"❌ Erreur : Le fichier '{filename}' n'existe pas.")
        return

    tree = ET.parse(filename)
    root = tree.getroot()
    queue_data = []

    for interval in root.findall('interval'):
        time_start = float(interval.get('begin'))
        
        # On cherche à la fois dans 'edge' et 'lane' pour être sûr
        elements = interval.findall('edge') + interval.findall('lane')
        
        for el in elements:
            obj_id = el.get('id')
            
            # Si on a spécifié des cibles, on filtre
            if target_ids is None or obj_id in target_ids:
                queue_data.append({
                    'time': time_start,
                    'id': obj_id, # On utilise un nom générique 'id'
                    'queueLength': float(el.get('maxJamLengthInMeters', 0))
                })

    if not queue_data:
        print("⚠ Aucune donnée trouvée. Vérifie que tes IDs correspondent à ceux de la simulation.")
        return

    df = pd.DataFrame(queue_data)

    # --- Visualisation ---
    plt.figure(figsize=(10, 6))
    
    # On boucle sur les IDs uniques trouvés dans la colonne 'id'
    unique_ids = df['id'].unique()
    for current_id in unique_ids:
        subset = df[df['id'] == current_id]
        plt.plot(subset['time'], subset['queueLength'], label=f"Zone: {current_id}")

    plt.title('Évolution des bouchons - Groupe 3')
    plt.xlabel('Temps (s)')
    plt.ylabel('Longueur du bouchon (m)')
    plt.legend()
    plt.grid(True, linestyle='--')
    plt.show()
    
    return df
    


def analyze_network_speed(filename='summary.xml'):
    if not os.path.exists(filename):
        print("Erreur : Fichier summary.xml introuvable.")
        return

    tree = ET.parse(filename)
    root = tree.getroot()
    speed_data = []

    for step in root.findall('step'):
        speed_data.append({
            'time': float(step.get('time')),
            'meanSpeed': float(step.get('meanSpeed')),
            'halting': int(step.get('halting')) # Nb de véhicules à l'arrêt
        })

    df = pd.DataFrame(speed_data)

    fig, ax1 = plt.subplots(figsize=(12, 6))

    ax1.set_xlabel('Temps (s)')
    ax1.set_ylabel('Vitesse Moyenne (m/s)', color='blue')
    ax1.plot(df['time'], df['meanSpeed'], color='blue', label='Vitesse moyenne')

    ax2 = ax1.twinx()
    ax2.set_ylabel('Véhicules à l\'arrêt', color='red')
    ax2.fill_between(df['time'], df['halting'], color='red', alpha=0.2, label='Congestion')

    plt.title('Performance du réseau : Vitesse vs Congestion')
    plt.show()


