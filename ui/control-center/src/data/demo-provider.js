import { ControlCenterProvider } from './provider.js';
import { DEMO_DATA } from './demo-data.js';

export class DemoControlCenterProvider extends ControlCenterProvider {
  async getSnapshot() {
    return structuredClone(DEMO_DATA);
  }
}
