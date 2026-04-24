import { EngineClient } from '@shannon/engine-client';
import { FindingsProvider } from '../interfaces/findings-provider.js';
import { ActivityInput } from '../temporal/activities.js';
import { VulnType } from '../types/agents.js';

export class ProFindingsProvider implements FindingsProvider {
  private engineClient: EngineClient;

  constructor(pythonPath?: string, enginesDir?: string) {
    this.engineClient = new EngineClient(pythonPath, enginesDir);
  }

  async mergeFindingsIntoQueue(
    repoPath: string,
    vulnType: VulnType,
    input: ActivityInput
  ): Promise<{ mergedCount: number }> {
    console.log(`[ProFindingsProvider] Running Pro Engine for ${vulnType} on ${input.webUrl}`);

    // 1. Run Stage 1: Static Analysis
    // Note: Stage 1 currently analyzes everything, we might want to filter by vulnType later
    const staticResult = await this.engineClient.runStaticAnalysis(repoPath, input.webUrl);
    
    if (!staticResult.success) {
      console.error(`[ProFindingsProvider] Static analysis failed: ${staticResult.error}`);
      return { mergedCount: 0 };
    }

    const scanId = staticResult.data?.scan_id;
    if (!scanId) {
      console.error('[ProFindingsProvider] No scan_id returned from static analysis');
      return { mergedCount: 0 };
    }

    // 2. Run Stage 3: Correlation & Reachability
    // This will populate the Redis queue used by Stage 2
    const correlationResult = await this.engineClient.runCorrelation(scanId);
    
    if (!correlationResult.success) {
      console.error(`[ProFindingsProvider] Correlation failed: ${correlationResult.error}`);
      return { mergedCount: 0 };
    }

    const queuedCount = correlationResult.data?.queue?.queued || 0;
    console.log(`[ProFindingsProvider] Successfully queued ${queuedCount} findings into Redis`);

    return { mergedCount: queuedCount };
  }
}
