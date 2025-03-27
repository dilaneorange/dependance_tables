import pandas as pd
from collections import defaultdict
from openai import OpenAI
import re

# Configuration Ollama
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama'
)

# Chargement des données
file_path = 'C:/Users/FDYZ3036/Documents/ORANGE/DEPENDANCES_FINAL/filtrage_3_tables1.csv'
data = pd.read_csv(file_path, encoding='ISO-8859-1', sep=';', dtype=str)
data = data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

# Construction du graphe
graph = defaultdict(set)
reverse_graph = defaultdict(set)
table_mapping = {}
all_tables = set()

for _, row in data.iterrows():
    all_values = [v for v in row if pd.notna(v) and str(v).strip()]
    for value in all_values:
        value_lower = value.lower()
        table_mapping[value_lower] = value
        all_tables.add(value_lower)
    for i in range(len(all_values)):
        for j in range(i+1, len(all_values)):
            src, dep = all_values[i], all_values[j]
            src_lower, dep_lower = src.lower(), dep.lower()
            graph[src_lower].add(dep_lower)
            reverse_graph[dep_lower].add(src_lower)

def get_original_case(table_lower):
    return table_mapping.get(table_lower, table_lower.upper())

def display_vertical(title, items):
    print(f"\n{title}:")
    if not items:
        print("  Aucun élément trouvé")
        return
    for item in items:
        print(f"  - {item}")
    print(f"\n  Total: {len(items)} éléments")

def ask_ollama(prompt):
    """Fonction pour interroger Ollama """
    try:
        response = client.chat.completions.create(
            model="mistral",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Réduit la créativité pour des réponses plus factuelles
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except:
        return None  # Retourne None si Ollama échoue

# Interface
print("\n" + "="*60)
print("SYSTÈME D'ANALYSE DE DÉPENDANCES ")
print("="*60)

while True:
    question = input("\nVotre question (ou 'quitter'): ").strip()
    if question.lower() in ('quitter', 'exit', 'bye'):
        print("Au revoir !")
        break
    
    # Détection des questions générales (uniquement)
    general_questions = {
        "bonjour": "Bonjour ! Comment puis-je vous aider avec vos dépendances de données aujourd'hui ?",
        "comment ça va": "Je fonctionne normalement, prêt à analyser vos données !",
    }
    
    if question.lower() in general_questions:
        print("\n" + general_questions[question.lower()])
        continue
    
    # Détection des questions techniques
    table_match = re.search(r'([a-z0-9_]+\.[a-z0-9_]+)', question, re.I)
    if not table_match:
        print("\nℹ️ Voici une réponse générale via Ollama :")
        ollama_response = ask_ollama(question)
        print(ollama_response if ollama_response else "Désolé, je n'ai pas pu obtenir de réponse.")
        continue
    
    # Traitement technique
    table = table_match.group(1)
    table_lower = table.lower()
    table_original = get_original_case(table_lower)
    
    if table_lower not in all_tables:
        print(f"\n❌ La table '{table_original}' n'existe pas.")
        similar = [t for t in table_mapping.values() if table_lower.split('.')[0] in t.lower()]
        if similar:
            display_vertical("Tables similaires existantes", similar[:5])
        continue
    
    # Analyse technique avec réponse Ollama automatique
    if re.search(r'(dépendance|dépend|dépendre).*(directe|immédiat)', question, re.I):
        deps = sorted([get_original_case(d) for d in graph.get(table_lower, set())])
        display_vertical(f"Dépendances DIRECTES de '{table_original}'", deps)
        if deps:
            prompt = f"Explique en une phrase les dépendances directes de '{table_original}' : {', '.join(deps)}"
            ollama_response = ask_ollama(prompt)
            print("\nExplication : " + ollama_response if ollama_response else "")
    
    elif re.search(r'(dépendance|dépend|dépendre).*(indirecte|tout)', question, re.I):
        deps = set()
        stack = list(graph.get(table_lower, set()))
        while stack:
            current = stack.pop()
            if current not in deps:
                deps.add(current)
                stack.extend(graph.get(current, set()))
        display_vertical(f"Dépendances INDIRECTES de '{table_original}'", sorted([get_original_case(d) for d in deps]))
        if deps:
            prompt = f"Résume en une phrase les dépendances indirectes de '{table_original}'"
            ollama_response = ask_ollama(prompt)
            print("\nExplication : " + ollama_response if ollama_response else "")
    
    elif re.search(r'(qui utilise|dépendant|utilisateur)', question, re.I):
        users = sorted([get_original_case(u) for u in reverse_graph.get(table_lower, set())])
        display_vertical(f"Utilisateurs de '{table_original}'", users)
        if users:
            prompt = f"Explique en une phrase qui utilise '{table_original}' : {', '.join(users)}"
            ollama_response = ask_ollama(prompt)
            print("\nExplication : " + ollama_response if ollama_response else "")
    
    else:
        # Mode hybride automatique
        print(f"\nAnalyse complète pour '{table_original}':")
        deps = sorted([get_original_case(d) for d in graph.get(table_lower, set())])
        users = sorted([get_original_case(u) for u in reverse_graph.get(table_lower, set())])
        
        display_vertical("Dépendances directes", deps)
        display_vertical("Utilisateurs directs", users)
        
        # Génération automatique de l'explication Ollama
        if deps or users:
            prompt = f"Résume en 2 phrases maximum les relations de '{table_original}'"
            if deps:
                prompt += f" avec ses dépendances ({', '.join(deps)})"
            if users:
                prompt += f" et ses utilisateurs ({', '.join(users)})"
            prompt += ". En français."
            
            ollama_response = ask_ollama(prompt)
            print("\nExplication :\n" + ollama_response if ollama_response else "")