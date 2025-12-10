"""
SwarmOS Output Schemas
======================

JSON schemas for structured output enforcement.
Use with OpenAI Structured Outputs, Gemini responseSchema, or Claude prefilling.
"""

from typing import Any, Dict, List, Tuple

# =============================================================================
# ORCHESTRATION SCHEMAS
# =============================================================================

TASK_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "core_challenge": {
            "type": "object",
            "properties": {
                "surface_request": {"type": "string"},
                "actual_hard_problem": {"type": "string"},
                "non_obvious_insight": {"type": "string"}
            },
            "required": ["surface_request", "actual_hard_problem", "non_obvious_insight"]
        },
        "experts_required": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "domain_depth": {"type": "string"},
                    "contrarian_mandate": {"type": "string"},
                    "capability_class": {
                        "type": "string",
                        "enum": ["RESEARCH", "ANALYSIS", "SYNTHESIS", "CRITIQUE"]
                    }
                },
                "required": ["role", "domain_depth", "contrarian_mandate", "capability_class"]
            }
        },
        "timing_analysis": {
            "type": "object",
            "properties": {
                "why_now": {"type": "string"},
                "bottlenecks_unlocking": {"type": "array", "items": {"type": "string"}},
                "timing_window": {"type": "string"}
            },
            "required": ["why_now", "bottlenecks_unlocking", "timing_window"]
        },
        "depth_decision": {
            "type": "object",
            "properties": {
                "choice": {"type": "string", "enum": ["DEEP", "BROAD"]},
                "target_count": {"type": "integer"},
                "justification": {"type": "string"}
            },
            "required": ["choice", "target_count", "justification"]
        },
        "anti_consensus": {
            "type": "object",
            "properties": {
                "obvious_wrong_answer": {"type": "string"},
                "unfashionable_right_answer": {"type": "string"}
            },
            "required": ["obvious_wrong_answer", "unfashionable_right_answer"]
        },
        "debate_required": {"type": "boolean"},
        "complexity_score": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "required": [
        "core_challenge", "experts_required", "timing_analysis", 
        "depth_decision", "anti_consensus", "debate_required", "complexity_score"
    ],
    "additionalProperties": False
}

TASK_DECOMPOSITION_SCHEMA = {
    "type": "object",
    "properties": {
        "subtasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "assigned_expert": {"type": "string"},
                    "description": {"type": "string"},
                    "specificity_requirements": {"type": "array", "items": {"type": "string"}},
                    "forbidden_phrases": {"type": "array", "items": {"type": "string"}},
                    "output_format": {"type": "string"},
                    "success_criteria": {"type": "string"}
                },
                "required": ["id", "assigned_expert", "description", "specificity_requirements", 
                            "forbidden_phrases", "output_format", "success_criteria"]
            }
        },
        "execution_order": {"type": "string", "enum": ["PARALLEL", "SEQUENTIAL", "HYBRID"]},
        "synthesis_strategy": {"type": "string"}
    },
    "required": ["subtasks", "execution_order", "synthesis_strategy"],
    "additionalProperties": False
}

QUERY_EXPANSION_SCHEMA = {
    "type": "object",
    "properties": {
        "original_query": {"type": "string"},
        "implicit_assumptions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "assumption": {"type": "string"},
                    "if_wrong": {"type": "string"}
                },
                "required": ["assumption", "if_wrong"]
            }
        },
        "timeframe_ambiguity": {
            "type": "object",
            "properties": {
                "implied_timeframe": {"type": "string"},
                "alternative_timeframes": {"type": "array", "items": {"type": "string"}},
                "recommendation": {"type": "string"}
            },
            "required": ["implied_timeframe", "alternative_timeframes", "recommendation"]
        },
        "audience_implications": {
            "type": "object",
            "properties": {
                "likely_audience": {"type": "string"},
                "how_it_shapes_answer": {"type": "string"}
            },
            "required": ["likely_audience", "how_it_shapes_answer"]
        },
        "contrarian_reframe": {
            "type": "object",
            "properties": {
                "consensus_interpretation": {"type": "string"},
                "contrarian_interpretation": {"type": "string"},
                "recommendation": {"type": "string"}
            },
            "required": ["consensus_interpretation", "contrarian_interpretation", "recommendation"]
        },
        "expanded_query": {"type": "string"},
        "sub_questions": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["original_query", "implicit_assumptions", "timeframe_ambiguity",
                "audience_implications", "contrarian_reframe", "expanded_query", "sub_questions"],
    "additionalProperties": False
}

