# packet_loader.py
# Loads converted JSON packets for NAQT, OSSAA, and Froshmore formats

import os
import json

def load_packets(format_type):
    """
    Load packets from the packets/[format_type] folder.
    format_type: "NAQT", "OSSAA", or "Froshmore"
    Returns: list of packet dicts
    """
    folder = os.path.join("packets", format_type)
    packets = []

    if not os.path.exists(folder):
        print(f"Packet folder not found: {folder}")
        return packets

    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            path = os.path.join(folder, filename)
            try:
                with open(path, encoding="utf-8") as f:
                    packet = json.load(f)
                    packets.append(packet)
            except Exception as e:
                print(f"Error loading {filename}: {e}")

    return packets
    elif ext == ".csv":
        return load_csv_packet(path)
    elif ext == ".docx":
        return load_docx_packet(path)
    elif ext == ".pdf":
        return load_pdf_packet(path)
    return []
