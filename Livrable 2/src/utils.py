
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

def launch_simulation(sumo_config, tripinfo_out="tripinfo.xml", summary_out="summary.xml", queue_out="queue_output.xml", lane_out="lane_output.xml"):
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
    "--queue-output", queue_out,
    # Activation des émissions pour qu'elles soient incluses dans tripinfo
    "--device.emissions.probability", "1", 
    "--quit-on-end", "true",
    "--no-step-log", "true"
]  
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ Simulation terminée. Fichiers créés : {tripinfo_out}, {summary_out}, {queue_out}, {lane_out}")
        
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

def analyze_pollution(filename='tripinfo_base.xml'):
    if not os.path.exists(filename):
        print("❌ Fichier tripinfo introuvable.")
        return

    tree = ET.parse(filename)
    root = tree.getroot()
    
    total_co2 = 0
    vehicle_count = 0

    for trip in root.findall('tripinfo'):
        emissions = trip.find('emissions')
        if emissions is not None:
            # CO2_abs est en mg, on convertit en grammes
            total_co2 += float(emissions.get('CO2_abs', 0)) / 1000
            vehicle_count += 1

    if vehicle_count > 0:
        print(f"--- Rapport Écologique ({filename}) ---")
        print(f"Nombre de véhicules : {vehicle_count}")
        print(f"CO2 total émis : {total_co2:.2f} g")
        print(f"Moyenne par véhicule : {total_co2/vehicle_count:.2f} g")
    else:
        print("⚠ Aucune donnée d'émission trouvée. Vérifiez '--device.emissions.probability'.")



def analyze_queue(filename, target_lanes=None, label="Simulation"):
    if not os.path.exists(filename):
        print(f"❌ Erreur : Le fichier '{filename}' n'existe pas.")
        return pd.DataFrame()

    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        data_list = []

        # On cherche chaque bloc <data> qui contient l'attribut 'timestep'
        for data_tag in root.findall('data'):
            time = float(data_tag.get('timestep'))
            
            # Dans chaque <data>, on cherche les balises <lane> (sous <lanes>)
            for lane in data_tag.iter('lane'):
                lane_id = lane.get('id')
                
                # Filtrage optionnel par ID de voie
                if target_lanes is None or lane_id in target_lanes:
                    data_list.append({
                        'time': time,
                        'lane': lane_id,
                        'queue_length': float(lane.get('queueing_length', 0)),
                        'scenario': label
                    })

        df = pd.DataFrame(data_list)
        
        if df.empty:
            print(f"⚠ Aucune donnée trouvée dans {filename}.")
            return pd.DataFrame(columns=['time', 'lane', 'queue_length', 'scenario'])
            
        return df

    except Exception as e:
        print(f"❌ Erreur lors du parsing de {filename}: {e}")
        return pd.DataFrame(columns=['time', 'lane', 'queue_length', 'scenario'])


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


