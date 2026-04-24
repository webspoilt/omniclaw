import { spawn } from 'child_process';
import path from 'path';

export interface EngineResult {
  success: boolean;
  output: string;
  error?: string;
  data?: any;
}

export class EngineClient {
  private pythonPath: string;
  private enginesDir: string;

  constructor(pythonPath: string = 'python', enginesDir?: string) {
    this.pythonPath = pythonPath;
    this.enginesDir = enginesDir || path.resolve(process.cwd(), 'engines');
  }

  /**
   * Run Stage 1: Static Analysis
   */
  async runStaticAnalysis(repoPath: string, repoUrl: string): Promise<EngineResult> {
    const scriptPath = path.join(this.enginesDir, 'static-analysis', 'engine', 'pipeline.py');
    return this.runPythonScript(scriptPath, ['--repo-path', repoPath, '--repo-url', repoUrl]);
  }

  /**
   * Run Stage 2: Dynamic Agent (Single Task)
   */
  async runDynamicAgent(taskData: any): Promise<EngineResult> {
    const scriptPath = path.join(this.enginesDir, 'dynamic-agent', 'agent_controller.py');
    // For now, passing task as JSON string
    return this.runPythonScript(scriptPath, ['--task', JSON.stringify(taskData)]);
  }

  /**
   * Run Stage 3: Correlation Engine
   */
  async runCorrelation(scanId: string): Promise<EngineResult> {
    const scriptPath = path.join(this.enginesDir, 'correlation', 'correlation_engine.py');
    return this.runPythonScript(scriptPath, ['--scan-id', scanId]);
  }

  private async runPythonScript(scriptPath: string, args: string[]): Promise<EngineResult> {
    return new Promise((resolve) => {
      const pythonProcess = spawn(this.pythonPath, [scriptPath, ...args]);
      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          try {
            const data = JSON.parse(stdout);
            resolve({ success: true, output: stdout, data });
          } catch {
            resolve({ success: true, output: stdout });
          }
        } else {
          resolve({
            success: false,
            output: stdout,
            error: stderr || `Process exited with code ${code}`,
          });
        }
      });
    });
  }
}
