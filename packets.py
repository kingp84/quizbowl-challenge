# packets.py
# Default in-memory packets to ensure the game runs even if no files are found.

DEFAULT_QUESTIONS = {
    "NAQT": [
        {
            "id": "naqt-001",
            "answer": "Waterloo",
            "clues": [
                {"difficulty": "Hard", "text": "This 1815 battle saw Napoleon defeated after Blücher’s Prussians arrived to support Wellington."},
                {"difficulty": "Medium", "text": "Fought in Belgium, it ended the Hundred Days and led to exile on Saint Helena."},
                {"difficulty": "Easy", "text": "Name the battle where Napoleon was defeated by Wellington: Battle of ________."}
            ]
        },
        {
            "id": "naqt-002",
            "answer": "Photosynthesis",
            "clues": [
                {"difficulty": "Hard", "text": "This process involves the Calvin cycle and the enzyme RuBisCO."},
                {"difficulty": "Medium", "text": "It converts carbon dioxide and water into glucose and oxygen in chloroplasts."},
                {"difficulty": "Easy", "text": "Plants make food using sunlight in a process called ________."}
            ]
        }
    ],
    "Froshmore": [
        {
            "id": "fro-001",
            "answer": "Mitochondria",
            "clues": [
                {"difficulty": "Hard", "text": "This organelle contains cristae and performs oxidative phosphorylation."},
                {"difficulty": "Medium", "text": "It has its own DNA and is known as the powerhouse of the cell."},
                {"difficulty": "Easy", "text": "Name the organelle famous as the cell’s powerhouse: ________."}
            ]
        }
    ],
    "OSSAA": [
        {
            "id": "ossaa-001",
            "answer": "Red River",
            "clues": [
                {"difficulty": "Hard", "text": "This river forms a significant stretch of the Texas–Oklahoma border and flows into the Mississippi."},
                {"difficulty": "Medium", "text": "Its name comes from the reddish silt; notable in the 1800s for navigation and commerce."},
                {"difficulty": "Easy", "text": "Name the river that borders Oklahoma and Texas: the ________ River."}
            ]
        }
    ]
}