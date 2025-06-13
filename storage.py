import json
import os

HR_RESULTS_FILE = 'hr_results.json'
TECH_RESULTS_FILE = 'tech_results.json'


def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


# HR FUNCTIONS

def save_hr_result(candidate_id, hr_entry):
    data = load_json(HR_RESULTS_FILE)
    if candidate_id not in data:
        data[candidate_id] = []
    data[candidate_id].append(hr_entry)
    save_json(HR_RESULTS_FILE, data)

def load_hr_results():
    """Return full dict {candidate_id: [list of HR entries]}"""
    return load_json(HR_RESULTS_FILE)


# TECH FUNCTIONS

def save_tech_result(candidate_id, tech_entry):
    data = load_json(TECH_RESULTS_FILE)
    if candidate_id not in data:
        data[candidate_id] = []
    data[candidate_id].append(tech_entry)
    save_json(TECH_RESULTS_FILE, data)

def load_tech_results():
    """Return full dict {candidate_id: [list of Tech entries]}"""
    return load_json(TECH_RESULTS_FILE)
