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
from .quantities import compatible_units, convert_standard_uncertainty, convert_value
from .rag import (
    CallableEmbeddingProvider,
    HashingEmbeddingProvider,
    HybridRagRetriever,
    VectorKnowledgeIndex,
)
from .study_history import StudyStore
from .source_registry import SourceRegistry
from .token_budget import TokenBudgetExceeded, TokenBudgetPolicy, estimate_tokens
from .trace import CalculationTrace
from .uncertainty import propagate_linear
from .version import __version__

__all__ = [
    "CalculationRequest",
    "CalculationTrace",
    "CompletionReport",
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
    "SourceRegistry",
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
    "compatible_units",
    "convert_standard_uncertainty",
    "convert_value",
    "normalized_error",
    "paired_statistics",
    "propagate_linear",
    "separate_bench_uncertainty",
    "zeta_score",
    "estimate_tokens",
]

