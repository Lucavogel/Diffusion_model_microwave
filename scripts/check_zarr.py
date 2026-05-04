import zarr
import sys
import os

if len(sys.argv) < 2:
    print("Utilisation : python check_zarr.py chemin_vers_le_dossier.zarr")
    sys.exit(1)

zarr_path = sys.argv[1]

if not os.path.exists(zarr_path):
    print(f"Erreur : Le dossier {zarr_path} n'existe pas.")
    sys.exit(1)

# Ouvrir le fichier zarr en lecture seule
try:
    root = zarr.open(zarr_path, mode='r')
    
    if 'meta' in root and 'episode_ends' in root['meta']:
        episode_ends = root['meta']['episode_ends'][:]
        num_episodes = len(episode_ends)
        total_steps = episode_ends[-1] if num_episodes > 0 else 0
        
        print("\n" + "="*50)
        print(f"RAPPORT DU DATASET : {os.path.basename(zarr_path)}")
        print("="*50)
        print(f"Nombre de trajectoires (épisodes) : {num_episodes}")
        print(f"Nombre total de pas (steps)       : {total_steps}")
        print("-" * 50)
        
        print("Données enregistrées (shape) :")
        for key in root['data'].keys():
            shape = root['data'][key].shape
            dtype = root['data'][key].dtype
            print(f"   - {key:<25}: {shape} ({dtype})")
            
        print("="*50 + "\n")
    else:
        print("Ce dossier zarr ne correspond pas au format ReplayBuffer de Diffusion Policy.")
except Exception as e:
    print(f"Erreur lors de la lecture du fichier : {e}")