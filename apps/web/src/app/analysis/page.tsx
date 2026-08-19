"use client";

import { useState } from "react";
import { Button } from "~/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Input } from "~/components/ui/input";
import { Label } from "~/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs";
import { AlertCircle, Shield } from "lucide-react";
import { Alert, AlertDescription } from "~/components/ui/alert";

type ScoreResponse = {
  variant: string;
  reference_score: number;
  alternate_score: number;
  score_delta: number;
  status: string;
  provenance: {
    scorer: string;
    scorer_version: string;
    strand: string;
    context_length: number;
  };
};

type ProtocolInfo = {
  protocol_version: string;
  context_length_bp: number;
  scorer: string;
  scorer_version: string;
};

const CHROMOSOMES = [
  "chr1", "chr2", "chr3", "chr4", "chr5", "chr6", "chr7", "chr8",
  "chr9", "chr10", "chr11", "chr12", "chr13", "chr14", "chr15",
  "chr16", "chr17", "chr18", "chr19", "chr20", "chr21", "chr22",
  "chrX", "chrY", "chrM",
];

export default function VariantAnalysisPage() {
  const [chrom, setChrom] = useState("chr17");
  const [position, setPosition] = useState("43044295");
  const [ref, setRef] = useState("C");
  const [alt, setAlt] = useState("T");
  const [strand, setStrand] = useState("forward");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScoreResponse | null>(null);
  const [protocol, setProtocol] = useState<ProtocolInfo | null>(null);

  const handleSubmit = async () => {
    if (!position || !ref || !alt) {
      setError("Position, ref, and alt are required.");
      return;
    }
    if (ref.toUpperCase() === alt.toUpperCase()) {
      setError("Reference and alternate alleles must differ.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/score/variant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chrom,
          start: parseInt(position),
          ref,
          alt,
          strand,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Scoring failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadProtocol = async () => {
    try {
      const response = await fetch("/api/protocol");
      if (response.ok) {
        const data = await response.json();
        setProtocol(data);
      }
    } catch {
      // ignore
    }
  };

  const loadExample = () => {
    setChrom("chr17");
    setPosition("43044295");
    setRef("C");
    setAlt("T");
  };

  return (
    <div className="min-h-screen bg-[#e9eeea]">
      <header className="border-b border-[#3c4f3d]/10 bg-white">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <Shield className="h-6 w-6 text-[#de8246]" />
            <h1 className="text-xl font-light tracking-wide text-[#3c4f3d]">
              EvoVariant-TR Research Workbench
            </h1>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        <Tabs defaultValue="analyze" className="space-y-6">
          <TabsList className="bg-[#e9eeea]">
            <TabsTrigger
              value="analyze"
              className="data-[state=active]:bg-white data-[state=active]:text-[#3c4f3d]"
            >
              Variant Analysis
            </TabsTrigger>
            <TabsTrigger
              value="methods"
              className="data-[state=active]:bg-white data-[state=active]:text-[#3c4f3d]"
            >
              Methods & Provenance
            </TabsTrigger>
          </TabsList>

          <TabsContent value="analyze" className="space-y-6">
            <Card className="gap-0 border-none bg-white py-0 shadow-sm">
              <CardHeader className="pt-4 pb-2">
                <CardTitle className="text-sm font-normal text-[#3c4f3d]/70">
                  Single Variant Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="pb-6">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
                  <div className="md:col-span-1">
                    <Label className="text-xs font-normal text-[#3c4f3d]/70">
                      Chromosome
                    </Label>
                    <Select value={chrom} onValueChange={setChrom}>
                      <SelectTrigger className="h-9 border-[#3c4f3d]/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CHROMOSOMES.map((c) => (
                          <SelectItem key={c} value={c}>
                            {c}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="md:col-span-1">
                    <Label className="text-xs font-normal text-[#3c4f3d]/70">
                      Position (1-based)
                    </Label>
                    <Input
                      type="number"
                      min="1"
                      value={position}
                      onChange={(e) => setPosition(e.target.value)}
                      className="h-9 border-[#3c4f3d]/10"
                    />
                  </div>

                  <div className="md:col-span-1">
                    <Label className="text-xs font-normal text-[#3c4f3d]/70">
                      Reference Allele
                    </Label>
                    <Input
                      type="text"
                      maxLength={4}
                      value={ref}
                      onChange={(e) => setRef(e.target.value.toUpperCase())}
                      className="h-9 border-[#3c4f3d]/10"
                    />
                  </div>

                  <div className="md:col-span-1">
                    <Label className="text-xs font-normal text-[#3c4f3d]/70">
                      Alternate Allele
                    </Label>
                    <Input
                      type="text"
                      maxLength={4}
                      value={alt}
                      onChange={(e) => setAlt(e.target.value.toUpperCase())}
                      className="h-9 border-[#3c4f3d]/10"
                    />
                  </div>

                  <div className="md:col-span-1">
                    <Label className="text-xs font-normal text-[#3c4f3d]/70">
                      Strand
                    </Label>
                    <Select value={strand} onValueChange={setStrand}>
                      <SelectTrigger className="h-9 border-[#3c4f3d]/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="forward">Forward</SelectItem>
                        <SelectItem value="reverse">Reverse</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="mt-6 flex gap-3">
                  <Button
                    onClick={handleSubmit}
                    disabled={isLoading}
                    className="bg-[#3c4f3d] text-white hover:bg-[#3c4f3d]/90"
                  >
                    {isLoading ? "Scoring..." : "Score Variant"}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={loadExample}
                    className="border-[#3c4f3d]/10"
                  >
                    BRCA1 Example
                  </Button>
                </div>

                {error && (
                  <Alert variant="destructive" className="mt-4">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>

            {result && (
              <Card className="gap-0 border-none bg-white py-0 shadow-sm">
                <CardHeader className="pt-4 pb-2">
                  <CardTitle className="text-sm font-normal text-[#3c4f3d]/70">
                    Scoring Results
                  </CardTitle>
                </CardHeader>
                <CardContent className="pb-4">
                  <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                    <div>
                      <p className="text-xs text-[#3c4f3d]/60">Variant</p>
                      <p className="font-medium text-[#3c4f3d]">
                        {result.variant}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[#3c4f3d]/60">
                        Score Delta
                      </p>
                      <p className="font-medium text-[#de8246]">
                        {result.score_delta.toFixed(4)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[#3c4f3d]/60">
                        Reference Score
                      </p>
                      <p className="font-medium text-[#3c4f3d]">
                        {result.reference_score.toFixed(4)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[#3c4f3d]/60">
                        Alternate Score
                      </p>
                      <p className="font-medium text-[#3c4f3d]">
                        {result.alternate_score.toFixed(4)}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 rounded-md bg-[#e9eeea]/50 p-3">
                    <p className="text-xs text-[#3c4f3d]/60">
                      Scorer: {result.provenance.scorer}{" "}
                      v{result.provenance.scorer_version}
                      {" · "}Strand: {result.provenance.strand}
                      {" · "}Context: {result.provenance.context_length}bp
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="methods">
            <Card className="gap-0 border-none bg-white py-0 shadow-sm">
              <CardHeader className="pt-4 pb-2">
                <CardTitle className="text-sm font-normal text-[#3c4f3d]/70">
                  Methods & Provenance
                </CardTitle>
              </CardHeader>
              <CardContent className="pb-6 space-y-6">
                {protocol ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <span className="text-xs text-[#3c4f3d]/60">Protocol Version</span>
                        <span className="ml-2 font-medium text-[#3c4f3d]">
                          {protocol.protocol_version}
                        </span>
                      </div>
                      <div>
                        <span className="text-xs text-[#3c4f3d]/60">Context Length</span>
                        <span className="ml-2 font-medium text-[#3c4f3d]">
                          {protocol.context_length_bp} bp
                        </span>
                      </div>
                      <div>
                        <span className="text-xs text-[#3c4f3d]/60">Scorer</span>
                        <span className="ml-2 font-medium text-[#3c4f3d]">
                          {protocol.scorer} v{protocol.scorer_version}
                        </span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <Button
                    variant="outline"
                    onClick={handleLoadProtocol}
                    className="border-[#3c4f3d]/10"
                  >
                    Load Protocol Info
                  </Button>
                )}

                <div className="border-t border-[#3c4f3d]/5 pt-4">
                  <h3 className="mb-2 text-xs font-medium text-[#3c4f3d]/60">
                    FROZEN PROTOCOL SPECIFICATION
                  </h3>
                  <ul className="space-y-1 text-xs text-[#3c4f3d]/70">
                    <li>• Estimand: Distinguish pathogenic vs benign resolution of VUS</li>
                    <li>• Design: Temporal generalization benchmark</li>
                    <li>• Context window: 8192 bp (frozen Milestone 41)</li>
                    <li>• Reference assembly: GRCh38</li>
                    <li>• Strands scored: Forward + Reverse-complement</li>
                    <li>• Scoring semantics: Log-likelihood ratio</li>
                    <li>• Calibration cohort: 571,740 definitive variants at t0</li>
                    <li>• Primary cohort: 380,776 VUS variants at t0</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}