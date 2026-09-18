/** @typedef {'LIVE'|'SIMULATED'|'SYNTHETIC'|'STATIC DEMO'|'UNKNOWN'} SourceType */
/** @typedef {'VERIFIED'|'PARTIAL'|'UNCALIBRATED'|'UNKNOWN'} EvidenceState */

/**
 * @typedef {Object} Provenance
 * @property {SourceType} sourceType
 * @property {string} generatedAt
 * @property {EvidenceState} evidenceState
 * @property {string} calibrationState
 * @property {string[]} sourceIds
 */

/**
 * @typedef {Object} Workload
 * @property {string} id
 * @property {string} name
 * @property {string} modality
 * @property {string} state
 * @property {string} qualityFloor
 * @property {string} placement
 * @property {string} slo
 * @property {Provenance} provenance
 */

export const SOURCE_TYPES = Object.freeze([
  'LIVE', 'SIMULATED', 'SYNTHETIC', 'STATIC DEMO', 'UNKNOWN',
]);

export const CONTROL_CENTER_SCHEMA = 'mercury.control-center/v1';
