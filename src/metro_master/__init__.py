"""METRO-MASTER: métrologie multi-agents et calculs vérifiables."""

from .comparison import (
    IdentifiabilityError,
    compare_results,
    normalized_error,
    paired_statistics,
    separate_bench_uncertainty,
    zeta_score,
)
from .conclusion import ConclusionClaim, ConclusionVerificationReport
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
from .rag import (
    CallableEmbeddingProvider,
    HashingEmbeddingProvider,
    HybridRagRetriever,
    VectorKnowledgeIndex,
)
from .study_history import StudyStore
from .token_budget import TokenBudgetExceeded, TokenBudgetPolicy, estimate_tokens
from .uncertainty import propagate_linear

__all__ = [
    "CalculationRequest",
    "ConclusionClaim",
    "ConclusionVerificationReport",
    "DeterministicEngine",
    "IdentifiabilityError",
    "GovernedPdfLibrary",
    "KnowledgeStore",
    "InputEvidence",
    "ModuleRegistry",
    "ModuleStore",
    "PdfPageChunk",
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
    "compare_results",
    "normalized_error",
    "paired_statistics",
    "propagate_linear",
    "separate_bench_uncertainty",
    "zeta_score",
    "estimate_tokens",
]

__version__ = "0.7.1"

