import { execFile } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execFileAsync = promisify(execFile);

export async function runDbQuery<T = any>(action: string, params: Record<string, any> = {}): Promise<T> {
  const backendDir = path.resolve(process.cwd(), '../backend');
  const pythonPath = path.join(backendDir, '.venv', 'Scripts', 'python.exe');
  const backendSrc = path.join(backendDir, 'src').replace(/\\/g, '\\\\');

  // Small, safe python script that imports backend/src/db.py and calls the requested function
  const pyCode = `
import sys, json
sys.path.insert(0, r'${backendSrc}')
import db

action = sys.argv[1]
params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

if action == 'summary':
    res = db.get_analytics_summary(**params)
elif action == 'charts':
    res = db.get_analytics_charts(**params)
elif action == 'list':
    res = db.get_call_analytics(**params)
elif action == 'escalations':
    res = db.get_open_escalations()
else:
    res = {}

print(json.dumps(res, ensure_ascii=False))
`;

  try {
    const { stdout } = await execFileAsync(
      pythonPath,
      ['-c', pyCode, action, JSON.stringify(params)],
      { cwd: backendDir, maxBuffer: 10 * 1024 * 1024 }
    );
    return JSON.parse(stdout) as T;
  } catch (err) {
    console.error(`DB Bridge Error [${action}]:`, err);
    // Return empty fallback on error without leaking internal tracebacks to client
    return (action === 'list' || action === 'escalations' ? [] : {}) as T;
  }
}
