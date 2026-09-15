from __future__ import annotations

import re

from mercury.context.models import (
    ContextArtifact,
    ContextPortability,
    ContextReuseDecision,
    ContextReuseRequest,
)


_SHA256_EVIDENCE = re.compile(r"sha256:[0-9a-f]{64}")


class ContextReuseGate:
    def evaluate(
        self,
        artifact: ContextArtifact,
        request: ContextReuseRequest,
    ) -> ContextReuseDecision:
        reasons: list[str] = []
        if request.artifact_id != artifact.artifact_id:
            reasons.append("artifact reference does not match")
        if request.requester_owner_id not in artifact.authorized_owner_ids:
            reasons.append("owner is not authorized")
        if request.requester_tenant_id not in artifact.authorized_tenant_ids:
            reasons.append("tenant is not authorized")
        if request.privacy_level != artifact.privacy_level:
            reasons.append("privacy level is incompatible")
        if not _SHA256_EVIDENCE.fullmatch(artifact.integrity_evidence or ""):
            reasons.append("integrity evidence is missing or invalid")
        if (
            artifact.portability is ContextPortability.MODEL_SPECIFIC
            and request.model_id != artifact.model_id
        ):
            reasons.append("model compatibility mismatch")
        if (
            artifact.portability is ContextPortability.RUNTIME_SPECIFIC
            and request.runtime_id != artifact.runtime_id
        ):
            reasons.append("runtime compatibility mismatch")
        return ContextReuseDecision(
            artifact_id=artifact.artifact_id,
            allowed=not reasons,
            reasons=tuple(reasons) or ("reuse requirements satisfied",),
        )