# =============================================================================
# AGENT OUTPUT SCHEMAS
# =============================================================================

RESEARCHER_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "thesis": {"type": "string"},
        "domain_expertise_applied": {"type": "string"},
        "consensus_view": {"type": "string"},
        "why_consensus_is_incomplete": {"type": "string"},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "source": {"type": "string"},
                    "strength": {"type": "string", "enum": ["STRONG", "MODERATE", "WEAK"]},
                    "contrarian_or_consensus": {"type": "string"}
                },
                "required": ["claim", "source", "strength", "contrarian_or_consensus"]
            }
        },
        "specific_entities": {
            "type": "object",
            "properties": {
                "companies": {"type": "array", "items": {"type": "string"}},
                "regulations": {"type": "array", "items": {"type": "string"}},
                "technologies": {"type": "array", "items": {"type": "string"}},
                "people": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["companies", "regulations", "technologies"]
        },
        "timing": {
            "type": "object",
            "properties": {
                "window": {"type": "string"},
                "bottlenecks": {"type": "array", "items": {"type": "string"}},
                "catalysts": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["window", "bottlenecks", "catalysts"]
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "what_would_change_my_mind": {"type": "string"}
    },
    "required": ["thesis", "domain_expertise_applied", "consensus_view",
                "why_consensus_is_incomplete", "evidence", "specific_entities",
                "timing", "confidence", "what_would_change_my_mind"],
    "additionalProperties": False
}

ANALYST_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "expert_pattern_match": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "typical_failure_mode": {"type": "string"},
                "non_obvious_success_factor": {"type": "string"}
            },
            "required": ["pattern", "typical_failure_mode", "non_obvious_success_factor"]
        },
        "bottleneck_analysis": {
            "type": "object",
            "properties": {
                "stated_bottleneck": {"type": "string"},
                "actual_bottleneck": {"type": "string"},
                "unlock_timeline": {"type": "string"},
                "bottleneck_controller": {"type": "string"}
            },
            "required": ["stated_bottleneck", "actual_bottleneck", "unlock_timeline", "bottleneck_controller"]
        },
        "distribution_reality": {
            "type": "object",
            "properties": {
                "buyer": {"type": "string"},
                "sales_cycle": {"type": "string"},
                "adoption_path": {"type": "string"},
                "blocking_objection": {"type": "string"}
            },
            "required": ["buyer", "sales_cycle", "adoption_path", "blocking_objection"]
        },
        "moat_analysis": {
            "type": "object",
            "properties": {
                "moat_type": {"type": "string"},
                "build_time": {"type": "string"},
                "replication_difficulty": {"type": "string"},
                "decay_rate": {"type": "string"}
            },
            "required": ["moat_type", "build_time", "replication_difficulty", "decay_rate"]
        },
        "timing_verdict": {
            "type": "object",
            "properties": {
                "actionable_window": {"type": "string"},
                "why_not_earlier": {"type": "string"},
                "why_not_later": {"type": "string"},
                "key_catalysts": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["actionable_window", "why_not_earlier", "why_not_later", "key_catalysts"]
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "strongest_counterargument": {"type": "string"}
    },
    "required": ["expert_pattern_match", "bottleneck_analysis", "distribution_reality",
                "moat_analysis", "timing_verdict", "confidence", "strongest_counterargument"],
    "additionalProperties": False
}

REVIEWER_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "object",
            "properties": {
                "depth": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer", "minimum": 1, "maximum": 5},
                        "evidence": {"type": "string"}
                    },
                    "required": ["score", "evidence"]
                },
                "accuracy": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer", "minimum": 1, "maximum": 5},
                        "evidence": {"type": "string"}
                    },
                    "required": ["score", "evidence"]
                },
                "timing": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer", "minimum": 1, "maximum": 5},
                        "evidence": {"type": "string"}
                    },
                    "required": ["score", "evidence"]
                },
                "contrarian_value": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer", "minimum": 1, "maximum": 5},
                        "evidence": {"type": "string"}
                    },
                    "required": ["score", "evidence"]
                }
            },
            "required": ["depth", "accuracy", "timing", "contrarian_value"]
        },
        "weighted_total": {"type": "number", "minimum": 0, "maximum": 5},
        "depth_signals_found": {"type": "array", "items": {"type": "string"}},
        "shallow_signals_found": {"type": "array", "items": {"type": "string"}},
        "fatal_flaws": {"type": "array", "items": {"type": "string"}},
        "specific_improvements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "issue": {"type": "string"},
                    "location": {"type": "string"},
                    "fix": {"type": "string"}
                },
                "required": ["issue", "location", "fix"]
            }
        },
        "verdict": {"type": "string", "enum": ["EXCEPTIONAL", "GOOD", "ACCEPTABLE", "NEEDS_REWORK", "REJECT"]},
        "rework_required": {"type": "boolean"},
        "rework_focus": {"type": "string"}
    },
    "required": ["scores", "weighted_total", "depth_signals_found", "shallow_signals_found",
                "fatal_flaws", "specific_improvements", "verdict", "rework_required"],
    "additionalProperties": False
}

