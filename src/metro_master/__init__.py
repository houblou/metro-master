"""MetrologyLab AI: métrologie multi-agents et calculs vérifiables.

Le nom de paquet ``metro_master`` reste stable pour la compatibilité.
"""

from .comparison import (
    IdentifiabilityError,
    compare_results,
    normalized_error,
    paired_statistics,
    separate_bench_uncertainty,
    zeta_score,
)
from .conclusion import CompletionReport, ConclusionClaim, ConclusionVerificationReport
from .execution import (
    CalculationRequest,
    DeterministicEngine,
    InputEvidence,
    ProvenanceValidationError,
)
from .knowledge import KnowledgeStore
from .models import UncertaintyComponent
from .module_registry import ModuleRegistry, ModuleStore
from .pdf_library import GovernedPdfLibrary, PdfPageChunk
from .research import (
    CallableResearchProvider,
    ResearchRequest,
    ResearchSource,
)
from .quantities import (
    DependencyUnavailable,
    PintQuantityAdapter,
    compatible_units,
    convert_standard_uncertainty,
    convert_value,
)
from .rag import (
    CallableEmbeddingProvider,
    HashingEmbeddingProvider,
    HybridRagRetriever,
    VectorKnowledgeIndex,
)
from .study_history import StudyStore
from .token_budget import TokenBudgetExceeded, TokenBudgetPolicy, estimate_tokens
from .trace import CalculationTrace
from .uncertainty import propagate_linear
from .uncertainty_oracles import OracleResult, verify_with_external_oracles
from .uncertainty_study import (
    UncertaintyStudyResult,
    build_uncertainty_study,
    evaluate_type_a,
    evaluate_type_b,
)
from .version import __version__

__all__ = [
    "CalculationRequest",
    "CalculationTrace",
    "CompletionReport",
    "ConclusionClaim",
    "ConclusionVerificationReport",
    "DeterministicEngine",
    "DependencyUnavailable",
    "IdentifiabilityError",
    "GovernedPdfLibrary",
    "KnowledgeStore",
    "InputEvidence",
    "ModuleRegistry",
    "ModuleStore",
    "OracleResult",
    "PdfPageChunk",
    "PintQuantityAdapter",
    "CallableResearchProvider",
    "ResearchRequest",
    "ResearchSource",
    "CallableEmbeddingProvider",
    "HashingEmbeddingProvider",
    "HybridRagRetriever",
    "VectorKnowledgeIndex",
    "ProvenanceValidationError",
    "StudyStore",
    "TokenBudgetExceeded",
    "TokenBudgetPolicy",
    "UncertaintyComponent",
    "UncertaintyStudyResult",
    "build_uncertainty_study",
    "compare_results",
    "compatible_units",
    "convert_standard_uncertainty",
    "convert_value",
    "normalized_error",
    "paired_statistics",
    "propagate_linear",
    "separate_bench_uncertainty",
    "zeta_score",
    "estimate_tokens",
    "evaluate_type_a",
    "evaluate_type_b",
    "verify_with_external_oracles",
]

