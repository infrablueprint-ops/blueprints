"""
SREGym Autonomous Triage Demonstrator (L/C/S Rubric)
Evaluates autonomous incident diagnosis on Localization, Characterization, and Scope.
"""

def evaluate_triage(incident_report, ground_truth):
    score_l = 1.0 if incident_report.get("service") == ground_truth.get("service") else 0.0
    score_c = 1.0 if incident_report.get("root_cause") == ground_truth.get("root_cause") else 0.5
    score_s = 1.0 if incident_report.get("blast_radius") == ground_truth.get("blast_radius") else 0.3
    
    composite = (score_l * 0.35) + (score_c * 0.40) + (score_s * 0.25)
    return {
        "localization": score_l,
        "characterization": score_c,
        "scope": score_s,
        "composite_lcs_score": round(composite, 2),
        "passing": composite >= 0.78
    }

if __name__ == "__main__":
    test_incident = {
        "service": "elasticsearch-cluster",
        "root_cause": "Lucene segment merging disk write stall",
        "blast_radius": "Search indexing latency spike on /api/v2/search"
    }
    truth = {
        "service": "elasticsearch-cluster",
        "root_cause": "Lucene segment merging disk write stall",
        "blast_radius": "Search indexing latency spike on /api/v2/search"
    }
    result = evaluate_triage(test_incident, truth)
    print("SREGym Triage Evaluation Results:")
    for k, v in result.items():
        print(f"  {k}: {v}")