SYNTHESIZER_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "executive_summary": {"type": "string"},
        "core_thesis": {"type": "string"},
        "synthesized_analysis": {"type": "string"},
        "key_insights": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "insight": {"type": "string"},
                    "supporting_evidence": {"type": "string"},
                    "timing": {"type": "string"}
                },
                "required": ["insight", "supporting_evidence", "timing"]
            }
        },
        "conflicts_resolved": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "disagreement": {"type": "string"},
                    "resolution": {"type": "string"}
                },
                "required": ["disagreement", "resolution"]
            }
        },
        "synthesis_value_add": {"type": "string"},
        "overall_confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "strongest_counterargument": {"type": "string"}
    },
    "required": ["executive_summary", "core_thesis", "synthesized_analysis",
                "key_insights", "conflicts_resolved", "synthesis_value_add",
                "overall_confidence", "strongest_counterargument"],
    "additionalProperties": False
}

# =============================================================================
# DEBATE SCHEMAS
# =============================================================================

DEBATE_PROPOSAL_SCHEMA = {
    "type": "object",
    "properties": {
        "position": {"type": "string"},
        "unfashionable_angle": {"type": "string"},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "support": {"type": "string"},
                    "strength": {"type": "string", "enum": ["STRONG", "MODERATE", "WEAK"]}
                },
                "required": ["claim", "support", "strength"]
            }
        },
        "specific_entities": {
            "type": "object",
            "properties": {
                "companies": {"type": "array", "items": {"type": "string"}},
                "regulations": {"type": "array", "items": {"type": "string"}},
                "technologies": {"type": "array", "items": {"type": "string"}},
                "numbers": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["companies", "regulations", "technologies", "numbers"]
        },
        "timing": {
            "type": "object",
            "properties": {
                "window": {"type": "string"},
                "bottlenecks": {"type": "array", "items": {"type": "string"}},
                "catalysts": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["window", "bottlenecks", "catalysts"]
        },
        "moat_mechanism": {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "how_it_builds": {"type": "string"},
                "replication_barrier": {"type": "string"}
            },
            "required": ["type", "how_it_builds", "replication_barrier"]
        },
        "strongest_counterargument": {"type": "string"},
        "why_i_might_be_wrong": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "required": ["position", "unfashionable_angle", "evidence", "specific_entities",
                "timing", "moat_mechanism", "strongest_counterargument",
                "why_i_might_be_wrong", "confidence"],
    "additionalProperties": False
}

DEBATE_CRITIQUE_SCHEMA = {
    "type": "object",
    "properties": {
        "steelman": {"type": "string"},
        "what_i_might_be_missing": {"type": "string"},
        "stress_test_results": {
            "type": "object",
            "properties": {
                "timing": {"type": "object", "properties": {"holds": {"type": "boolean"}, "issue": {"type": "string"}}, "required": ["holds"]},
                "specificity": {"type": "object", "properties": {"holds": {"type": "boolean"}, "issue": {"type": "string"}}, "required": ["holds"]},
                "moat": {"type": "object", "properties": {"holds": {"type": "boolean"}, "issue": {"type": "string"}}, "required": ["holds"]},
                "evidence": {"type": "object", "properties": {"holds": {"type": "boolean"}, "issue": {"type": "string"}}, "required": ["holds"]}
            },
            "required": ["timing", "specificity", "moat", "evidence"]
        },
        "critiques": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["FATAL", "MAJOR", "MINOR"]},
                    "target": {"type": "string"},
                    "critique": {"type": "string"},
                    "evidence": {"type": "string"},
                    "if_true_impact": {"type": "string"}
                },
                "required": ["type", "target", "critique", "evidence", "if_true_impact"]
            }
        },
        "alternative_position": {"type": "string"},
        "overall_assessment": {
            "type": "object",
            "properties": {
                "verdict": {"type": "string", "enum": ["STRONG", "HAS_MERIT", "WEAK", "FATALLY_FLAWED"]},
                "confidence_in_critique": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["verdict", "confidence_in_critique"]
        }
    },
    "required": ["steelman", "what_i_might_be_missing", "stress_test_results",
                "critiques", "alternative_position", "overall_assessment"],
    "additionalProperties": False
}

