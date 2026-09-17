from mercury.morphing.compatibility import evaluate_morph_compatibility
from mercury.morphing.contracts import MorphProfile,MorphProfileDraft,MorphProfileStatus,MorphValidationIssue,morph_profile_id
def validate_morph_profile(draft,capabilities,requirements):
 if not isinstance(draft,MorphProfileDraft): raise ValueError("draft required")
 issues=[]
 if draft.profile_id!=morph_profile_id(draft): issues.append(MorphValidationIssue(issue_id="profile_id",violated_invariant="profile_id",reason="deterministic profile id mismatch"))
 return MorphProfile(**draft.model_dump(mode="python"),status=MorphProfileStatus.REJECTED if issues else MorphProfileStatus.VALID,issues=tuple(issues))
