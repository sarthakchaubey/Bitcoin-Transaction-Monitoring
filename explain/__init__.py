"""Phase 7 SHAP explanations and investigation evidence packaging."""

from .evidence_package import build_all_evidence_packages, build_evidence_package
from .reason_builder import build_reason_sentence, confidence_label
from .shap_explainer import ShapExplainer

__all__ = [
    "ShapExplainer", "build_reason_sentence", "confidence_label",
    "build_evidence_package", "build_all_evidence_packages",
]