DEBATE_VOTING_SCHEMA = {
    "type": "object",
    "properties": {
        "proposal_scores": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "proposal_id": {"type": "integer"},
                    "specificity": {"type": "object", "properties": {"score": {"type": "integer"}, "evidence": {"type": "string"}}, "required": ["score", "evidence"]},
                    "contrarian_value": {"type": "object", "properties": {"score": {"type": "integer"}, "evidence": {"type": "string"}}, "required": ["score", "evidence"]},
                    "timing_rigor": {"type": "object", "properties": {"score": {"type": "integer"}, "evidence": {"type": "string"}}, "required": ["score", "evidence"]},
                    "evidence_quality": {"type": "object", "properties": {"score": {"type": "integer"}, "evidence": {"type": "string"}}, "required": ["score", "evidence"]},
                    "weighted_total": {"type": "number", "minimum": 0, "maximum": 5}
                },
                "required": ["proposal_id", "specificity", "contrarian_value", "timing_rigor", "evidence_quality", "weighted_total"]
            }
        },
        "selected_proposal": {"type": "integer"},
        "selection_reasoning": {"type": "string"},
        "strongest_counterargument_to_selection": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "required": ["proposal_scores", "selected_proposal", "selection_reasoning",
                "strongest_counterargument_to_selection", "confidence"],
    "additionalProperties": False
}

DEBATE_JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "position_summaries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "proposal_id": {"type": "integer"},
                    "core_position": {"type": "string"},
                    "strongest_point": {"type": "string"},
                    "weakest_point": {"type": "string"}
                },
                "required": ["proposal_id", "core_position", "strongest_point", "weakest_point"]
            }
        },
        "crux_of_debate": {"type": "string"},
        "evidence_evaluation": {
            "type": "object",
            "properties": {
                "strongest_evidence_overall": {"type": "string"},
                "by_whom": {"type": "integer"}
            },
            "required": ["strongest_evidence_overall", "by_whom"]
        },
        "critique_assessment": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "critique": {"type": "string"},
                    "landed": {"type": "boolean"},
                    "impact": {"type": "string"}
                },
                "required": ["critique", "landed", "impact"]
            }
        },
        "winner": {
            "type": "object",
            "properties": {
                "proposal_id": {"type": "integer"},
                "reasoning": {"type": "string"},
                "margin": {"type": "string", "enum": ["DECISIVE", "CLEAR", "NARROW"]}
            },
            "required": ["proposal_id", "reasoning", "margin"]
        },
        "synthesized_best_answer": {
            "type": "object",
            "properties": {
                "position": {"type": "string"},
                "incorporates_from_each": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["position", "incorporates_from_each", "confidence"]
        }
    },
    "required": ["position_summaries", "crux_of_debate", "evidence_evaluation",
                "critique_assessment", "winner", "synthesized_best_answer"],
    "additionalProperties": False
}

# =============================================================================
# QUALITY CONTROL SCHEMAS
# =============================================================================

QUALITY_EVALUATION_SCHEMA = {
    "type": "object",
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "severity": {"type": "string", "enum": ["CRITICAL", "MAJOR", "MINOR"]},
                    "location": {"type": "string"},
                    "problem": {"type": "string"},
                    "fix": {"type": "string"},
                    "fix_priority": {"type": "integer", "minimum": 1, "maximum": 10}
                },
                "required": ["type", "severity", "location", "problem", "fix", "fix_priority"]
            }
        },
        "issue_counts": {
            "type": "object",
            "properties": {
                "critical": {"type": "integer"},
                "major": {"type": "integer"},
                "minor": {"type": "integer"}
            },
            "required": ["critical", "major", "minor"]
        },
        "rework_decision": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["ACCEPT", "REWORK", "REJECT"]},
                "reasoning": {"type": "string"},
                "rework_focus": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["action", "reasoning", "rework_focus"]
        },
        "quality_score": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "required": ["issues", "issue_counts", "rework_decision", "quality_score"],
    "additionalProperties": False
}

