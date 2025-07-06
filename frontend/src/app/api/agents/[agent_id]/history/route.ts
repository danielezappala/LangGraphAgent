import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import { promises as fs } from 'fs';

// Mappa agent_id -> agent_name (hardcoded per ora, in sync con AGENT_CONFIGS)
const AGENT_ID_TO_NAME: Record<string, string> = {
  basic1: "Basic1",
  // aggiungi qui altri agent_id/nome se ne aggiungi altri
};

export async function GET(req: NextRequest, context: any) {
  const params = await context.params;
  const agent_id = params.agent_id;
  const agentName = AGENT_ID_TO_NAME[agent_id] || agent_id; // fallback su id se non trovato
  const historyPath = path.resolve(process.cwd(), '../backend', `history_${agentName}.json`);
  let data;
  try {
    data = await fs.readFile(historyPath, 'utf8');
  } catch (e) {
    // Fallback: se non esiste un file specifico, prova quello di default
    try {
      data = await fs.readFile(path.join(process.cwd(), 'backend', 'history.json'), 'utf8');
    } catch {
      return NextResponse.json([], { status: 200 });
    }
  }
  try {
    const history = JSON.parse(data);
    return NextResponse.json(history, { status: 200 });
  } catch (e) {
    return NextResponse.json([], { status: 200 });
  }
}
