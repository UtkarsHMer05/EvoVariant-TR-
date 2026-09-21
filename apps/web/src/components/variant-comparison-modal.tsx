import type { ClinvarVariant } from "~/utils/genome-api";
import { Button } from "./ui/button";
import { ExternalLink, X } from "lucide-react";
import {
  getClassificationColorClasses,
  getNucleotideColorClass,
} from "~/utils/coloring-utils";

export function VariantComparisonModal({
  comparisonVariant,
  onClose,
}: {
  comparisonVariant: ClinvarVariant | null;
  onClose: () => void;
}) {
  if (!comparisonVariant?.evo2Result) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-lg bg-white">
        {/* Modal header */}
        <div className="border-b border-[#3c4f3d]/10 p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-[#3c4f3d]">
              Variant Analysis Comparison
            </h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-7 w-7 cursor-pointer p-0 text-[#3c4f3d]/70 hover:bg-[#9eeea]/70 hover:text-[#3c4f3d]"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* Modal content */}
        <div className="p-5">
          {comparisonVariant?.evo2Result && (
            <div className="space-y-6">
              <div className="rounded-md border border-[#3c4f3d]/10 bg-[#e9eeea]/30 p-4">
                <h4 className="mb-3 text-sm font-medium text-[#3c4f3d]">
                  Variant Information
                </h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <div className="space-y-2">
                      <div className="flex">
                        <span className="w-28 text-xs text-[#3c4f3d]/70">
                          Position:
                        </span>
                        <span className="text-xs">
                          {comparisonVariant.location}
                        </span>
                      </div>
                      <div className="flex">
                        <span className="w-28 text-xs text-[#3c4f3d]/70">
                          Type:
                        </span>
                        <span className="text-xs">
                          {comparisonVariant.variation_type}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="space-y-2">
                      <div className="flex">
                        <span className="w-28 text-xs text-[#3c4f3d]/70">
                          Variant:
                        </span>
                        <span className="font-mono text-xs">
                          {(() => {
                            const match =
                              /(\w)>(\w)/.exec(comparisonVariant.title);
                            if (match?.length === 3) {
                              const [, ref, alt] = match;
                              return (
                                <>
                                  <span
                                    className={getNucleotideColorClass(ref!)}
                                  >
                                    {ref}
                                  </span>
                                  <span>{">"}</span>
                                  <span
                                    className={getNucleotideColorClass(alt!)}
                                  >
                                    {alt}
                                  </span>
                                </>
                              );
                            }
                            return comparisonVariant.title;
                          })()}
                        </span>
                      </div>
                      <div className="flex items-center">
                        <span className="w-28 text-xs text-[#3c4f3d]/70">
                          ClinVar ID:
                        </span>
                        <a
                          href={`https://www.ncbi.nlm.nih.gov/clinvar/variation/${comparisonVariant.clinvar_id}`}
                          className="text-xs text-[#de8246] hover:underline"
                          target="_blank"
                        >
                          {comparisonVariant.clinvar_id}
                        </a>
                        <ExternalLink className="ml-1 inline-block h-3 w-3 text-[#de8246]" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Variant results */}
              <div>
                <h4 className="mb-3 text-sm font-medium text-[#3c4f3d]">
                  Analysis Comparison
                </h4>
                <div className="rounded-md border border-[#3c4f3d]/10 bg-white p-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    {/* ClinVar Assesment */}
                    <div className="rounded-md bg-[#e9eeea]/50 p-4">
                      <h5 className="mb-2 flex items-center gap-2 text-xs font-medium text-[#3c4f3d]">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#3c4f3d]/10">
                          <span className="h-3 w-3 rounded-full bg-[#3c4f3d]"></span>
                        </span>
                        ClinVar Assessment
                      </h5>
                      <div className="mt-2">
                        <div
                          className={`w-fit rounded-md px-2 py-1 text-xs font-normal ${getClassificationColorClasses(comparisonVariant.classification)}`}
                        >
                          {comparisonVariant.classification ||
                            "Unknown significance"}
                        </div>
                      </div>
                    </div>

                    {/* Raw research signal */}
                    <div className="rounded-md bg-[#e9eeea]/50 p-4">
                      <h5 className="mb-2 flex items-center gap-2 text-xs font-medium text-[#3c4f3d]">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#3c4f3d]/10">
                          <span className="h-3 w-3 rounded-full bg-[#de8246]"></span>
                        </span>
                        Research model signal
                      </h5>
                      <div className="mt-3">
                        <div className="mb-1 text-xs text-[#3c4f3d]/70">
                          Primary delta signal:
                        </div>
                        <div className="text-sm font-medium">
                          {comparisonVariant.evo2Result.delta_primary.toFixed(6)}
                        </div>
                        <div className="text-xs text-[#3c4f3d]/60">
                          Raw alternate-minus-reference signal; no clinical label or confidence is derived here.
                        </div>
                      </div>
                      <div className="mt-3">
                        <div className="space-y-1 text-xs text-[#3c4f3d]/70">
                          <div>
                            Forward: {comparisonVariant.evo2Result.delta_forward?.toFixed(6) ?? "UNAVAILABLE"}
                          </div>
                          <div>
                            Reverse-complement: {comparisonVariant.evo2Result.delta_reverse?.toFixed(6) ?? "UNAVAILABLE"}
                          </div>
                          <div>
                            Disagreement: {comparisonVariant.evo2Result.orientation_disagreement?.toFixed(6) ?? "UNAVAILABLE"}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal footer */}
        <div className="flex justify-end border-t border-[#3c4f3d]/10 bg-[#e9eeea]/30 p-4">
          <Button
            variant="outline"
            onClick={onClose}
            className="cursor-pointer border-[#3c4f3d]/10 bg-white text-[#3c4f3d] hover:bg-[#e9eeea]/70"
          >
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
