import { cn } from '@/utils/cn'

interface NarrativePanelProps {
  sentences: string[]
  selectedSentence: number | null
  onSentenceClick: (index: number) => void
}

export default function NarrativePanel({
  sentences,
  selectedSentence,
  onSentenceClick,
}: NarrativePanelProps) {
  return (
    <div className="prose max-w-none">
      <div className="space-y-1 leading-relaxed">
        {sentences.map((sentence, index) => (
          <span
            key={index}
            onClick={() => onSentenceClick(index)}
            className={cn(
              'cursor-pointer px-1 py-0.5 rounded transition-all duration-200 inline sentence-highlight',
              selectedSentence === index
                ? 'selected bg-blue-100 ring-2 ring-blue-300'
                : 'hover:bg-amber-50'
            )}
          >
            <span className="text-blue-500 mr-1 text-sm">
              [{index + 1}]
            </span>
            {sentence}{' '}
          </span>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Click on any sentence to view its supporting evidence in the audit trail panel.
        </p>
      </div>
    </div>
  )
}
