#!/usr/bin/env python3
# filepath: sync_components.py
import os
import shutil
import glob
import logging
import json
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Konfiguration
SOURCE_DIR = '.'
TARGET_DIR = './custom_components/hoymiles_dtu_pro'
HOYMILES_SOURCE = './hoymiles'
HOYMILES_TARGET = f'{TARGET_DIR}/hoymiles'

# Dateien und Ordner, die nicht kopiert werden sollen
EXCLUDE = [
    '.git', 
    'custom_components', 
    '__pycache__', 
    '.github', 
    'venv', 
    'env',
    'sync_components.py',
    'setup_hooks.sh',
    'LICENSE',
    '.gitignore',
    'images',
    'hacs.json',  # hacs.json bleibt nur im Root
    'info.md',    # info.md bleibt nur im Root
    'README.md'   # README.md bleibt nur im Root
]

def should_copy(path):
    """Prüft, ob die Datei kopiert werden soll"""
    rel_path = os.path.relpath(path, SOURCE_DIR)
    for exclude_item in EXCLUDE:
        if exclude_item in rel_path:
            return False
    return True

def ensure_directory(directory):
    """Stellt sicher, dass das Verzeichnis existiert"""
    os.makedirs(directory, exist_ok=True)

def copy_file(source, target):
    """Kopiert eine Datei und korrigiert die ersten Zeilen, wenn sie Kommentare enthalten"""
    logger.info(f"Kopiere {source} nach {target}")
    
    # Lese die Quelldatei
    with open(source, 'r', encoding='utf-8', errors='ignore') as src_file:
        content = src_file.read()
    
    # Entferne Kommentarzeilen am Anfang der Datei, die den Dateipfad enthalten
    content = re.sub(r'^// filepath:.*\n', '', content)
    
    # Schreibe den bereinigten Inhalt in die Zieldatei
    with open(target, 'w', encoding='utf-8') as dst_file:
        dst_file.write(content)

def sync_files():
    """Kopiere Dateien vom Hauptverzeichnis in den custom_components-Ordner"""
    logger.info("Starte Synchronisation...")
    
    # Stelle sicher, dass die Zielordner existieren
    ensure_directory(TARGET_DIR)
    ensure_directory(HOYMILES_TARGET)
    
    # Python-Dateien im Root kopieren
    py_files = glob.glob(os.path.join(SOURCE_DIR, "*.py"))
    for file in py_files:
        if should_copy(file):
            dest = os.path.join(TARGET_DIR, os.path.basename(file))
            copy_file(file, dest)
    
    # JSON-Dateien kopieren (nur manifest.json)
    json_files = glob.glob(os.path.join(SOURCE_DIR, "*.json"))
    for file in json_files:
        if should_copy(file) and os.path.basename(file) == "manifest.json":
            dest = os.path.join(TARGET_DIR, os.path.basename(file))
            copy_file(file, dest)
    
    # Hoymiles-Modul kopieren
    if os.path.exists(HOYMILES_SOURCE):
        # Stelle sicher, dass das Zielverzeichnis existiert
        ensure_directory(HOYMILES_TARGET)
        
        # Python-Dateien aus dem hoymiles-Verzeichnis kopieren
        py_files = glob.glob(os.path.join(HOYMILES_SOURCE, "*.py"))
        for file in py_files:
            if should_copy(file):
                dest = os.path.join(HOYMILES_TARGET, os.path.basename(file))
                copy_file(file, dest)
    
    update_version()
    logger.info("Synchronisation abgeschlossen!")
    return True

def update_version():
    """Aktualisiert die Versionsnummer in den manifest.json Dateien"""
    source_manifest = os.path.join(SOURCE_DIR, "manifest.json")
    target_manifest = os.path.join(TARGET_DIR, "manifest.json")
    
    if os.path.exists(source_manifest) and os.path.exists(target_manifest):
        # Lese die Quelldatei
        with open(source_manifest, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        
        # Lese die Zieldatei
        with open(target_manifest, 'r', encoding='utf-8') as f:
            target_data = json.load(f)
        
        # Aktualisiere die Version
        if source_data.get('version') != target_data.get('version'):
            target_data['version'] = source_data['version']
            
            # Schreibe die aktualisierte Datei
            with open(target_manifest, 'w', encoding='utf-8') as f:
                json.dump(target_data, f, indent=2)
                
            logger.info(f"Version in {target_manifest} auf {source_data['version']} aktualisiert")
    else:
        logger.warning("Manifest-Dateien nicht gefunden, Version nicht aktualisiert")

def git_add_custom_components():
    """Fügt den custom_components Ordner zum Git-Staging hinzu"""
    try:
        import subprocess
        subprocess.run(["git", "add", "custom_components"], check=True)
        logger.info("Änderungen im custom_components Ordner zum Staging hinzugefügt")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Fehler beim Hinzufügen zum Staging: {e}")
        return False

if __name__ == "__main__":
    sync_files()