SUPERVISOR_CRITIQUE_SCHEMA = {
    "type": "object",
    "properties": {
        "first_impression": {
            "type": "object",
            "properties": {
                "quality_signal": {"type": "string", "enum": ["EXPERT", "COMPETENT", "GENERIC", "POOR"]},
                "reasoning": {"type": "string"}
            },
            "required": ["quality_signal", "reasoning"]
        },
        "specificity_audit": {
            "type": "object",
            "properties": {
                "named_entities_count": {"type": "integer"},
                "specific_numbers_count": {"type": "integer"},
                "generic_phrases_found": {"type": "array", "items": {"type": "string"}},
                "specificity_score": {"type": "integer", "minimum": 1, "maximum": 5}
            },
            "required": ["named_entities_count", "specific_numbers_count", "generic_phrases_found", "specificity_score"]
        },
        "depth_assessment": {
            "type": "object",
            "properties": {
                "domain_expertise_demonstrated": {"type": "boolean"},
                "evidence": {"type": "string"},
                "depth_score": {"type": "integer", "minimum": 1, "maximum": 5}
            },
            "required": ["domain_expertise_demonstrated", "evidence", "depth_score"]
        },
        "timing_validation": {
            "type": "object",
            "properties": {
                "timelines_justified": {"type": "boolean"},
                "unjustified_timelines": {"type": "array", "items": {"type": "string"}},
                "timing_score": {"type": "integer", "minimum": 1, "maximum": 5}
            },
            "required": ["timelines_justified", "unjustified_timelines", "timing_score"]
        },
        "actionability": {
            "type": "object",
            "properties": {
                "immediately_actionable": {"type": "boolean"},
                "what_would_make_actionable": {"type": "string"},
                "actionability_score": {"type": "integer", "minimum": 1, "maximum": 5}
            },
            "required": ["immediately_actionable", "what_would_make_actionable", "actionability_score"]
        },
        "overall_score": {"type": "number", "minimum": 0, "maximum": 10},
        "verdict": {"type": "string", "enum": ["ACCEPT", "NEEDS_MINOR_IMPROVEMENT", "NEEDS_REWORK", "REJECT"]},
        "rework_required": {"type": "boolean"},
        "rework_instructions": {
            "type": "object",
            "properties": {
                "priority_fixes": {"type": "array", "items": {"type": "string"}},
                "specific_guidance": {"type": "string"}
            },
            "required": ["priority_fixes", "specific_guidance"]
        }
    },
    "required": ["first_impression", "specificity_audit", "depth_assessment",
                "timing_validation", "actionability", "overall_score",
                "verdict", "rework_required", "rework_instructions"],
    "additionalProperties": False
}

# =============================================================================
# SCHEMA REGISTRY
# =============================================================================

SCHEMAS: Dict[str, dict] = {
    # Orchestration
    "task_analysis": TASK_ANALYSIS_SCHEMA,
    "task_decomposition": TASK_DECOMPOSITION_SCHEMA,
    "query_expansion": QUERY_EXPANSION_SCHEMA,
    
    # Agent outputs
    "researcher": RESEARCHER_OUTPUT_SCHEMA,
    "analyst": ANALYST_OUTPUT_SCHEMA,
    "reviewer": REVIEWER_OUTPUT_SCHEMA,
    "synthesizer": SYNTHESIZER_OUTPUT_SCHEMA,
    
    # Debate
    "debate_proposal": DEBATE_PROPOSAL_SCHEMA,
    "debate_critique": DEBATE_CRITIQUE_SCHEMA,
    "debate_voting": DEBATE_VOTING_SCHEMA,
    "debate_judge": DEBATE_JUDGE_SCHEMA,
    
    # Quality control
    "quality_evaluation": QUALITY_EVALUATION_SCHEMA,
    "supervisor_critique": SUPERVISOR_CRITIQUE_SCHEMA,
}


def get_schema(schema_name: str) -> dict:
    """Get a schema by name."""
    if schema_name not in SCHEMAS:
        raise ValueError(f"Unknown schema: {schema_name}. Available: {list(SCHEMAS.keys())}")
    return SCHEMAS[schema_name]


def get_openai_response_format(schema_name: str) -> dict:
    """Get schema formatted for OpenAI Structured Outputs."""
    schema = get_schema(schema_name)
    return {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "strict": True,
            "schema": schema
        }
    }


def get_gemini_response_schema(schema_name: str) -> dict:
    """Get schema formatted for Gemini responseSchema."""
    return get_schema(schema_name)


def validate_output(output: dict, schema_name: str) -> Tuple[bool, List[str]]:
    """Validate output against schema. Returns (is_valid, errors)."""
    try:
        import jsonschema
        
        schema = get_schema(schema_name)
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(output))
        
        if errors:
            error_messages = [f"{list(e.path)}: {e.message}" for e in errors]
            return False, error_messages
        
        return True, []
    except ImportError:
        # If jsonschema not installed, skip validation
        return True, []
