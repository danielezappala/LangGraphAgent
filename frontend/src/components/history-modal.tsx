"use client";
import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogClose } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";

interface HistoryModalProps {
  agentId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface HistoryMessage {
  role: string;
  content: string;
  date?: string;
}

export function HistoryModal({ agentId, open, onOpenChange }: HistoryModalProps) {
  const [history, setHistory] = useState<HistoryMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError(null);
    fetch(`/api/agents/${agentId}/history`)
      .then(async (res) => {
        if (!res.ok) throw new Error("Errore nel caricamento della cronologia");
        return res.json();
      })
      .then(setHistory)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [agentId, open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg w-full">
        <DialogHeader>
          <DialogTitle>Cronologia agente</DialogTitle>
          <DialogClose />
        </DialogHeader>
        <ScrollArea className="h-96">
          {loading && <div className="text-center text-muted-foreground">Caricamento...</div>}
          {error && <div className="text-red-500 text-center">{error}</div>}
          {!loading && !error && history.length === 0 && (
            <div className="text-center text-muted-foreground">Nessuna cronologia trovata.</div>
          )}
          {!loading && !error && history.length > 0 && (
            <ul className="space-y-3">
              {history.map((msg, i) => (
                <li key={i} className="border rounded p-2 bg-muted">
                  <div className="text-xs text-gray-500 mb-1">{msg.role} {msg.date && <span>({msg.date})</span>}</div>
                  <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                </li>
              ))}
            </ul>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
