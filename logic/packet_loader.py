import os, json

def load_packet(folder: str, format_name: str):
    base = os.path.join(folder, format_name.lower())
    packets = []
    if not os.path.isdir(base):
        return packets
    for fname in os.listdir(base):
        if fname.endswith(".json"):
            with open(os.path.join(base, fname), "r", encoding="utf-8") as f:
                packets.append(json.load(f))
    return packets

def next_question(packets, idx):
    if not packets:
        return None, idx
    packet = packets[0]
    qlist = packet.get("questions", [])
    if idx < len(qlist):
        return qlist[idx], idx + 1
    return None, idx