"use client"

import { useState } from "react"
import { Sparkles, Lightbulb, Check } from "lucide-react"
import { optimizePrompt } from "@/actions/optimize"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "sonner"

interface PromptAssistantDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  originalBrief: string
  contentType: string
  tone: string
  structure: Array<{ component: string; count: number }>
  onApply: (optimizedPrompt: string) => void
}

interface OptimizationResult {
  optimized_prompt: string
  improvements: string[]
}

export function PromptAssistantDialog({
  open,
  onOpenChange,
  originalBrief,
  contentType,
  tone,
  structure,
  onApply
}: PromptAssistantDialogProps) {
  const [isOptimizing, setIsOptimizing] = useState(false)
  const [result, setResult] = useState<OptimizationResult | null>(null)

  const handleOptimize = async () => {
    if (!originalBrief.trim()) {
      toast.error("Please enter a brief first")
      return
    }

    setIsOptimizing(true)
    try {
      const result = await optimizePrompt({
        text: originalBrief,
        content_type: contentType,
        tone: tone,
        structure: structure
      })

      if (result.success && result.data) {
        setResult(result.data)
        toast.success("Prompt ottimizzato con successo!")
      } else {
        throw new Error(result.error || "Failed to optimize prompt")
      }
    } catch (error) {
      console.error("Error optimizing prompt:", error)
      toast.error("Errore durante l'ottimizzazione del prompt")
    } finally {
      setIsOptimizing(false)
    }
  }

  const handleApply = () => {
    if (result) {
      onApply(result.optimized_prompt)
      toast.success("Prompt applicato al brief!")
      onOpenChange(false)
      setResult(null)
    }
  }

  const handleClose = () => {
    onOpenChange(false)
    setResult(null)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Prompt Assistant
          </DialogTitle>
          <DialogDescription>
            Trasforma la tua descrizione in un prompt ottimizzato per generare contenuti migliori.
            Perfetto per chi non conosce il prompt engineering!
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Original Brief */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium">📝 Brief Originale</h3>
              <Badge variant="secondary">{originalBrief.length} caratteri</Badge>
            </div>
            <div className="rounded-lg border bg-muted p-4">
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                {originalBrief || "Nessun brief inserito"}
              </p>
            </div>
          </div>

          {/* Context Info */}
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground mb-1">Tone</p>
              <Badge variant="outline" className="capitalize">{tone}</Badge>
            </div>
            <div>
              <p className="text-muted-foreground mb-1">Struttura</p>
              <Badge variant="outline">{structure.length} componenti</Badge>
            </div>
            <div>
              <p className="text-muted-foreground mb-1">Tipo</p>
              <Badge variant="outline" className="capitalize">{contentType}</Badge>
            </div>
          </div>

          {/* Optimize Button */}
          {!result && (
            <Button
              onClick={handleOptimize}
              disabled={isOptimizing || !originalBrief.trim()}
              className="w-full"
              size="lg"
            >
              {isOptimizing ? (
                <>
                  <Sparkles className="mr-2 h-4 w-4 animate-pulse" />
                  Ottimizzazione in corso...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  ✨ Ottimizza il mio prompt
                </>
              )}
            </Button>
          )}

          {/* Results */}
          {result && (
            <>
              {/* Improvements */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-yellow-500" />
                  <h3 className="text-sm font-medium">Miglioramenti Applicati</h3>
                </div>
                <ul className="space-y-2">
                  {result.improvements.map((improvement, index) => (
                    <li
                      key={index}
                      className="flex items-start gap-2 text-sm"
                    >
                      <Check className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-muted-foreground">{improvement}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Optimized Prompt */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium">✨ Prompt Ottimizzato</h3>
                  <Badge className="bg-green-500">{result.optimized_prompt.length} caratteri</Badge>
                </div>
                <Textarea
                  value={result.optimized_prompt}
                  onChange={(e) =>
                    setResult({ ...result, optimized_prompt: e.target.value })
                  }
                  rows={12}
                  className="font-mono text-sm"
                />
                <p className="text-xs text-muted-foreground">
                  💡 Puoi modificare il prompt ottimizzato prima di applicarlo
                </p>
              </div>
            </>
          )}
        </div>

        <DialogFooter>
          {result ? (
            <>
              <Button variant="outline" onClick={handleClose}>
                Annulla
              </Button>
              <Button
                variant="outline"
                onClick={handleOptimize}
                disabled={isOptimizing}
              >
                <Sparkles className="mr-2 h-4 w-4" />
                Ri-ottimizza
              </Button>
              <Button onClick={handleApply}>
                <Check className="mr-2 h-4 w-4" />
                Applica al Brief
              </Button>
            </>
          ) : (
            <Button variant="outline" onClick={handleClose}>
              Chiudi
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

