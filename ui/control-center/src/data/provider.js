/**
 * Replaceable UI data boundary. A future provider may call a dedicated API,
 * but browser code must never import MERCURY Python internals directly.
 */
export class ControlCenterProvider {
  async getSnapshot() {
    throw new Error('ControlCenterProvider.getSnapshot must be implemented');
  }
}
