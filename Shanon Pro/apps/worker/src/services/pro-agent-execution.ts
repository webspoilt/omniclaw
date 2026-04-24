import { EngineClient } from '@shannon/engine-client';
import { AgentExecutionService, AgentExecutionInput } from './agent-execution.js';
import { AuditSession } from '../audit/index.js';
import { ActivityLogger } from '../types/activity-logger.js';
import { AgentName } from '../types/agents.js';
import { AgentEndResult } from '../types/audit.js';
import { Result, ok, err } from '../types/result.js';
import { PentestError } from './error-handling.js';
import { ConfigLoaderService } from './config-loader.js';
import { ErrorCode } from '../types/errors.js';

export class ProAgentExecutionService extends AgentExecutionService {
  private engineClient: EngineClient;

  constructor(configLoader: ConfigLoaderService, pythonPath?: string, enginesDir?: string) {
    super(configLoader);
    this.engineClient = new EngineClient(pythonPath, enginesDir);
  }

  async execute(
    agentName: AgentName,
    input: AgentExecutionInput,
    auditSession: AuditSession,
    logger: ActivityLogger,
  ): Promise<Result<AgentEndResult, PentestError>> {
    // Check if this agent should be handled by the Pro Engine (Stage 2)
    // For now, let's say all exploit agents in Pro mode use the engine
    if (agentName.endsWith('-exploit')) {
      logger.info(`[ProAgentExecutionService] Executing ${agentName} via Pro Engine`);
      
      const startTime = Date.now();
      
      // Prepare task data for Stage 2
      const taskData = {
        agent_name: agentName,
        target_url: input.webUrl,
        repo_path: input.repoPath,
        deliverables_path: input.deliverablesPath,
        // Add more context as needed by agent_controller.py
      };

      const result = await this.engineClient.runDynamicAgent(taskData);

      if (!result.success) {
        return err(
          new PentestError(
            `Pro Engine failed to execute ${agentName}: ${result.error}`,
            'validation',
            true,
            { agentName, error: result.error },
            ErrorCode.AGENT_EXECUTION_FAILED,
          )
        );
      }

      const endResult: AgentEndResult = {
        attemptNumber: input.attemptNumber,
        duration_ms: Date.now() - startTime,
        cost_usd: 0, // Local execution cost
        success: true,
        model: 'pro-engine-v1',
      };

      return ok(endResult);
    }

    // Fallback to base implementation (Claude SDK)
    return super.execute(agentName, input, auditSession, logger);
  }
}
